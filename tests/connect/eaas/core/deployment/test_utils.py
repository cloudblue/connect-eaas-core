import logging

import pytest

from connect.client import ConnectClient
from connect.eaas.core.deployment.helpers import GitException
from connect.eaas.core.deployment.utils import (
    DeploymentError,
    create_extension,
    extract_arguments,
    get_category,
    get_git_data,
    preprocess_variables,
    process_variables,
    stop_environment,
    update_extension,
)


CLIENT = ConnectClient(
    'ApiKey XYZ:XYZ',
    endpoint='https://localhost/public/v1',
)
LOGGER = logging.getLogger('test')


def test_extract_arguments_ok(mocker):
    tempdir_mock = mocker.MagicMock()
    tempdir_mock.__enter__.return_value = '/tmp'
    mocker.patch(
        'connect.eaas.core.deployment.utils.tempfile.TemporaryDirectory',
        return_value=tempdir_mock,
    )
    mocker.patch('connect.eaas.core.deployment.utils.clone_repo')

    path_mock = mocker.MagicMock()
    mocker.patch('connect.eaas.core.deployment.utils.Path', return_value=path_mock)
    mocker.patch('connect.eaas.core.deployment.utils.os.path.exists', return_value=True)
    yaml_data = """
    package_id: package.id
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

    deploy_args = extract_arguments('https://github.com/test/repo.git', '1.0')
    assert deploy_args == {
        'package_id': 'package.id',
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
def test_extract_arguments_ok_with_overview(mocker):
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
    type: multiaccount
    overview: path.to.overview.md
    """
    mock_open = mocker.mock_open(read_data=yaml_data)
    mocker.patch('connect.eaas.core.deployment.utils.open', mock_open)

    deploy_args = extract_arguments('https://github.com/test/repo.git', '1.0')
    assert deploy_args['overview'] is not None


@pytest.mark.django_db
def test_extract_arguments_ok_with_non_existing_overview(mocker):
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
        'connect.eaas.core.deployment.utils.os.path.exists',
        side_effect=[True, True, False],
    )
    yaml_data = """
    package_id: package.id
    type: multiaccount
    overview: path.to.overview.md
    """
    mock_open = mocker.mock_open(read_data=yaml_data)
    mocker.patch('connect.eaas.core.deployment.utils.open', mock_open)

    deploy_args = extract_arguments('https://github.com/test/repo.git', '1.0')
    assert deploy_args['overview'] is None


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
        side_effect=GitException('Server error'),
    )

    with pytest.raises(DeploymentError) as cv:
        extract_arguments('https://github.com/test/repo.git', '1.0')

    assert str(cv.value) == 'Server error'


def test_extract_arguments_no_yaml(mocker):
    tempdir_mock = mocker.MagicMock()
    tempdir_mock.__enter__.return_value = '/tmp'
    mocker.patch(
        'connect.eaas.core.deployment.utils.tempfile.TemporaryDirectory',
        return_value=tempdir_mock,
    )
    mocker.patch('connect.eaas.core.deployment.utils.clone_repo')
    path_mock = mocker.MagicMock()
    mocker.patch('connect.eaas.core.deployment.utils.Path', return_value=path_mock)

    with pytest.raises(DeploymentError) as cv:
        extract_arguments('https://github.com/test/repo.git', '1.0')

    assert 'Deployment file is not found' in str(cv.value)


def test_extract_arguments_error_opening_file(mocker):
    tempdir_mock = mocker.MagicMock()
    tempdir_mock.__enter__.return_value = '/tmp'
    mocker.patch(
        'connect.eaas.core.deployment.utils.tempfile.TemporaryDirectory',
        return_value=tempdir_mock,
    )
    mocker.patch('connect.eaas.core.deployment.utils.clone_repo')
    path_mock = mocker.MagicMock()
    mocker.patch('connect.eaas.core.deployment.utils.Path', return_value=path_mock)
    mocker.patch('connect.eaas.core.deployment.utils.os.path.exists', return_value=True)
    mocker.patch(
        'connect.eaas.core.deployment.utils.open',
        side_effect=OSError('Unable to open'),
    )

    with pytest.raises(DeploymentError) as cv:
        extract_arguments('https://github.com/test/repo.git', '1.0')

    assert str(cv.value) == 'Error opening file: Unable to open'


def test_extract_arguments_scanner_error(mocker):
    tempdir_mock = mocker.MagicMock()
    tempdir_mock.__enter__.return_value = '/tmp'
    mocker.patch(
        'connect.eaas.core.deployment.utils.tempfile.TemporaryDirectory',
        return_value=tempdir_mock,
    )
    mocker.patch('connect.eaas.core.deployment.utils.clone_repo')

    path_mock = mocker.MagicMock()
    mocker.patch('connect.eaas.core.deployment.utils.Path', return_value=path_mock)
    mocker.patch('connect.eaas.core.deployment.utils.os.path.exists', return_value=True)
    yaml_data = """
        package_id: package.id
        tag: 27.17
        env
    """
    mock_open = mocker.mock_open(read_data=yaml_data)
    mocker.patch('connect.eaas.core.deployment.utils.open', mock_open)

    with pytest.raises(DeploymentError) as cv:
        extract_arguments('https://github.com/test/repo.git', '1.0')

    assert 'Invalid deployment file' in str(cv.value)


def test_extract_arguments_no_type(mocker):
    tempdir_mock = mocker.MagicMock()
    tempdir_mock.__enter__.return_value = '/tmp'
    mocker.patch(
        'connect.eaas.core.deployment.utils.tempfile.TemporaryDirectory',
        return_value=tempdir_mock,
    )
    mocker.patch('connect.eaas.core.deployment.utils.clone_repo')

    path_mock = mocker.MagicMock()
    mocker.patch('connect.eaas.core.deployment.utils.Path', return_value=path_mock)
    mocker.patch('connect.eaas.core.deployment.utils.os.path.exists', return_value=True)
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

    deploy_args = extract_arguments('https://github.com/test/repo', '1.0')
    assert deploy_args['type'] == 'transformations'


def test_extract_arguments_invalid_pyprj(mocker):
    tempdir_mock = mocker.MagicMock()
    tempdir_mock.__enter__.return_value = '/tmp'
    mocker.patch(
        'connect.eaas.core.deployment.utils.tempfile.TemporaryDirectory',
        return_value=tempdir_mock,
    )
    mocker.patch('connect.eaas.core.deployment.utils.clone_repo')

    path_mock = mocker.MagicMock()
    mocker.patch('connect.eaas.core.deployment.utils.Path', return_value=path_mock)
    mocker.patch('connect.eaas.core.deployment.utils.os.path.exists', return_value=True)
    yaml_data = """
        package_id: package.id
        """
    mock_open = mocker.mock_open(read_data=yaml_data)
    mocker.patch('connect.eaas.core.deployment.utils.open', mock_open)
    mocker.patch(
        'connect.eaas.core.deployment.utils.toml.load',
        return_value={'tool': {'connect.eaas.ext': {'tfnapp': 'TfnApp'}}},
    )

    with pytest.raises(DeploymentError) as cv:
        extract_arguments('https://github.com/test/repo', '1.0')

    assert 'Error extracting data' in str(cv.value)


def test_extract_arguments_with_icon(mocker):
    tempdir_mock = mocker.MagicMock()
    tempdir_mock.__enter__.return_value = '/tmp'
    mocker.patch(
        'connect.eaas.core.deployment.utils.tempfile.TemporaryDirectory',
        return_value=tempdir_mock,
    )
    mocker.patch('connect.eaas.core.deployment.utils.clone_repo')

    path_mock = mocker.MagicMock()
    mocker.patch('connect.eaas.core.deployment.utils.Path', return_value=path_mock)
    mocker.patch('connect.eaas.core.deployment.utils.os.path.exists', return_value=True)
    yaml_data = """
            package_id: package.id
            type: multiaccount
            icon: path/to/icon.png
            """
    mock_open = mocker.mock_open(read_data=yaml_data)
    mocker.patch('connect.eaas.core.deployment.utils.open', mock_open)

    deploy_args = extract_arguments('https://github.com/test/repo', '1.0')
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
    process_variables(
        arguments,
        client('devops').services['SRV-001'].environments['ENV-001'],
        print,
    )

    assert mock_put.call_count == 1
    assert mock_post.call_count == 1


def test_get_git_data_ok(mocker):
    mocker.patch(
        'connect.eaas.core.deployment.utils.list_tags',
        return_value={'1.2': 'hash 1.2', '1.1': 'hash 1.1'},
    )

    result = get_git_data('https://github.com/test/repo', '1.2')
    assert result == {
        'tag': '1.2',
        'commit': 'hash 1.2',
        'url': 'https://github.com/test/repo',
    }


def test_get_git_data_no_tag_ok(mocker):
    mocker.patch(
        'connect.eaas.core.deployment.utils.list_tags',
        return_value={'1.2': 'hash 1.2', '1.1': 'hash 1.1'},
    )

    result = get_git_data('https://github.com/test/repo', None)
    assert result['tag'] == '1.2'


def test_get_git_data_list_tag_error(mocker):
    mocker.patch(
        'connect.eaas.core.deployment.utils.list_tags',
        side_effect=GitException('Server error'),
    )

    with pytest.raises(DeploymentError) as cv:
        get_git_data('https://github.com/test/repo', None)
    assert 'Cannot retrieve git repository https://github.com/test/repo tags info' in str(cv.value)


def test_get_git_data_invalid_tag(mocker):
    mocker.patch(
        'connect.eaas.core.deployment.utils.list_tags',
        return_value={'1.2': 'hash 1.2', '1.1': 'hash 1.1'},
    )

    with pytest.raises(DeploymentError) as cv:
        get_git_data('https://github.com/test/repo', '1.1.1')
    assert str(cv.value) == 'Tag 1.1.1 doesn\'t exist, please, select one of: 1.2, 1.1.'


def test_get_category_ok(responses):
    responses.add(
        'GET',
        (
            'https://localhost/public/v1/dictionary/extensions/categories?'
            'eq(name,Integration)&limit=1&offset=0'
        ),
        json=[{'id': 'CA-001', 'name': 'Industry'}],
        status=200,
    )

    category = get_category(CLIENT, {'category': 'Integration'}, LOGGER.info)

    assert category == {'id': 'CA-001'}


def test_get_category_empty_ok(responses):
    category = get_category(CLIENT, {}, LOGGER.info)
    assert category is None


def test_get_category_filter_error(caplog, responses):
    responses.add(
        'GET',
        (
            'https://localhost/public/v1/dictionary/extensions/categories?'
            'eq(name,Integration)&limit=1&offset=0'
        ),
        json={},
        status=400,
    )

    with caplog.at_level(logging.DEBUG):
        category = get_category(
            CLIENT,
            {'category': 'Integration'},
            LOGGER.info,
        )

    assert 'Error during looking up category: 400 Bad Request. Skip it.' in caplog.text
    assert category is None


def test_get_category_empty_filter(caplog, responses):
    responses.add(
        'GET',
        (
            'https://localhost/public/v1/dictionary/extensions/categories'
            '?eq(name,Integration)&limit=1&offset=0'
        ),
        json=[],
        status=200,
    )

    with caplog.at_level(logging.DEBUG):
        category = get_category(
            CLIENT,
            {'category': 'Integration'},
            LOGGER.info,
        )

    assert 'Category Integration was not found.' in caplog.text
    assert category is None


def test_create_extension_ok(responses):
    responses.add(
        'POST',
        'https://localhost/public/v1/devops/services',
        json={'id': 'SRV-001'},
        status=201,
    )

    extension = create_extension(
        CLIENT,
        {'type': 'multiaccount', 'package_id': 'test.ext', 'name': 'Extension'},
        LOGGER.info,
    )

    assert extension == {'id': 'SRV-001'}


def test_create_extension_with_icon_ok(responses):
    responses.add(
        'POST',
        'https://localhost/public/v1/devops/services',
        json={'id': 'SRV-001'},
        status=201,
    )
    responses.add(
        'PUT',
        'https://localhost/public/v1/devops/services/SRV-001',
        json={'id': 'SRV-001', 'icon': 'icon'},
        status=201,
    )

    extension = create_extension(
        CLIENT,
        {'type': 'multiaccount', 'package_id': 'test.ext', 'name': 'Extension', 'icon': 'icon'},
        LOGGER.info,
    )

    assert extension == {'id': 'SRV-001', 'icon': 'icon'}


def test_create_extension_error(caplog, responses):
    responses.add(
        'POST',
        'https://localhost/public/v1/devops/services',
        json={},
        status=400,
    )

    with caplog.at_level(logging.DEBUG):
        extension = create_extension(
            CLIENT,
            {'type': 'multiaccount', 'package_id': 'test.ext', 'name': 'Extension'},
            LOGGER.info,
        )

    assert 'Error creating extension' in caplog.text
    assert extension is None


def test_update_extension_ok(responses):
    responses.add(
        'PUT',
        'https://localhost/public/v1/devops/services/SRV-001',
        json={'id': 'SRV-001'},
        status=201,
    )

    extension = update_extension(
        CLIENT,
        {'id': 'SRV-001'},
        {'type': 'multiaccount', 'package_id': 'test.ext', 'name': 'Extension'},
        LOGGER.info,
    )

    assert extension == {'id': 'SRV-001'}


def test_update_extension_error(responses):
    responses.add(
        'PUT',
        'https://localhost/public/v1/devops/services/SRV-001',
        json={},
        status=400,
    )

    extension = update_extension(
        CLIENT,
        {'id': 'SRV-001'},
        {'type': 'multiaccount', 'package_id': 'test.ext', 'name': 'Extension'},
        LOGGER.info,
    )

    assert extension is None


def test_stop_environment_ok_stopped():
    env = stop_environment(
        {'id': 'ENV-001', 'status': 'stopped'},
        CLIENT('devops').services['SRV-001'].environments['ENV-001'],
        LOGGER.info,
    )

    assert env == {'id': 'ENV-001', 'status': 'stopped'}


def test_stop_environment_ok(caplog, responses):
    responses.add(
        'POST',
        'https://localhost/public/v1/devops/services/SRV-001/environments/ENV-001/stop',
        json={},
        status=201,
    )
    responses.add(
        'GET',
        'https://localhost/public/v1/devops/services/SRV-001/environments/ENV-001',
        json={'id': 'ENV-001', 'status': 'running'},
        status=200,
    )
    responses.add(
        'GET',
        'https://localhost/public/v1/devops/services/SRV-001/environments/ENV-001',
        json={'id': 'ENV-001', 'status': 'stopped'},
        status=200,
    )

    with caplog.at_level(logging.DEBUG):
        env = stop_environment(
            {
                'id': 'ENV-001',
                'status': 'running',
                'type': 'test',
            },
            CLIENT('devops').services['SRV-001'].environments['ENV-001'],
            LOGGER.info,
        )

    assert 'test environment is running. Ready to stop it.' in caplog.text
    assert 'Environment is not stopped: wait 1s more, elapsed 0s' in caplog.text
    assert env == {'id': 'ENV-001', 'status': 'stopped'}


def test_stop_environment_timeout(caplog, responses):
    responses.add(
        'POST',
        'https://localhost/public/v1/devops/services/SRV-001/environments/ENV-001/stop',
        json={},
        status=201,
    )
    responses.add(
        'GET',
        'https://localhost/public/v1/devops/services/SRV-001/environments/ENV-001',
        json={'id': 'ENV-001', 'status': 'running'},
        status=200,
    )

    with caplog.at_level(logging.DEBUG):
        env = stop_environment(
            {
                'id': 'ENV-001',
                'status': 'running',
                'type': 'test',
            },
            CLIENT('devops').services['SRV-001'].environments['ENV-001'],
            LOGGER.info,
        )

    assert 'test environment is running. Ready to stop it.' in caplog.text
    assert 'Environment is not stopped: wait 1s more, elapsed 0s' in caplog.text
    assert 'Environment is not stopped: wait 1s more, elapsed 1s' in caplog.text
    assert 'Environment is not stopped: wait 1s more, elapsed 2s' in caplog.text
    assert 'Environment is not stopped: wait 1s more, elapsed 3s' in caplog.text
    assert 'Environment is not stopped: wait 1s more, elapsed 4s' in caplog.text
    assert 'Environment hasn\'t stopped in maximum wait time' in caplog.text
    assert env == {'id': 'ENV-001', 'status': 'running'}


def test_stop_environment_error(caplog, responses):
    responses.add(
        'POST',
        'https://localhost/public/v1/devops/services/SRV-001/environments/ENV-001/stop',
        json={},
        status=400,
    )

    with caplog.at_level(logging.DEBUG):
        env = stop_environment(
            {
                'id': 'ENV-001',
                'status': 'running',
                'type': 'test',
            },
            CLIENT('devops').services['SRV-001'].environments['ENV-001'],
            LOGGER.info,
        )

    assert 'Error stopping test environment:' in caplog.text
    assert env == {'id': 'ENV-001', 'status': 'running', 'type': 'test'}
