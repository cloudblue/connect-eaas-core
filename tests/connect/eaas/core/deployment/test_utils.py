import pytest

from connect.client import ConnectClient
from connect.eaas.core.deployment.utils import (
    extract_arguments,
    get_git_data,
    preprocess_variables,
    process_variables,
)


@pytest.mark.django_db
def test_extract_arguments_ok(mocker):
    tempdir_mock = mocker.MagicMock()
    tempdir_mock.__enter__.return_value = '/tmp'
    mocker.patch(
        'connect.eaas.core.deployment.utils.tempfile.TemporaryDirectory',
        return_value=tempdir_mock,
    )
    mocker.patch('connect.eaas.core.deployment.utils.clone_repo', return_value=None)

    path_mock = mocker.MagicMock()
    mocker.patch('connect.eaas.core.deployment.utils.Path', return_value=path_mock)
    mocker.patch('connect.eaas.core.deployment.utils.os.path.exists', return_value=True)
    yaml_data = """
    package_id: package.id
    tag: 27.17
    env: test
    type: multiaccount
    var:
        DB_HOST:
            value: localhost
            secure: false
        DB_PASSWORD:
            value: password
            secure: true
        ENV_VAR: null
    """
    mock_open = mocker.mock_open(read_data=yaml_data)
    mocker.patch('connect.eaas.core.deployment.utils.open', mock_open)

    deploy_args, _ = extract_arguments('https://github.com/test/repo.git')
    assert deploy_args == {
        'package_id': 'package.id',
        'tag': 27.17,
        'env': 'test',
        'type': 'multiaccount',
        'var': {
            'DB_HOST': {
                'value': 'localhost',
                'secure': False,
            },
            'DB_PASSWORD': {
                'value': 'password',
                'secure': True,
            },
            'ENV_VAR': None,
        },
    }


@pytest.mark.django_db
def test_extract_arguments_clone_error(mocker):
    tempdir_mock = mocker.MagicMock()
    tempdir_mock.__enter__.return_value = '/tmp'
    mocker.patch(
        'connect.eaas.core.deployment.utils.tempfile.TemporaryDirectory',
        return_value=tempdir_mock,
    )
    mocker.patch(
        'connect.eaas.core.deployment.utils.clone_repo',
        return_value='some error',
    )

    _, error = extract_arguments('https://github.com/test/repo.git')

    assert error == 'some error'


@pytest.mark.django_db
def test_extract_arguments_no_yaml(mocker):
    tempdir_mock = mocker.MagicMock()
    tempdir_mock.__enter__.return_value = '/tmp'
    mocker.patch(
        'connect.eaas.core.deployment.utils.tempfile.TemporaryDirectory',
        return_value=tempdir_mock,
    )
    mocker.patch('connect.eaas.core.deployment.utils.clone_repo', return_value=None)
    path_mock = mocker.MagicMock()
    mocker.patch('connect.eaas.core.deployment.utils.Path', return_value=path_mock)

    _, error = extract_arguments('https://github.com/test/repo.git')

    assert 'No such file' in error.message
    assert '.connect_deployment.yaml' in error.message


@pytest.mark.django_db
def test_extract_arguments_error_opening_file(mocker):
    tempdir_mock = mocker.MagicMock()
    tempdir_mock.__enter__.return_value = '/tmp'
    mocker.patch(
        'connect.eaas.core.deployment.utils.tempfile.TemporaryDirectory',
        return_value=tempdir_mock,
    )
    mocker.patch('connect.eaas.core.deployment.utils.clone_repo', return_value=None)
    path_mock = mocker.MagicMock()
    mocker.patch('connect.eaas.core.deployment.utils.Path', return_value=path_mock)
    mocker.patch(
        'connect.eaas.core.deployment.utils.open',
        side_effect=OSError('Unable to open'),
    )

    _, error = extract_arguments('https://github.com/test/repo.git')

    assert error.message == 'Error opening file: Unable to open'


@pytest.mark.django_db
def test_extract_arguments_scanner_error(mocker):
    tempdir_mock = mocker.MagicMock()
    tempdir_mock.__enter__.return_value = '/tmp'
    mocker.patch(
        'connect.eaas.core.deployment.utils.tempfile.TemporaryDirectory',
        return_value=tempdir_mock,
    )
    mocker.patch('connect.eaas.core.deployment.utils.clone_repo', return_value=None)

    path_mock = mocker.MagicMock()
    mocker.patch('connect.eaas.core.deployment.utils.Path', return_value=path_mock)
    yaml_data = """
        package_id: package.id
        tag: 27.17
        env
    """
    mock_open = mocker.mock_open(read_data=yaml_data)
    mocker.patch('connect.eaas.core.deployment.utils.open', mock_open)

    _, error = extract_arguments('https://github.com/test/repo.git')

    assert 'Invalid deployment file' in error.message


def test_extract_arguments_no_type(mocker):
    tempdir_mock = mocker.MagicMock()
    tempdir_mock.__enter__.return_value = '/tmp'
    mocker.patch(
        'connect.eaas.core.deployment.utils.tempfile.TemporaryDirectory',
        return_value=tempdir_mock,
    )
    mocker.patch('connect.eaas.core.deployment.utils.clone_repo', return_value=None)

    path_mock = mocker.MagicMock()
    mocker.patch('connect.eaas.core.deployment.utils.Path', return_value=path_mock)
    yaml_data = """
        package_id: package.id
        """
    mock_open = mocker.mock_open(read_data=yaml_data)
    mocker.patch('connect.eaas.core.deployment.utils.open', mock_open)
    mocker.patch(
        'connect.eaas.core.deployment.utils.toml.load',
        return_value={
            'tool': {'poetry': {'plugins': {'connect.eaas.ext': {'tfnapp': 'TfnApp'}}}},
        },
    )

    deploy_args, _ = extract_arguments('https://github.com/test/repo')
    assert deploy_args['type'] == 'transformations'


def test_extract_arguments_invalid_pyprj(mocker):
    tempdir_mock = mocker.MagicMock()
    tempdir_mock.__enter__.return_value = '/tmp'
    mocker.patch(
        'connect.eaas.core.deployment.utils.tempfile.TemporaryDirectory',
        return_value=tempdir_mock,
    )
    mocker.patch('connect.eaas.core.deployment.utils.clone_repo', return_value=None)

    path_mock = mocker.MagicMock()
    mocker.patch('connect.eaas.core.deployment.utils.Path', return_value=path_mock)
    yaml_data = """
        package_id: package.id
        """
    mock_open = mocker.mock_open(read_data=yaml_data)
    mocker.patch('connect.eaas.core.deployment.utils.open', mock_open)
    mocker.patch(
        'connect.eaas.core.deployment.utils.toml.load',
        return_value={'tool': {'connect.eaas.ext': {'tfnapp': 'TfnApp'}}},
    )

    _, error = extract_arguments('https://github.com/test/repo')
    assert 'Error extracting data' in error.message


def test_extract_arguments_with_icon(mocker):
    tempdir_mock = mocker.MagicMock()
    tempdir_mock.__enter__.return_value = '/tmp'
    mocker.patch(
        'connect.eaas.core.deployment.utils.tempfile.TemporaryDirectory',
        return_value=tempdir_mock,
    )
    mocker.patch('connect.eaas.core.deployment.utils.clone_repo', return_value=None)

    path_mock = mocker.MagicMock()
    mocker.patch('connect.eaas.core.deployment.utils.Path', return_value=path_mock)
    yaml_data = """
            package_id: package.id
            type: multiaccount
            icon: path/to/icon.png
            """
    mock_open = mocker.mock_open(read_data=yaml_data)
    mocker.patch('connect.eaas.core.deployment.utils.open', mock_open)

    deploy_args, _ = extract_arguments('https://github.com/test/repo', is_install=True)
    assert deploy_args['icon'] is not None
    assert not isinstance(deploy_args['icon'], str)


def test_preprocess_variables(mocker):
    mocker.patch(
        'connect.eaas.core.deployment.utils.os.getenv',
        return_value='env_value',
    )

    result = preprocess_variables(
        {
            'package_id': 'package.id',
            'var': {
                'DB_HOST': {
                    'value': 'localhost',
                    'secure': True,
                },
                'DB_PASSWORD': {
                    'value': 'password',
                },
                'ENV_VAR': None,
            },
        },
    )

    assert result == {
        'DB_HOST': {
            'value': 'localhost',
            'secure': True,
        },
        'DB_PASSWORD': {
            'value': 'password',
            'secure': False,
        },
        'ENV_VAR': {
            'value': 'env_value',
            'secure': False,
        },
    }


def test_process_variables_ok(responses):
    env_api = 'https://localhost/public/v1/devops/services/SRV-001/environments/ENV-001'
    responses.add(
        'GET',
        f'{env_api}/variables',
        json=[
            {
                'id': 'VAR-1',
                'name': 'DB_HOST',
                'value': 'old-localhost',
                'secure': True,
            },
            {
                'id': 'VAR-2',
                'name': 'DB_USER',
                'value': 'user',
                'secure': False,
            },
        ],
        status=200,
    )
    mock_put = responses.add(
        'PUT',
        f'{env_api}/variables/VAR-1',
        json={},
        status=201,
    )
    mock_post = responses.add(
        'POST',
        f'{env_api}/variables',
        json={},
        status=201,
    )

    arguments = {
        'var': {
            'DB_HOST': {
                'value': 'localhost',
                'secure': True,
            },
            'DB_USER': {
                'value': 'user',
                'secure': False,
            },
            'DB_PASSWORD': {
                'value': 'password',
                'secure': True,
            },
        },
    }
    client = ConnectClient('ApiKey XXX:YYY', endpoint='https://localhost/public/v1')
    process_variables(arguments, client('devops').services['SRV-001'].environments['ENV-001'])

    assert mock_put.call_count == 1
    assert mock_post.call_count == 1


def test_get_git_data_ok(mocker):
    mocker.patch(
        'connect.eaas.core.deployment.utils.list_tags',
        return_value=({'1.2': 'hash 1.2', '1.1': 'hash 1.1'}, None),
    )

    result, _ = get_git_data('https://github.com/test/repo', 1.1)
    assert result == {
        'tag': '1.1',
        'commit': 'hash 1.1',
        'url': 'https://github.com/test/repo',
    }


def test_get_git_data_no_tag_ok(mocker):
    mocker.patch(
        'connect.eaas.core.deployment.utils.list_tags',
        return_value=({'1.2': 'hash 1.2', '1.1': 'hash 1.1'}, None),
    )

    result, _ = get_git_data('https://github.com/test/repo', None)
    assert result['tag'] == '1.2'


def test_get_git_data_list_tag_error(mocker):
    mocker.patch(
        'connect.eaas.core.deployment.utils.list_tags',
        return_value=(None, mocker.MagicMock(message='some error')),
    )

    _, error = get_git_data('https://github.com/test/repo', None)
    assert 'Cannot retrieve git repository https://github.com/test/repo tags info' in error.message


def test_get_git_data_invalid_tag(mocker):
    mocker.patch(
        'connect.eaas.core.deployment.utils.list_tags',
        return_value=({'1.2': 'hash 1.2', '1.1': 'hash 1.1'}, None),
    )

    _, error = get_git_data('https://github.com/test/repo', '1.1.1')
    assert error.message == 'Invalid tag: 1.1.1.'
