import importlib
import inspect
import os
import re
import sys
from collections import deque

import yaml

from connect.eaas.core.extension import (
    AnvilExtension,
    EventsExtension,
    Extension,
    WebAppExtension,
)
from connect.eaas.core.responses import (
    CustomEventResponse,
    ProcessingResponse,
    ProductActionResponse,
    ValidationResponse,
)
from connect.eaas.core.validation.helpers import (
    get_code_context,
    get_event_definitions,
    load_project_toml_file,
)
from connect.eaas.core.validation.proto import (
    ValidationItem,
    ValidationResult,
)


def validate_pyproject_toml(project_dir, *args, **kwargs):  # noqa: CCR001
    messages = []

    data = load_project_toml_file(project_dir)
    if isinstance(data, ValidationResult):
        return data

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
                    'No extension declaration has been found.'
                    'The extension must be declared in the '
                    '*[tool.poetry.plugins."connect.eaas.ext"]* section.'
                ),
                file=descriptor_file,
            ),
        )
        return ValidationResult(items=messages, must_exit=True)

    sys.path.append(os.path.join(os.getcwd(), project_dir))
    possible_extensions = ['extension', 'webapp', 'anvil']
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
                            f'The extension class *{extension_dict[extension_type]}* '
                            f'cannot be loaded: {err}.'
                        ),
                        file=descriptor_file,
                    ),
                )
                return ValidationResult(items=messages, must_exit=True)

            defined_classes = [
                member[1]
                for member in inspect.getmembers(extension_module, predicate=inspect.isclass)
            ]

            for deprecated_cls, cls_name in (
                (CustomEventResponse, 'InteractiveResponse'),
                (ProcessingResponse, 'BackgroundResponse'),
                (ProductActionResponse, 'InteractiveResponse'),
                (ValidationResponse, 'InteractiveResponse'),
            ):
                if deprecated_cls in defined_classes:
                    messages.append(
                        ValidationItem(
                            message=(
                                f'The response class *{deprecated_cls.__name__}* '
                                f'has been deprecated in favor of *{cls_name}*.'
                            ),
                            **get_code_context(extension_module, deprecated_cls.__name__),
                        ),
                    )

            extensions[extension_type] = getattr(extension_module, class_name)

    if not extensions:
        messages.append(
            ValidationItem(
                level='ERROR',
                message=(
                    'Invalid extension declaration in *[tool.poetry.plugins."connect.eaas.ext"]*: '
                    'The extension must be declared as: *"extension" = '
                    '"your_package.extension:YourExtension"* '
                    'for Fulfillment automation or Hub integration. '
                    'For Multi account installation must be '
                    'declared at least one the following: *"extension" = '
                    '"your_package.events:YourEventsExtension"*, '
                    '*"webapp" = "your_package.webapp:YourWebAppExtension"*, '
                    '*"anvil" = "your_package.anvil:YourAnvilExtension"*.'
                ),
                file=descriptor_file,
            ),
        )
        return ValidationResult(items=messages, must_exit=True)

    return ValidationResult(items=messages, context={'extension_classes': extensions})


def validate_extension_class(context, *args, **kwargs):  # noqa: CCR001
    messages = []
    class_mapping = {
        'extension': 'connect.eaas.core.extension.[Events]Extension',
        'webapp': 'connect.eaas.core.extension.WebAppExtension',
        'anvil': 'connect.eaas.core.extension.AnvilExtension',
    }
    ext_class = None
    extension_json_file = None

    for extension_type, extension_class in context['extension_classes'].items():
        extension_class_file = inspect.getsourcefile(extension_class)

        if (
            extension_type == 'extension'
            and not issubclass(extension_class, (Extension, EventsExtension))
            or extension_type == 'webapp' and not issubclass(extension_class, WebAppExtension)
            or extension_type == 'anvil' and not issubclass(extension_class, AnvilExtension)
        ):
            messages.append(
                ValidationItem(
                    level='ERROR',
                    message=(
                        f'The extension class *{extension_class.__name__}* '
                        f'is not a subclass of *{class_mapping[extension_type]}*.'
                    ),
                    file=extension_class_file,
                ),
            )
            return ValidationResult(items=messages, must_exit=True)

        if not extension_json_file:  # pragma: no branch
            extension_json_file = os.path.join(
                os.path.dirname(extension_class_file),
                'extension.json',
            )
            ext_class = extension_class

    try:
        descriptor = ext_class.get_descriptor()
    except FileNotFoundError:
        messages.append(
            ValidationItem(
                level='ERROR',
                message='The extension descriptor *extension.json* cannot be loaded.',
                file=extension_json_file,
            ),
        )
        return ValidationResult(items=messages, must_exit=True)

    for description in ['variables', 'capabilities', 'schedulables']:
        if description in descriptor:
            messages.append(
                ValidationItem(
                    message=(
                        f'Extension {description} must be declared using the '
                        f'*connect.eaas.core.decorators.'
                        f'{description if description != "schedulables" else "event"}* decorator.'
                    ),
                    file=extension_json_file,
                ),
            )

    return ValidationResult(items=messages, context={'descriptor': descriptor})


def validate_events(config, context, *args, **kwargs):
    messages = []

    extension_class = context['extension_classes'].get('extension')

    if not extension_class:
        return ValidationResult()

    definitions = {
        definition['type']: definition for definition in get_event_definitions(
            config.active.client,
        )
    }
    events = extension_class.get_events()
    for event in events:
        method = getattr(extension_class, event['method'])
        if event['event_type'] not in definitions:
            messages.append(
                ValidationItem(
                    level='ERROR',
                    message=f'The event type *{event["event_type"]}* is not valid.',
                    **get_code_context(method, '@event'),
                ),
            )
            continue

        statuses = definitions[event['event_type']]['object_statuses']
        if statuses:
            invalid_statuses = set(event['statuses']) - set(statuses)
        else:
            invalid_statuses = set(event['statuses'] or [])
        if invalid_statuses:
            messages.append(
                ValidationItem(
                    level='ERROR',
                    message=(
                        f'The status/es *{", ".join(invalid_statuses)}* are invalid '
                        f'for the event *{event["event_type"]}*.'
                    ),
                    **get_code_context(method, '@event'),
                ),
            )

        signature = inspect.signature(method)
        if len(signature.parameters) != 2:
            sig_str = f'{event["method"]}({", ".join(signature.parameters)})'

            messages.append(
                ValidationItem(
                    level='ERROR',
                    message=(
                        f'The handler for the event *{event["event_type"]}* '
                        f'has an invalid signature: *{sig_str}*'
                    ),
                    **get_code_context(method, sig_str),
                ),
            )
    return ValidationResult(items=messages)


def validate_schedulables(context, *args, **kwargs):
    messages = []

    extension_class = context['extension_classes'].get('extension')

    if not extension_class:
        return ValidationResult()

    schedulables = extension_class.get_schedulables()
    for schedulable in schedulables:
        method = getattr(extension_class, schedulable['method'])
        signature = inspect.signature(method)
        if len(signature.parameters) != 2:
            sig_str = f'{schedulable["method"]}({", ".join(signature.parameters)})'

            messages.append(
                ValidationItem(
                    level='ERROR',
                    message=(
                        f'The schedulable method *{schedulable["method"]}* '
                        f'has an invalid signature: *{sig_str}*'
                    ),
                    **get_code_context(method, sig_str),
                ),
            )
    return ValidationResult(items=messages)


def validate_variables(context, *args, **kwargs):  # noqa: CCR001

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


def validate_webapp_extension(context, *args, **kwargs):  # noqa: CCR001

    messages = []

    if 'webapp' not in context['extension_classes']:
        return ValidationResult()

    extension_class = context['extension_classes']['webapp']
    extension_class_file = inspect.getsourcefile(extension_class)

    if not inspect.getsource(extension_class).strip().startswith('@web_app(router)'):
        messages.append(
            ValidationItem(
                level='ERROR',
                message='The Web app extension class must be wrapped in *@web_app(router)*.',
                file=extension_class_file,
            ),
        )
        return ValidationResult(items=messages, must_exit=True)

    has_router_function = False
    for _, value in inspect.getmembers(extension_class):
        if (
                inspect.isfunction(value)
                and inspect.getsource(value).strip().startswith('@router.')
        ):
            has_router_function = True
            break

    if not has_router_function:
        messages.append(
            ValidationItem(
                level='ERROR',
                message=(
                    'The Web app extension class must contain at least one router '
                    'implementation function wrapped in *@router.your_method("/your_path")*.'
                ),
                file=extension_class_file,
            ),
        )
        return ValidationResult(items=messages, must_exit=True)

    if 'ui' in context['descriptor']:
        extension_json_file = os.path.join(os.path.dirname(extension_class_file), 'extension.json')

        ui_items = deque()
        missed_files = []
        for _, value in context['descriptor']['ui'].items():
            ui_items.append(value)

        while ui_items:
            ui_item = ui_items.pop()
            try:
                url = ui_item['url']
            except KeyError:
                messages.append(
                    ValidationItem(
                        level='ERROR',
                        message=(
                            'The extension descriptor contains incorrect ui item'
                            f'*{ui_item.get("label")}*, url is not presented.'
                        ),
                        file=extension_json_file,
                    ),
                )
                return ValidationResult(items=messages, must_exit=True)

            path = os.path.join(
                os.path.dirname(extension_class_file),
                'static_root',
                url.split('/')[-1],
            )
            if not os.path.exists(path):
                missed_files.append(url)

            for child in ui_item.get('children', []):
                ui_items.append(child)

        if missed_files:
            messages.append(
                ValidationItem(
                    level='ERROR',
                    message=(
                        'The extension descriptor contains missing static files: '
                        f'{", ".join(missed_files)}.'
                    ),
                    file=extension_json_file,
                ),
            )
            return ValidationResult(items=messages, must_exit=True)

    return ValidationResult(items=messages)


def validate_anvil_extension(context, *args, **kwargs):

    messages = []

    if 'anvil' not in context['extension_classes']:
        return ValidationResult()

    extension_class = context['extension_classes']['anvil']
    anvil_key_var = extension_class.get_anvil_key_variable()

    if anvil_key_var:
        variable_name_pattern = r'^[A-Za-z](?:[A-Za-z0-9_\-.]+)*$'
        variable_name_regex = re.compile(variable_name_pattern)

        if not variable_name_regex.match(anvil_key_var):
            messages.append(
                ValidationItem(
                    level='ERROR',
                    message=(
                        f'Invalid Anvil key variable name: the value *{anvil_key_var}* '
                        f'does not match the pattern *{variable_name_pattern}*.'
                    ),
                    file=inspect.getsourcefile(extension_class),
                ),
            )

    return ValidationResult(items=messages)


def validate_docker_compose_yml(project_dir, context, *args, **kwargs):
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
        if image != runner_image:
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


extension_validators = [
    validate_pyproject_toml,
    validate_docker_compose_yml,
    validate_extension_class,
    validate_events,
    validate_variables,
    validate_schedulables,
    validate_webapp_extension,
    validate_anvil_extension,
]
