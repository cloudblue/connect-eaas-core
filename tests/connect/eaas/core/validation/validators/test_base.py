import toml
import yaml

from connect.eaas.core.validation.models import ValidationItem, ValidationResult
from connect.eaas.core.validation.validators.base import (
    validate_docker_compose_yml,
    validate_extension_json,
    validate_pyproject_toml,
    validate_variables,
)


def test_validate_pyproject_toml_file_not_found(mocker):
    result = validate_pyproject_toml({'project_dir': 'fake_dir'})

    assert isinstance(result, ValidationResult)
    assert result.must_exit is True
    assert len(result.items) == 1
    item = result.items[0]
    assert isinstance(item, ValidationItem)
    assert item.level == 'ERROR'
    assert (
        'The mandatory *pyproject.toml* project descriptor file'
        ' is not present in the folder fake_dir.'
    ) in item.message
    assert item.file == 'fake_dir/pyproject.toml'


def test_validate_pyproject_toml_invalid_toml(mocker):
    mocker.patch(
        'connect.eaas.core.validation.validators.base.os.path.isfile',
        return_value=True,
    )
    mocker.patch(
        'connect.eaas.core.validation.validators.base.toml.load',
        side_effect=toml.TomlDecodeError('error', 'error', 0),
    )

    result = validate_pyproject_toml({'project_dir': 'fake_dir'})

    assert isinstance(result, ValidationResult)
    assert result.must_exit is True
    assert len(result.items) == 1
    item = result.items[0]
    assert isinstance(item, ValidationItem)
    assert item.level == 'ERROR'
    assert 'The project descriptor file *pyproject.toml* is not a valid toml file.' in item.message
    assert item.file == 'fake_dir/pyproject.toml'


def test_validate_pyproject_toml_depends_on_runner(mocker):
    mocker.patch(
        'connect.eaas.core.validation.validators.base.os.path.isfile',
        return_value=True,
    )
    mocker.patch(
        'connect.eaas.core.validation.validators.base.toml.load',
        return_value={
            'tool': {
                'poetry': {
                    'dependencies': {
                        'connect-extension-runner': '23',
                    },
                    'plugins': {
                        'connect.eaas.ext': {
                            'eventsapp': 'root_pkg.extension:MyExtension',
                        },
                    },
                },
            },
        },
    )
    mocker.patch('connect.eaas.core.validation.validators.base.importlib.import_module')
    mocker.patch(
        'connect.eaas.core.validation.validators.base.inspect.getmembers',
        return_value=[],
    )

    result = validate_pyproject_toml({'project_dir': 'fake_dir'})

    assert isinstance(result, ValidationResult)
    assert result.must_exit is False
    assert len(result.items) == 1
    item = result.items[0]
    assert isinstance(item, ValidationItem)
    assert item.level == 'WARNING'
    assert 'Extensions must depend on *connect-eaas-core* library' in item.message
    assert 'not *connect-extension-runner*.' in item.message
    assert item.file == 'fake_dir/pyproject.toml'


def test_validate_pyproject_toml_missed_eaas_core_dependency(mocker):
    mocker.patch(
        'connect.eaas.core.validation.validators.base.os.path.isfile',
        return_value=True,
    )
    mocker.patch(
        'connect.eaas.core.validation.validators.base.toml.load',
        return_value={
            'tool': {
                'poetry': {
                    'dependencies': {},
                    'plugins': {
                        'connect.eaas.ext': {
                            'eventsapp': 'root_pkg.extension:MyExtension',
                        },
                    },
                },
            },
        },
    )
    mocker.patch('connect.eaas.core.validation.validators.base.importlib.import_module')
    mocker.patch(
        'connect.eaas.core.validation.validators.base.inspect.getmembers',
        return_value=[],
    )

    result = validate_pyproject_toml({'project_dir': 'fake_dir'})

    assert isinstance(result, ValidationResult)
    assert result.must_exit is False
    assert len(result.items) == 1
    item = result.items[0]
    assert isinstance(item, ValidationItem)
    assert item.level == 'ERROR'
    assert 'No dependency on *connect-eaas-core* has been found.' in item.message
    assert item.file == 'fake_dir/pyproject.toml'


def test_validate_pyproject_toml_no_extension_declaration(mocker):
    mocker.patch(
        'connect.eaas.core.validation.validators.base.os.path.isfile',
        return_value=True,
    )
    mocker.patch(
        'connect.eaas.core.validation.validators.base.toml.load',
        return_value={
            'tool': {
                'poetry': {
                    'dependencies': {
                        'connect-eaas-core': '1.0.0',
                    },
                },
            },
        },
    )
    mocker.patch('connect.eaas.core.validation.validators.base.importlib.import_module')
    mocker.patch(
        'connect.eaas.core.validation.validators.base.inspect.getmembers',
        return_value=[],
    )

    result = validate_pyproject_toml({'project_dir': 'fake_dir'})

    assert isinstance(result, ValidationResult)
    assert result.must_exit is True
    assert len(result.items) == 1
    item = result.items[0]
    assert isinstance(item, ValidationItem)
    assert item.level == 'ERROR'
    assert 'No extension declaration has been found.' in item.message
    assert item.file == 'fake_dir/pyproject.toml'


def test_validate_pyproject_toml_invalid_extension_declaration(mocker):
    mocker.patch(
        'connect.eaas.core.validation.validators.base.os.path.isfile',
        return_value=True,
    )
    mocker.patch(
        'connect.eaas.core.validation.validators.base.toml.load',
        return_value={
            'tool': {
                'poetry': {
                    'dependencies': {
                        'connect-eaas-core': '1.0.0',
                    },
                    'plugins': {
                        'connect.eaas.ext': {
                            'other_key': 'root_pkg.extension:MyExtension',
                        },
                    },
                },
            },
        },
    )
    mocker.patch('connect.eaas.core.validation.validators.base.importlib.import_module')
    mocker.patch(
        'connect.eaas.core.validation.validators.base.inspect.getmembers',
        return_value=[],
    )

    result = validate_pyproject_toml({'project_dir': 'fake_dir'})

    assert isinstance(result, ValidationResult)
    assert result.must_exit is True
    assert len(result.items) == 1
    item = result.items[0]
    assert isinstance(item, ValidationItem)
    assert item.level == 'ERROR'
    assert 'Invalid application declaration in' in item.message
    assert item.file == 'fake_dir/pyproject.toml'


def test_validate_pyproject_toml_deprecated_extension_declaration(mocker):
    mocker.patch(
        'connect.eaas.core.validation.validators.base.os.path.isfile',
        return_value=True,
    )
    mocker.patch(
        'connect.eaas.core.validation.validators.base.toml.load',
        return_value={
            'tool': {
                'poetry': {
                    'dependencies': {
                        'connect-eaas-core': '1.0.0',
                    },
                    'plugins': {
                        'connect.eaas.ext': {
                            'extension': 'root_pkg.extension:MyExtension',
                        },
                    },
                },
            },
        },
    )
    mocker.patch('connect.eaas.core.validation.validators.base.importlib.import_module')
    mocker.patch(
        'connect.eaas.core.validation.validators.base.inspect.getmembers',
        return_value=[],
    )

    result = validate_pyproject_toml({'project_dir': 'fake_dir'})

    assert isinstance(result, ValidationResult)
    assert result.must_exit is False
    assert len(result.items) == 1
    item = result.items[0]
    assert isinstance(item, ValidationItem)
    assert item.level == 'WARNING'
    assert item.message == (
        'Declaring an events application using the *extension* entrypoint name is '
        'deprecated in favor of *eventsapp*.'
    )
    assert item.file == 'fake_dir/pyproject.toml'


def test_validate_pyproject_toml_import_error(mocker):
    mocker.patch(
        'connect.eaas.core.validation.validators.base.os.path.isfile',
        return_value=True,
    )
    mocker.patch(
        'connect.eaas.core.validation.validators.base.toml.load',
        return_value={
            'tool': {
                'poetry': {
                    'dependencies': {
                        'connect-eaas-core': '1.0.0',
                    },
                    'plugins': {
                        'connect.eaas.ext': {
                            'eventsapp': 'root_pkg.extension:MyExtension',
                        },
                    },
                },
            },
        },
    )
    mocker.patch(
        'connect.eaas.core.validation.validators.base.importlib.import_module',
        side_effect=ImportError(),
    )

    result = validate_pyproject_toml({'project_dir': 'fake_dir'})

    assert isinstance(result, ValidationResult)
    assert result.must_exit is True
    assert len(result.items) == 1
    item = result.items[0]
    assert isinstance(item, ValidationItem)
    assert item.level == 'ERROR'
    assert 'The application class *root_pkg.extension:MyExtension* cannot be loaded' in item.message
    assert item.file == 'fake_dir/pyproject.toml'


def test_validate_variables_no_name(mocker):
    extension_class = mocker.MagicMock()
    extension_class.get_variables.return_value = [{
        'initial_value': 'value',
    }]
    context = {'extension_classes': {'extension': extension_class}}

    mocker.patch(
        'connect.eaas.core.validation.validators.base.get_code_context',
        return_value={
            'file': 'file',
            'start_line': 0,
            'lineno': 5,
            'code': 'code',
        },
    )

    result = validate_variables(context)

    assert isinstance(result, ValidationResult)
    assert result.must_exit is False
    assert len(result.items) == 1
    item = result.items[0]
    assert isinstance(item, ValidationItem)
    assert item.level == 'ERROR'
    assert 'Invalid variable declaration: the *name* attribute is mandatory.' in item.message
    assert item.file == 'file'
    assert item.start_line == 0
    assert item.lineno == 5
    assert item.code == 'code'


def test_validate_variables_non_unique(mocker):
    extension_class = mocker.MagicMock()
    extension_class.get_variables.return_value = [
        {'name': 'VAR1'},
        {'name': 'VAR1'},
    ]
    context = {'extension_classes': {'extension': extension_class}}

    mocker.patch(
        'connect.eaas.core.validation.validators.base.get_code_context',
        return_value={
            'file': 'file',
            'start_line': 0,
            'lineno': 5,
            'code': 'code',
        },
    )

    result = validate_variables(context)

    assert isinstance(result, ValidationResult)
    assert result.must_exit is False
    assert len(result.items) == 1
    item = result.items[0]
    assert isinstance(item, ValidationItem)
    assert item.level == 'ERROR'
    assert (
        'Duplicate variable name: the variable with name *VAR1* '
        'has already been declared.'
    ) in item.message
    assert item.file == 'file'
    assert item.start_line == 0
    assert item.lineno == 5
    assert item.code == 'code'


def test_validate_variables_invalid_name(mocker):
    extension_class = mocker.MagicMock()
    extension_class.get_variables.return_value = [
        {'name': '1VAR'},
    ]
    context = {'extension_classes': {'extension': extension_class}}

    mocker.patch(
        'connect.eaas.core.validation.validators.base.get_code_context',
        return_value={
            'file': 'file',
            'start_line': 0,
            'lineno': 5,
            'code': 'code',
        },
    )

    result = validate_variables(context)

    assert isinstance(result, ValidationResult)
    assert result.must_exit is False
    assert len(result.items) == 1
    item = result.items[0]
    assert isinstance(item, ValidationItem)
    assert item.level == 'ERROR'
    assert 'Invalid variable name: the value *1VAR* does not match' in item.message
    assert item.file == 'file'
    assert item.start_line == 0
    assert item.lineno == 5
    assert item.code == 'code'


def test_validate_variables_invalid_initial_value(mocker):
    extension_class = mocker.MagicMock()
    extension_class.get_variables.return_value = [
        {
            'name': 'VAR1',
            'initial_value': mocker.MagicMock(),
        },
    ]
    context = {'extension_classes': {'extension': extension_class}}

    mocker.patch(
        'connect.eaas.core.validation.validators.base.get_code_context',
        return_value={
            'file': 'file',
            'start_line': 0,
            'lineno': 5,
            'code': 'code',
        },
    )

    result = validate_variables(context)

    assert isinstance(result, ValidationResult)
    assert result.must_exit is False
    assert len(result.items) == 1
    item = result.items[0]
    assert isinstance(item, ValidationItem)
    assert item.level == 'ERROR'
    assert 'Invalid *initial_value* attribute for variable *VAR1*:' in item.message
    assert item.file == 'file'
    assert item.start_line == 0
    assert item.lineno == 5
    assert item.code == 'code'


def test_validate_variables_invalid_secure(mocker):
    extension_class = mocker.MagicMock()
    extension_class.get_variables.return_value = [
        {
            'name': 'VAR1',
            'secure': mocker.MagicMock(),
        },
    ]
    context = {'extension_classes': {'extension': extension_class}}

    mocker.patch(
        'connect.eaas.core.validation.validators.base.get_code_context',
        return_value={
            'file': 'file',
            'start_line': 0,
            'lineno': 5,
            'code': 'code',
        },
    )

    result = validate_variables(context)

    assert isinstance(result, ValidationResult)
    assert result.must_exit is False
    assert len(result.items) == 1
    item = result.items[0]
    assert isinstance(item, ValidationItem)
    assert item.level == 'ERROR'
    assert 'Invalid *secure* attribute for variable *VAR1*:' in item.message
    assert item.file == 'file'
    assert item.start_line == 0
    assert item.lineno == 5
    assert item.code == 'code'


def test_validate_docker_compose_yml_not_found(mocker):
    result = validate_docker_compose_yml({'project_dir': 'fake_dir'})

    assert isinstance(result, ValidationResult)
    assert result.must_exit is False
    assert len(result.items) == 1
    item = result.items[0]
    assert isinstance(item, ValidationItem)
    assert item.level == 'WARNING'
    assert 'the file *docker-compose.yml* is not present.' in item.message
    assert item.file == 'fake_dir/docker-compose.yml'


def test_validate_docker_compose_yml_invalid_yml(mocker):
    mocker.patch(
        'connect.eaas.core.validation.validators.base.os.path.isfile',
        return_value=True,
    )
    mocker.patch(
        'connect.eaas.core.validation.validators.base.open',
    )
    mocker.patch(
        'connect.eaas.core.validation.validators.base.yaml.safe_load',
        side_effect=yaml.YAMLError(),
    )

    result = validate_docker_compose_yml({'project_dir': 'fake_dir'})

    assert isinstance(result, ValidationResult)
    assert result.must_exit is False
    assert len(result.items) == 1
    item = result.items[0]
    assert isinstance(item, ValidationItem)
    assert item.level == 'ERROR'
    assert 'The file *docker-compose.yml* is not valid.' in item.message
    assert item.file == 'fake_dir/docker-compose.yml'


def test_validate_docker_compose_yml_invalid_image(mocker):
    mocker.patch(
        'connect.eaas.core.validation.validators.base.os.path.isfile',
        return_value=True,
    )
    mocker.patch(
        'connect.eaas.core.validation.validators.base.open',
    )
    mocker.patch(
        'connect.eaas.core.validation.validators.base.yaml.safe_load',
        return_value={
            'services': {
                'dev': {
                    'image': 'cloudblueconnect/connect-extension-runner:0.3',
                },
            },
        },
    )

    result = validate_docker_compose_yml({'project_dir': 'fake_dir', 'runner_version': '1.0'})

    assert isinstance(result, ValidationResult)
    assert result.must_exit is False
    assert len(result.items) == 1
    item = result.items[0]
    assert isinstance(item, ValidationItem)
    assert item.level == 'ERROR'
    assert (
        'Invalid image for service *dev*: expected '
        '*cloudblueconnect/connect-extension-runner:1.0* '
        'got *cloudblueconnect/connect-extension-runner:0.3*.'
    ) in item.message
    assert item.file == 'fake_dir/docker-compose.yml'


def test_validate_docker_compose_yml_invalid_image_dockerfile(mocker):
    mocker.patch(
        'connect.eaas.core.validation.validators.base.os.path.isfile',
        return_value=True,
    )
    mocker.patch(
        'connect.eaas.core.validation.validators.base.open',
        side_effect=['', 'FROM cloudblueconnect/connect-extension-runner:0.3\n'],
    )
    mocker.patch(
        'connect.eaas.core.validation.validators.base.yaml.safe_load',
        return_value={
            'services': {
                'dev': {
                    'build': {'dockerfile': 'Dockerfile'},
                },
            },
        },
    )

    result = validate_docker_compose_yml({'project_dir': 'fake_dir', 'runner_version': '1.0'})

    assert isinstance(result, ValidationResult)
    assert result.must_exit is False
    assert len(result.items) == 1
    item = result.items[0]
    assert isinstance(item, ValidationItem)
    assert item.level == 'ERROR'
    assert (
        'Invalid base image in Dockerfile of service *dev*: expected '
        '*cloudblueconnect/connect-extension-runner:1.0* '
        'got *cloudblueconnect/connect-extension-runner:0.3*.'
    ) in item.message
    assert item.file == 'fake_dir/Dockerfile'


def test_validate_docker_compose_yml_invalid_image_no_dockerfile(mocker):
    mocker.patch(
        'connect.eaas.core.validation.validators.base.os.path.isfile',
        side_effect=[True, False],
    )
    mocker.patch(
        'connect.eaas.core.validation.validators.base.open',
    )
    mocker.patch(
        'connect.eaas.core.validation.validators.base.yaml.safe_load',
        return_value={
            'services': {
                'dev': {
                    'build': {'dockerfile': 'Dockerfile'},
                },
            },
        },
    )

    result = validate_docker_compose_yml({'project_dir': 'fake_dir', 'runner_version': '1.0'})

    assert isinstance(result, ValidationResult)
    assert result.must_exit is False
    assert len(result.items) == 1
    item = result.items[0]
    assert isinstance(item, ValidationItem)
    assert item.level == 'ERROR'
    assert (
        'The service *dev* of *docker-compose.yml* points to a '
        'Dockerfile that does not exist.'
    ) == item.message
    assert item.file == 'fake_dir/Dockerfile'


def test_validate_docker_compose_yml_invalid_image_invalid_dockerfile(mocker):
    mocker.patch(
        'connect.eaas.core.validation.validators.base.os.path.isfile',
        side_effect=[True, True],
    )
    mocker.patch(
        'connect.eaas.core.validation.validators.base.open',
        side_effect=['', ''],
    )
    mocker.patch(
        'connect.eaas.core.validation.validators.base.yaml.safe_load',
        return_value={
            'services': {
                'dev': {
                    'build': {'dockerfile': 'Dockerfile'},
                },
            },
        },
    )

    result = validate_docker_compose_yml({'project_dir': 'fake_dir', 'runner_version': '1.0'})

    assert isinstance(result, ValidationResult)
    assert result.must_exit is False
    assert len(result.items) == 1
    item = result.items[0]
    assert isinstance(item, ValidationItem)
    assert item.level == 'ERROR'
    assert (
        'Invalid *Dockerfile* for service *dev*, no FROM statement has been found.'
    ) == item.message
    assert item.file == 'fake_dir/Dockerfile'


def test_validate_docker_compose_yml(mocker):
    mocker.patch(
        'connect.eaas.core.validation.validators.base.os.path.isfile',
        return_value=True,
    )
    mocker.patch(
        'connect.eaas.core.validation.validators.base.open',
    )
    mocker.patch(
        'connect.eaas.core.validation.validators.base.yaml.safe_load',
        return_value={
            'services': {
                'dev': {
                    'image': 'cloudblueconnect/connect-extension-runner:1.0',
                },
            },
        },
    )

    result = validate_docker_compose_yml({'project_dir': 'fake_dir', 'runner_version': '1.0'})

    assert isinstance(result, ValidationResult)
    assert result.must_exit is False
    assert len(result.items) == 0


def test_validate_extension_json(mocker):
    mocker.patch(
        'connect.eaas.core.validation.validators.base.inspect.getsourcefile',
        return_value='/extension.py',
    )

    mocker.patch(
        'connect.eaas.core.validation.validators.base.os.path.dirname',
        return_value='/myextprj',
    )

    extension_class = mocker.MagicMock()
    extension_class.get_descriptor.return_value = {'name': 'my extension', 'audience': ['vendor']}

    result = validate_extension_json(
        {
            'extension_classes': {'extension': extension_class},
        },
    )
    assert isinstance(result, ValidationResult)
    assert len(result.items) == 0
    assert result.context['descriptor'] == {'name': 'my extension', 'audience': ['vendor']}
    assert result.context['extension_json_file'] == '/myextprj/extension.json'


def test_validate_extension_json_file_not_found(mocker):
    mocker.patch(
        'connect.eaas.core.validation.validators.base.inspect.getsourcefile',
        return_value='/extension.py',
    )

    mocker.patch(
        'connect.eaas.core.validation.validators.base.os.path.dirname',
        return_value='/myextprj',
    )

    extension_class = mocker.MagicMock()
    extension_class.get_descriptor.side_effect = FileNotFoundError

    result = validate_extension_json(
        {
            'extension_classes': {'extension': extension_class},
        },
    )
    assert isinstance(result, ValidationResult)
    assert len(result.items) == 1
    assert result.items[0].level == 'ERROR'
    assert result.items[0].message == 'The extension descriptor *extension.json* cannot be loaded.'
    assert result.items[0].file == '/myextprj/extension.json'


def test_validate_extension_json_file_typo_in_roles(mocker):
    mocker.patch(
        'connect.eaas.core.validation.validators.base.inspect.getsourcefile',
        return_value='/extension.py',
    )

    mocker.patch(
        'connect.eaas.core.validation.validators.base.os.path.dirname',
        return_value='/myextprj',
    )

    extension_class = mocker.MagicMock()
    extension_class.get_descriptor.return_value = {'name': 'my extension', 'audience': ['vandor']}

    result = validate_extension_json(
        {
            'extension_classes': {'extension': extension_class},
        },
    )

    assert isinstance(result, ValidationResult)
    assert len(result.items) == 1
    assert result.items[0].level == 'ERROR'
    assert 'Valid values are: *vendor*, *distributor*, *reseller*.' in result.items[0].message
    assert result.items[0].file == '/myextprj/extension.json'
