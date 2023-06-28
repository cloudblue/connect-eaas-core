import logging

from connect.client import ConnectClient
from connect.eaas.core.deployment.install import install_extension
from connect.eaas.core.deployment.utils import DeploymentError


CLIENT = ConnectClient(
    'ApiKey XYZ:XYZ',
    endpoint='https://localhost/public/v1',
)
LOGGER = logging.getLogger('test')


def test_install_error_extract_arguments(caplog, mocker):
    mocker.patch(
        'connect.eaas.core.deployment.install.extract_arguments',
        side_effect=DeploymentError('Some error'),
    )
    with caplog.at_level(logging.DEBUG):
        install_extension(
            'https://github.com/dummy/repo.git',
            CLIENT,
            LOGGER.info,
        )

    assert 'Some error' in caplog.text
    assert 'Extension successfully installed' not in caplog.text


def test_install_no_package_id(caplog, mocker):
    mocker.patch(
        'connect.eaas.core.deployment.install.extract_arguments',
        return_value={'tag': '1.2'},
    )
    with caplog.at_level(logging.DEBUG):
        install_extension(
            'https://github.com/dummy/repo.git',
            CLIENT,
            LOGGER.info,
        )

    assert 'No required package_id found in .connect_deployment.yaml file.' in caplog.text
    assert 'Extension successfully installed' not in caplog.text


def test_install_error_get_git_data(caplog, mocker):
    mocker.patch(
        'connect.eaas.core.deployment.install.extract_arguments',
        return_value={'package_id': 'pacakge.id'},
    )
    mocker.patch(
        'connect.eaas.core.deployment.install.get_git_data',
        side_effect=DeploymentError('Git error'),
    )
    with caplog.at_level(logging.DEBUG):
        install_extension(
            'https://github.com/dummy/repo.git',
            CLIENT,
            LOGGER.info,
        )

    assert 'Git error' in caplog.text
    assert 'Extension successfully installed' not in caplog.text


def test_install_error_creating_extension(caplog, mocker, responses):
    mocker.patch(
        'connect.eaas.core.deployment.install.extract_arguments',
        return_value={'package_id': 'pacakge.id', 'type': 'wrong_type', 'name': 'Name'},
    )
    mocker.patch('connect.eaas.core.deployment.install.get_git_data', return_value={})
    responses.add(
        'POST',
        'https://localhost/public/v1/devops/services',
        json={},
        status=400,
    )

    with caplog.at_level(logging.DEBUG):
        install_extension(
            'https://github.com/dummy/repo.git',
            CLIENT,
            LOGGER.info,
            '1.2',
        )

    assert 'Error creating extension' in caplog.text
    assert 'Extension successfully installed' not in caplog.text


def test_install_error_processing_environment(caplog, mocker, responses):
    mocker.patch(
        'connect.eaas.core.deployment.install.extract_arguments',
        return_value={'package_id': 'pacakge.id', 'env': 'test', 'type': 'multiaccount'},
    )
    mocker.patch('connect.eaas.core.deployment.install.get_git_data', return_value={})
    responses.add(
        'POST',
        'https://localhost/public/v1/devops/services',
        json={
            'id': 'SRV-001',
            'environments': {'test': {'id': 'ENV-001'}},
        },
        status=201,
    )
    mocker.patch('connect.eaas.core.deployment.install.process_variables')
    responses.add(
        'PUT',
        'https://localhost/public/v1/devops/services/SRV-001/environments/ENV-001',
        json={},
        status=400,
    )

    with caplog.at_level(logging.DEBUG):
        install_extension(
            'https://github.com/dummy/repo.git',
            CLIENT,
            LOGGER.info,
        )

    assert 'Error processing environment' in caplog.text
    assert 'Extension successfully installed' not in caplog.text


def test_install_ok(caplog, mocker, responses):
    mocker.patch(
        'connect.eaas.core.deployment.install.extract_arguments',
        return_value={'package_id': 'pacakge.id', 'env': 'test', 'type': 'multiaccount'},
    )
    mocker.patch('connect.eaas.core.deployment.install.get_git_data', return_value={})
    responses.add(
        'POST',
        'https://localhost/public/v1/devops/services',
        json={
            'id': 'SRV-001',
            'environments': {'test': {'id': 'ENV-001'}},
        },
        status=201,
    )
    mocker.patch('connect.eaas.core.deployment.install.process_variables')
    responses.add(
        'PUT',
        'https://localhost/public/v1/devops/services/SRV-001/environments/ENV-001',
        json={},
        status=200,
    )

    with caplog.at_level(logging.DEBUG):
        install_extension(
            'https://github.com/dummy/repo.git',
            CLIENT,
            LOGGER.info,
            '1.2',
        )

    assert 'Extension successfully installed' in caplog.text


def test_install_ok_with_category(caplog, mocker, responses):
    mocker.patch(
        'connect.eaas.core.deployment.install.extract_arguments',
        return_value={
            'package_id': 'pacakge.id',
            'env': 'test',
            'type': 'multiaccount',
            'overview': 'Overview of extension',
            'category': 'Integration',
        },
    )
    mocker.patch('connect.eaas.core.deployment.install.get_git_data', return_value={})
    responses.add(
        'POST',
        'https://localhost/public/v1/devops/services',
        json={
            'id': 'SRV-001',
            'environments': {'test': {'id': 'ENV-001'}},
        },
        status=201,
    )
    responses.add(
        'GET',
        (
            'https://localhost/public/v1/dictionary/extensions/categories?'
            'eq(name,Integration)&limit=1&offset=0'
        ),
        json=[{'id': 'CA-001', 'name': 'Industry'}],
        status=200,
    )
    mocker.patch('connect.eaas.core.deployment.install.process_variables')
    responses.add(
        'PUT',
        'https://localhost/public/v1/devops/services/SRV-001/environments/ENV-001',
        json={},
        status=200,
    )

    with caplog.at_level(logging.DEBUG):
        install_extension(
            'https://github.com/dummy/repo.git',
            CLIENT,
            LOGGER.info,
        )

    assert 'Extension successfully installed' in caplog.text


def test_install_ok_with_category_filter_error(caplog, mocker, responses):
    mocker.patch(
        'connect.eaas.core.deployment.install.extract_arguments',
        return_value={
            'package_id': 'pacakge.id',
            'env': 'test',
            'type': 'multiaccount',
            'overview': 'Overview of extension',
            'category': 'Integration',
        },
    )
    mocker.patch('connect.eaas.core.deployment.install.get_git_data', return_value={})
    responses.add(
        'POST',
        'https://localhost/public/v1/devops/services',
        json={
            'id': 'SRV-001',
            'environments': {'test': {'id': 'ENV-001'}},
        },
        status=201,
    )
    responses.add(
        'GET',
        (
            'https://localhost/public/v1/dictionary/extensions/categories?'
            'eq(name,Integration)&limit=1&offset=0'
        ),
        json={},
        status=400,
    )
    mocker.patch('connect.eaas.core.deployment.install.process_variables')
    responses.add(
        'PUT',
        'https://localhost/public/v1/devops/services/SRV-001/environments/ENV-001',
        json={},
        status=200,
    )

    with caplog.at_level(logging.DEBUG):
        install_extension(
            'https://github.com/dummy/repo.git',
            CLIENT,
            LOGGER.info,
        )

    assert 'Extension successfully installed' in caplog.text
    assert 'Error during looking up category' in caplog.text


def test_install_ok_with_category_empty_filter(caplog, mocker, responses):
    mocker.patch(
        'connect.eaas.core.deployment.install.extract_arguments',
        return_value={
            'package_id': 'pacakge.id',
            'env': 'test',
            'type': 'multiaccount',
            'overview': 'Overview of extension',
            'category': 'Integration',
        },
    )
    mocker.patch('connect.eaas.core.deployment.install.get_git_data', return_value={})
    responses.add(
        'POST',
        'https://localhost/public/v1/devops/services',
        json={
            'id': 'SRV-001',
            'environments': {'test': {'id': 'ENV-001'}},
        },
        status=201,
    )
    responses.add(
        'GET',
        (
            'https://localhost/public/v1/dictionary/extensions/categories'
            '?eq(name,Integration)&limit=1&offset=0'
        ),
        json=[],
        status=200,
    )
    mocker.patch('connect.eaas.core.deployment.install.process_variables')
    responses.add(
        'PUT',
        'https://localhost/public/v1/devops/services/SRV-001/environments/ENV-001',
        json={},
        status=200,
    )

    with caplog.at_level(logging.DEBUG):
        install_extension(
            'https://github.com/dummy/repo.git',
            CLIENT,
            LOGGER.info,
        )

    assert 'Extension successfully installed' in caplog.text
