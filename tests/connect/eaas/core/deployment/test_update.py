import logging

from connect.client import ConnectClient
from connect.eaas.core.deployment.update import update_extension
from connect.eaas.core.deployment.utils import DeploymentError


CLIENT = ConnectClient(
    'ApiKey XXX:YYY',
    endpoint='https://localhost/public/v1',
)
LOGGER = logging.getLogger('test')


def test_update_error_extract_arguments(caplog, mocker):
    mocker.patch(
        'connect.eaas.core.deployment.update.extract_arguments',
        side_effect=DeploymentError('Some error'),
    )
    with caplog.at_level(logging.DEBUG):
        update_extension(
            'https://github.com/dummy/repo.git',
            CLIENT,
            LOGGER.info,
        )

    assert 'Some error' in caplog.text
    assert 'Extension successfully updated' not in caplog.text


def test_update_no_package_id(caplog, mocker):
    mocker.patch(
        'connect.eaas.core.deployment.update.extract_arguments',
        return_value={'tag': '1.2'},
    )
    with caplog.at_level(logging.DEBUG):
        update_extension(
            'https://github.com/dummy/repo.git',
            CLIENT,
            LOGGER.info,
        )

    assert 'No required package_id found in .connect_deployment.yaml file.' in caplog.text
    assert 'Extension successfully updated' not in caplog.text


def test_update_error_get_git_data(caplog, mocker):
    mocker.patch(
        'connect.eaas.core.deployment.update.extract_arguments',
        return_value={'package_id': 'pacakge.id'},
    )
    mocker.patch(
        'connect.eaas.core.deployment.update.get_git_data',
        side_effect=DeploymentError('Git error'),
    )
    with caplog.at_level(logging.DEBUG):
        update_extension(
            'https://github.com/dummy/repo.git',
            CLIENT,
            LOGGER.info,
        )

    assert 'Git error' in caplog.text
    assert 'Extension successfully updated' not in caplog.text


def test_update_error_filtering_extension(caplog, mocker, responses):
    mocker.patch(
        'connect.eaas.core.deployment.update.extract_arguments',
        return_value={'package_id': 'pacakge.id', 'type': 'wrong_type', 'name': 'Name'},
    )
    mocker.patch('connect.eaas.core.deployment.update.get_git_data', return_value={})
    responses.add(
        'GET',
        'https://localhost/public/v1/devops/services?eq(package_id,p.id)&limit=1&offset=0',
        json=[],
        status=400,
    )

    with caplog.at_level(logging.DEBUG):
        update_extension(
            'https://github.com/dummy/repo.git',
            CLIENT,
            LOGGER.info,
        )

    assert 'Error getting extension' in caplog.text
    assert 'Extension successfully updated' not in caplog.text


def test_update_error_no_extension(caplog, mocker, responses):
    mocker.patch(
        'connect.eaas.core.deployment.update.extract_arguments',
        return_value={'package_id': 'pacakge.id', 'type': 'wrong_type', 'name': 'Name'},
    )
    mocker.patch('connect.eaas.core.deployment.update.get_git_data', return_value={})
    responses.add(
        'GET',
        'https://localhost/public/v1/devops/services?eq(package_id,p.id)&limit=1&offset=0',
        json=[],
        status=200,
    )

    with caplog.at_level(logging.DEBUG):
        update_extension(
            'https://github.com/dummy/repo.git',
            CLIENT,
            LOGGER.info,
        )

    assert 'Extension with package_id pacakge.id doesn\'t exist.' in caplog.text
    assert 'Extension successfully updated' not in caplog.text


def test_update_error_processing_environment(caplog, mocker, responses):
    mocker.patch(
        'connect.eaas.core.deployment.update.extract_arguments',
        return_value={'package_id': 'p.id', 'env': 'test', 'type': 'multiaccount'},
    )
    mocker.patch('connect.eaas.core.deployment.update.get_git_data', return_value={})
    responses.add(
        'GET',
        'https://localhost/public/v1/devops/services?eq(package_id,p.id)&limit=1&offset=0',
        json=[
            {
                'id': 'SRV-001',
                'environments': {
                    'test': {'id': 'ENV-001', 'status': 'stopped'},
                },
            },
        ],
        status=200,
    )
    mocker.patch('connect.eaas.core.deployment.update.process_variables')
    responses.add(
        'PUT',
        'https://localhost/public/v1/devops/services/SRV-001/environments/ENV-001',
        json={},
        status=400,
    )

    with caplog.at_level(logging.DEBUG):
        update_extension(
            'https://github.com/dummy/repo.git',
            CLIENT,
            LOGGER.info,
        )

    assert 'Error processing environment' in caplog.text
    assert 'Extension successfully updated' not in caplog.text


def test_update_unable_to_stop(caplog, mocker, responses):
    mocker.patch(
        'connect.eaas.core.deployment.update.extract_arguments',
        return_value={'package_id': 'p.id', 'env': 'test', 'type': 'multiaccount'},
    )
    mocker.patch('connect.eaas.core.deployment.update.get_git_data', return_value={})
    responses.add(
        'GET',
        'https://localhost/public/v1/devops/services?eq(package_id,p.id)&limit=1&offset=0',
        json=[
            {
                'id': 'SRV-001',
                'environments': {
                    'test': {'id': 'ENV-001', 'status': 'running', 'runtime': 'cloud'},
                },
            },
        ],
        status=200,
    )
    responses.add(
        'POST',
        'https://localhost/public/v1/devops/services/SRV-001/environments/ENV-001/stop',
        json={},
        status=201,
    )
    responses.add(
        'GET',
        'https://localhost/public/v1/devops/services/SRV-001/environments/ENV-001',
        json={'id': 'ENV-001', 'status': 'stopping'},
        status=200,
    )

    with caplog.at_level(logging.DEBUG):
        update_extension(
            'https://github.com/dummy/repo.git',
            CLIENT,
            LOGGER.info,
        )

    assert 'Environment hasn\'t stopped in maximum wait time' in caplog.text
    assert 'Extension successfully updated' not in caplog.text


def test_update_ok(caplog, mocker, responses):
    mocker.patch(
        'connect.eaas.core.deployment.update.extract_arguments',
        return_value={'package_id': 'p.id', 'env': 'test', 'type': 'multiaccount'},
    )
    mocker.patch('connect.eaas.core.deployment.update.get_git_data', return_value={})
    responses.add(
        'GET',
        'https://localhost/public/v1/devops/services?eq(package_id,p.id)&limit=1&offset=0',
        json=[
            {
                'id': 'SRV-001',
                'environments': {
                    'test': {'id': 'ENV-001', 'status': 'running', 'runtime': 'cloud'},
                },
            },
        ],
        status=200,
    )
    responses.add(
        'POST',
        'https://localhost/public/v1/devops/services/SRV-001/environments/ENV-001/stop',
        json={},
        status=201,
    )
    responses.add(
        'GET',
        'https://localhost/public/v1/devops/services/SRV-001/environments/ENV-001',
        json={'id': 'ENV-001', 'status': 'stopped'},
        status=200,
    )
    mocker.patch('connect.eaas.core.deployment.update.process_variables')
    responses.add(
        'PUT',
        'https://localhost/public/v1/devops/services/SRV-001/environments/ENV-001',
        json={},
        status=201,
    )
    responses.add(
        'POST',
        'https://localhost/public/v1/devops/services/SRV-001/environments/ENV-001/start',
        json={},
        status=201,
    )

    with caplog.at_level(logging.DEBUG):
        update_extension(
            'https://github.com/dummy/repo.git',
            CLIENT,
            LOGGER.info,
        )

    assert 'Extension successfully updated' in caplog.text
