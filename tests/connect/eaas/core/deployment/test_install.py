import logging

from connect.client import ConnectClient
from connect.eaas.core.deployment.install import install_extension


CLIENT = ConnectClient(
    'ApiKey XYZ:XYZ',
    endpoint='https://localhost/public/v1',
)
LOGGER = logging.getLogger('test')


def test_install_error_extract_arguments(caplog, mocker):
    mocker.patch(
        'connect.eaas.core.deployment.install.extract_arguments',
        return_value=(None, mocker.MagicMock(message='Some error')),
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
        return_value=({'tag': '1.2'}, None),
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
        return_value=({'package_id': 'pacakge.id'}, None),
    )
    mocker.patch(
        'connect.eaas.core.deployment.install.get_git_data',
        return_value=(None, mocker.MagicMock(message='Git error')),
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
        return_value=({'package_id': 'pacakge.id', 'type': 'wrong_type', 'name': 'Name'}, None),
    )
    mocker.patch(
        'connect.eaas.core.deployment.install.get_git_data',
        return_value=({}, None),
    )
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
        )

    assert 'Error creating extension' in caplog.text
    assert 'Extension successfully installed' not in caplog.text


def test_install_error_processing_environment(caplog, mocker, responses):
    mocker.patch(
        'connect.eaas.core.deployment.install.extract_arguments',
        return_value=({'package_id': 'pacakge.id', 'env': 'test', 'type': 'multiaccount'}, None),
    )
    mocker.patch(
        'connect.eaas.core.deployment.install.get_git_data',
        return_value=({}, None),
    )
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
        return_value=({'package_id': 'pacakge.id', 'env': 'test', 'type': 'multiaccount'}, None),
    )
    mocker.patch(
        'connect.eaas.core.deployment.install.get_git_data',
        return_value=({}, None),
    )
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
        )

    assert 'Extension successfully installed' in caplog.text
