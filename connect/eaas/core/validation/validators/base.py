import importlib
import inspect
import os
import re
import sys

import toml
import yaml

from connect.eaas.core.validation.helpers import get_code_context
from connect.eaas.core.validation.models import ValidationItem, ValidationResult


def _load_project_toml_file(path):
    descriptor_file = os.path.join(path, 'pyproject.toml')
    if not os.path.isfile(descriptor_file):
        return None, [
            ValidationItem(
                level='ERROR',
                message=(
                    'The mandatory *pyproject.toml* project '
                    f'descriptor file is not present in the folder {path}.'
                ),
                file=descriptor_file,
            ),
        ]
    try:
        return toml.load(descriptor_file), []
    except toml.TomlDecodeError:
        return None, [
            ValidationItem(
                level='ERROR',
                message=(
                    'The project descriptor file *pyproject.toml* is '
                    'not a valid toml file.'
                ),
                file=descriptor_file,
            ),
        ]


def validate_pyproject_toml(context):  # noqa: CCR001
    project_dir = context['project_dir']

    data, messages = _load_project_toml_file(project_dir)
    if not data:
        return ValidationResult(items=messages, must_exit=True)

    messages = []

    descriptor_file = os.path.join(project_dir, 'pyproject.toml')
    dependencies = data['tool']['poetry']['dependencies']

    if 'connect-extension-runner' in dependencies:
        messages.append(
            ValidationItem(
                message=(
                    'Extensions must depend on *connect-eaas-core* library not '
                    '*connect-extension-runner*.'
                ),
                file=descriptor_file,
            ),
        )
    elif 'connect-eaas-core' not in dependencies:
        messages.append(
            ValidationItem(
                level='ERROR',
                message='No dependency on *connect-eaas-core* has been found.',
                file=descriptor_file,
            ),
        )

    extension_dict = data['tool']['poetry'].get('plugins', {}).get('connect.eaas.ext')
    if not isinstance(extension_dict, dict):
        messages.append(
            ValidationItem(
                level='ERROR',
                message=(
                    'No extension declaration has been found. '
                    'The extension must be declared in the '
                    '*[tool.poetry.plugins."connect.eaas.ext"]* section.'
                ),
                file=descriptor_file,
            ),
        )
        return ValidationResult(items=messages, must_exit=True)

    sys.path.append(os.path.join(os.getcwd(), project_dir))
    possible_extensions = ['extension', 'webapp', 'anvilapp', 'eventsapp']
    extensions = {}
    for extension_type in possible_extensions:
        if extension_type in extension_dict.keys():
            package, class_name = extension_dict[extension_type].rsplit(':', 1)
            try:
                extension_module = importlib.import_module(package)
            except ImportError as err:
                messages.append(
                    ValidationItem(
                        level='ERROR',
                        message=(
                            f'The application class *{extension_dict[extension_type]}* '
                            f'cannot be loaded: {err}.'
                        ),
                        file=descriptor_file,
                    ),
                )
                return ValidationResult(items=messages, must_exit=True)

            extensions[extension_type] = getattr(extension_module, class_name)

    if 'extension' in extension_dict:
        messages.append(
            ValidationItem(
                level='WARNING',
                message=(
                    'Declaring an events application using the *extension* entrypoint name is '
                    'deprecated in favor of *eventsapp*.'
                ),
                file=descriptor_file,
            ),
        )

    if not extensions:
        messages.append(
            ValidationItem(
                level='ERROR',
                message=(
                    'Invalid application declaration in '
                    '*[tool.poetry.plugins."connect.eaas.ext"]*: '
                    'The application must be declared as: *"eventsapp" = '
                    '"your_package.extension:YourApplication"* '
                    'for Fulfillment automation or Hub integration. '
                    'For Multi account installation must be '
                    'declared at least one the following: *"eventsapp" = '
                    '"your_package.events:YourEventsApplication"*, '
                    '*"webapp" = "your_package.webapp:YourWebApplication"*, '
                    '*"anvilapp" = "your_package.anvil:YourAnvilApplication"*.'
                ),
                file=descriptor_file,
            ),
        )
        return ValidationResult(items=messages, must_exit=True)

    context['extension_classes'] = extensions
    return ValidationResult(items=messages, context=context)


def validate_docker_compose_yml(context):
    project_dir = context['project_dir']
    messages = []
    compose_file = os.path.join(project_dir, 'docker-compose.yml')
    if not os.path.isfile(compose_file):
        messages.append(
            ValidationItem(
                message=(
                    f'The directory *{project_dir}* does not look like an extension project '
                    'directory, the file *docker-compose.yml* is not present.'
                ),
                file=compose_file,
            ),
        )
        return ValidationResult(items=messages)
    try:
        data = yaml.safe_load(open(compose_file, 'r'))
    except yaml.YAMLError:
        messages.append(
            ValidationItem(
                level='ERROR',
                message='The file *docker-compose.yml* is not valid.',
                file=compose_file,
            ),
        )
        return ValidationResult(items=messages)

    runner_image = f'cloudblueconnect/connect-extension-runner:{context["runner_version"]}'

    for service in data['services']:
        image = data['services'][service].get('image')
        if image.startswith('cloudblueconnect/connect-extension-runner') and image != runner_image:
            messages.append(
                ValidationItem(
                    level='ERROR',
                    message=(
                        f'Invalid image for service *{service}*: '
                        f'expected *{runner_image}* got *{image}*.'
                    ),
                    file=compose_file,
                ),
            )
    return ValidationResult(items=messages)


def validate_variables(context):  # noqa: CCR001

    messages = []

    for _, extension_class in context['extension_classes'].items():

        variables = extension_class.get_variables()
        variable_name_pattern = r'^[A-Za-z](?:[A-Za-z0-9_\-.]+)*$'
        variable_name_regex = re.compile(variable_name_pattern)

        names = []

        for variable in variables:
            if 'name' not in variable:
                messages.append(
                    ValidationItem(
                        level='ERROR',
                        message='Invalid variable declaration: the *name* attribute is mandatory.',
                        **get_code_context(extension_class, '@variables'),
                    ),
                )
                continue

            if variable["name"] in names:
                messages.append(
                    ValidationItem(
                        level='ERROR',
                        message=(
                            f'Duplicate variable name: the variable with name *{variable["name"]}* '
                            'has already been declared.'
                        ),
                        **get_code_context(extension_class, '@variables'),
                    ),
                )

            names.append(variable["name"])

            if not variable_name_regex.match(variable['name']):
                messages.append(
                    ValidationItem(
                        level='ERROR',
                        message=(
                            f'Invalid variable name: the value *{variable["name"]}* '
                            f'does not match the pattern *{variable_name_pattern}*.'
                        ),
                        **get_code_context(extension_class, '@variables'),
                    ),
                )
            if 'initial_value' in variable and not isinstance(variable['initial_value'], str):
                messages.append(
                    ValidationItem(
                        level='ERROR',
                        message=(
                            f'Invalid *initial_value* attribute for variable *{variable["name"]}*: '
                            f'must be a non-null string not *{type(variable["initial_value"])}*.'
                        ),
                        **get_code_context(extension_class, '@variables'),
                    ),
                )

            if 'secure' in variable and not isinstance(variable['secure'], bool):
                messages.append(
                    ValidationItem(
                        level='ERROR',
                        message=(
                            f'Invalid *secure* attribute for variable *{variable["name"]}*: '
                            f'must be a boolean not *{type(variable["secure"])}*.'
                        ),
                        **get_code_context(extension_class, '@variables'),
                    ),
                )

    return ValidationResult(items=messages)


def validate_extension_json(context):
    messages = []
    extension_class = list(context['extension_classes'].values())[0]
    extension_class_file = inspect.getsourcefile(extension_class)
    extension_json_file = os.path.join(
        os.path.dirname(extension_class_file),
        'extension.json',
    )
    descriptor = None
    try:
        descriptor = extension_class.get_descriptor()
    except FileNotFoundError:
        messages.append(
            ValidationItem(
                level='ERROR',
                message='The extension descriptor *extension.json* cannot be loaded.',
                file=extension_json_file,
            ),
        )
        return ValidationResult(items=messages, must_exit=True)

    # validate required fields

    return ValidationResult(items=messages, context={
        'descriptor': descriptor,
        'extension_json_file': extension_json_file,
    })
