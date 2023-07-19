import logging

from connect.client import ClientError, ConnectClient
from connect.eaas.core.deployment.extension import deploy_extension
from connect.eaas.core.deployment.utils import DeploymentError


CLIENT = ConnectClient(
    'ApiKey XXX:YYY',
    endpoint='https://localhost/public/v1',
)
LOGGER = logging.getLogger('test')


def test_deploy_extension_ok_install(caplog, responses, mocker):
    mocker.patch(
        'connect.eaas.core.deployment.extension.get_git_data',
        return_value={'tag': '1.2', 'commit': 'commit_hash', 'url': 'https://github.com/dummy'},
    )
    mocker.patch(
        'connect.eaas.core.deployment.extension.extract_arguments',
        return_value={
            'package_id': 'p.id',
            'env': 'test',
            'type': 'multiaccount',
            'var': {},
        },
    )
    responses.add(
        'GET',
        'https://localhost/public/v1/devops/services?eq(package_id,p.id)&limit=1&offset=0',
        json=[],
        status=200,
    )
    mocker.patch(
        'connect.eaas.core.deployment.extension.create_extension',
        return_value={
            'id': 'SRV-001',
            'environments': {
                'test': {'id': 'ENV-001', 'status': 'uninitialized', 'runtime': 'local'},
            },
        },
    )
    mocker.patch(
        'connect.eaas.core.deployment.extension.stop_environment',
        return_value={
            'id': 'ENV-001',
            'type': 'test',
            'runtime': 'cloud',
            'status': 'stopped',
        },
    )
    mocker.patch(
        'connect.eaas.core.deployment.extension.process_variables',
        return_value=False,
    )
    responses.add(
        'PUT',
        'https://localhost/public/v1/devops/services/SRV-001/environments/ENV-001',
        json={'status': 'deploying', 'runtime': 'cloud'},
        status=201,
    )

    with caplog.at_level(logging.DEBUG):
        deploy_extension(
            'https://github.com/dummy',
            CLIENT,
            LOGGER.info,
            '1.2',
        )

    assert 'Extension with package_id p.id does not exist, creating it' in caplog.text
    assert 'Extension with package_id p.id successfully deployed' in caplog.text


def test_deploy_extension_ok_update_local(caplog, responses, mocker):
    mocker.patch(
        'connect.eaas.core.deployment.extension.get_git_data',
        return_value={'tag': '1.2', 'commit': 'commit_hash', 'url': 'https://github.com/dummy'},
    )
    mocker.patch(
        'connect.eaas.core.deployment.extension.extract_arguments',
        return_value={
            'package_id': 'p.id',
            'env': 'test',
            'type': 'multiaccount',
            'name': 'Extension',
            'var': {},
        },
    )
    responses.add(
        'GET',
        'https://localhost/public/v1/devops/services?eq(package_id,p.id)&limit=1&offset=0',
        json=[
            {
                'id': 'SRV-001',
                'environments': {
                    'test': {'id': 'ENV-001', 'status': 'stopped', 'runtime': 'local'},
                },
            },
        ],
        status=200,
    )
    mocker.patch(
        'connect.eaas.core.deployment.extension.update_extension',
        return_value={
            'id': 'SRV-001',
            'environments': {
                'test': {'id': 'ENV-001', 'status': 'stopped', 'runtime': 'local'},
            },
        },
    )
    mocker.patch(
        'connect.eaas.core.deployment.extension.stop_environment',
        return_value={
            'id': 'ENV-001',
            'type': 'test',
            'runtime': 'local',
            'status': 'stopped',
        },
    )
    mocker.patch('connect.eaas.core.deployment.extension.process_variables')
    responses.add(
        'PUT',
        'https://localhost/public/v1/devops/services/SRV-001/environments/ENV-001',
        json={'status': 'deploying', 'runtime': 'cloud'},
        status=201,
    )

    with caplog.at_level(logging.DEBUG):
        deploy_extension(
            'https://github.com/dummy',
            CLIENT,
            LOGGER.info,
            '1.2',
        )

    assert 'Extension with package_id p.id does exist, updating it' in caplog.text
    assert 'Extension with package_id p.id successfully deployed' in caplog.text


def test_deploy_extension_ok_update_cloud(caplog, responses, mocker):
    mocker.patch(
        'connect.eaas.core.deployment.extension.get_git_data',
        return_value={'tag': '1.2', 'commit': 'commit_hash', 'url': 'https://github.com/dummy'},
    )
    mocker.patch(
        'connect.eaas.core.deployment.extension.extract_arguments',
        return_value={
            'package_id': 'p.id',
            'env': 'test',
            'type': 'multiaccount',
            'name': 'Extension',
            'var': {},
        },
    )
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
    mocker.patch(
        'connect.eaas.core.deployment.extension.update_extension',
        return_value={
            'id': 'SRV-001',
            'environments': {
                'test': {'id': 'ENV-001', 'status': 'running', 'runtime': 'cloud'},
            },
        },
    )
    mocker.patch(
        'connect.eaas.core.deployment.extension.stop_environment',
        return_value={
            'id': 'ENV-001',
            'type': 'test',
            'runtime': 'cloud',
            'status': 'stopped',
        },
    )
    mocker.patch('connect.eaas.core.deployment.extension.process_variables')
    responses.add(
        'PUT',
        'https://localhost/public/v1/devops/services/SRV-001/environments/ENV-001',
        json={'status': 'stopped', 'runtime': 'cloud', 'type': 'test'},
        status=201,
    )
    responses.add(
        'POST',
        'https://localhost/public/v1/devops/services/SRV-001/environments/ENV-001/start',
        json={'status': 'deploying', 'runtime': 'cloud'},
        status=201,
    )

    with caplog.at_level(logging.DEBUG):
        deploy_extension(
            'https://github.com/dummy',
            CLIENT,
            LOGGER.info,
            '1.2',
        )

    assert 'Extension with package_id p.id does exist, updating it' in caplog.text
    assert 'Extension with package_id p.id successfully deployed' in caplog.text


def test_deploy_extension_ok_update_only_config(caplog, responses, mocker):
    mocker.patch(
        'connect.eaas.core.deployment.extension.get_git_data',
        return_value={'tag': '1.2', 'commit': 'commit_hash', 'url': 'https://github.com/dummy'},
    )
    mocker.patch(
        'connect.eaas.core.deployment.extension.extract_arguments',
        return_value={
            'package_id': 'p.id',
            'env': 'test',
            'type': 'multiaccount',
            'name': 'Extension',
            'var': {},
        },
    )
    responses.add(
        'GET',
        'https://localhost/public/v1/devops/services?eq(package_id,p.id)&limit=1&offset=0',
        json=[
            {
                'id': 'SRV-001',
                'environments': {
                    'test': {
                        'id': 'ENV-001',
                        'status': 'running',
                        'runtime': 'cloud',
                        'git': {'commit': 'commit_hash'},
                    },
                },
            },
        ],
        status=200,
    )
    mocker.patch(
        'connect.eaas.core.deployment.extension.update_extension',
        return_value={
            'id': 'SRV-001',
            'environments': {
                'test': {
                    'id': 'ENV-001',
                    'status': 'running',
                    'runtime': 'cloud',
                    'git': {'commit': 'commit_hash'},
                    'type': 'test',
                },
            },
        },
    )
    mocker.patch(
        'connect.eaas.core.deployment.extension.process_variables',
        return_value=True,
    )
    responses.add(
        'POST',
        'https://localhost/public/v1/devops/services/SRV-001/environments/ENV-001/update-config',
        json={},
        status=200,
    )

    with caplog.at_level(logging.DEBUG):
        deploy_extension(
            'https://github.com/dummy',
            CLIENT,
            LOGGER.info,
            '1.2',
        )

    assert 'Updating test environment config.' in caplog.text
    assert 'Extension with package_id p.id successfully deployed' in caplog.text


def test_deploy_extension_extracting_error(caplog, responses, mocker):
    mocker.patch(
        'connect.eaas.core.deployment.extension.get_git_data',
        side_effect=DeploymentError('Error retrieving git date'),
    )

    with caplog.at_level(logging.DEBUG):
        deploy_extension(
            'https://github.com/dummy',
            CLIENT,
            LOGGER.info,
            '1.2',
        )

    assert 'Error retrieving git date' in caplog.text
    assert 'Extension with package_id p.id successfully deployed' not in caplog.text


def test_deploy_extension_no_package_id(caplog, responses, mocker):
    mocker.patch(
        'connect.eaas.core.deployment.extension.get_git_data',
        return_value={'tag': '1.2', 'commit': 'commit_hash', 'url': 'https://github.com/dummy'},
    )
    mocker.patch(
        'connect.eaas.core.deployment.extension.extract_arguments',
        return_value={},
    )

    with caplog.at_level(logging.DEBUG):
        deploy_extension(
            'https://github.com/dummy',
            CLIENT,
            LOGGER.info,
            '1.2',
        )

    assert 'No required package_id found' in caplog.text
    assert 'Extension with package_id p.id successfully deployed' not in caplog.text


def test_deploy_extension_filtering_error(caplog, responses, mocker):
    mocker.patch(
        'connect.eaas.core.deployment.extension.get_git_data',
        return_value={'tag': '1.2', 'commit': 'commit_hash', 'url': 'https://github.com/dummy'},
    )
    mocker.patch(
        'connect.eaas.core.deployment.extension.extract_arguments',
        return_value={
            'package_id': 'p.id',
            'env': 'test',
            'type': 'multiaccount',
            'name': 'Extension',
            'var': {},
        },
    )
    responses.add(
        'GET',
        'https://localhost/public/v1/devops/services?eq(package_id,p.id)&limit=1&offset=0',
        json={},
        status=400,
    )

    with caplog.at_level(logging.DEBUG):
        deploy_extension(
            'https://github.com/dummy',
            CLIENT,
            LOGGER.info,
            '1.2',
        )

    assert 'Error getting extension: 400 Bad Request' in caplog.text
    assert 'Extension with package_id p.id successfully deployed' not in caplog.text


def test_deploy_extension_error_processing_env(caplog, responses, mocker):
    mocker.patch(
        'connect.eaas.core.deployment.extension.get_git_data',
        return_value={'tag': '1.2', 'commit': 'commit_hash', 'url': 'https://github.com/dummy'},
    )
    mocker.patch(
        'connect.eaas.core.deployment.extension.extract_arguments',
        return_value={
            'package_id': 'p.id',
            'env': 'test',
            'type': 'multiaccount',
            'name': 'Extension',
            'var': {},
        },
    )
    responses.add(
        'GET',
        'https://localhost/public/v1/devops/services?eq(package_id,p.id)&limit=1&offset=0',
        json=[],
        status=200,
    )
    mocker.patch(
        'connect.eaas.core.deployment.extension.create_extension',
        return_value={
            'id': 'SRV-001',
            'environments': {
                'test': {'id': 'ENV-001', 'status': 'running', 'runtime': 'cloud'},
            },
        },
    )
    mocker.patch(
        'connect.eaas.core.deployment.extension.stop_environment',
        return_value={
            'id': 'ENV-001',
            'type': 'test',
            'runtime': 'cloud',
            'status': 'stopped',
        },
    )
    mocker.patch(
        'connect.eaas.core.deployment.extension.process_variables',
        side_effect=ClientError('Ooops'),
    )

    with caplog.at_level(logging.DEBUG):
        deploy_extension(
            'https://github.com/dummy',
            CLIENT,
            LOGGER.info,
            '1.2',
        )

    assert 'Error processing environment: Ooops' in caplog.text
    assert 'Extension with package_id p.id successfully deployed' not in caplog.text


def test_deploy_extension_env_not_stopped(caplog, responses, mocker):
    mocker.patch(
        'connect.eaas.core.deployment.extension.get_git_data',
        return_value={'tag': '1.2', 'commit': 'commit_hash', 'url': 'https://github.com/dummy'},
    )
    mocker.patch(
        'connect.eaas.core.deployment.extension.extract_arguments',
        return_value={
            'package_id': 'p.id',
            'env': 'test',
            'type': 'multiaccount',
            'name': 'Extension',
            'var': {},
        },
    )
    responses.add(
        'GET',
        'https://localhost/public/v1/devops/services?eq(package_id,p.id)&limit=1&offset=0',
        json=[],
        status=200,
    )
    mocker.patch(
        'connect.eaas.core.deployment.extension.create_extension',
        return_value={
            'id': 'SRV-001',
            'environments': {
                'test': {'id': 'ENV-001', 'status': 'running', 'runtime': 'cloud'},
            },
        },
    )
    mocker.patch(
        'connect.eaas.core.deployment.extension.stop_environment',
        return_value={
            'id': 'ENV-001',
            'type': 'test',
            'runtime': 'cloud',
            'status': 'running',
        },
    )

    with caplog.at_level(logging.DEBUG):
        deploy_extension(
            'https://github.com/dummy',
            CLIENT,
            LOGGER.info,
            '1.2',
        )

    assert 'Extension with package_id p.id successfully deployed' not in caplog.text


def test_deploy_extension_error_creating(caplog, responses, mocker):
    mocker.patch(
        'connect.eaas.core.deployment.extension.get_git_data',
        return_value={'tag': '1.2', 'commit': 'commit_hash', 'url': 'https://github.com/dummy'},
    )
    mocker.patch(
        'connect.eaas.core.deployment.extension.extract_arguments',
        return_value={
            'package_id': 'p.id',
            'env': 'test',
            'type': 'multiaccount',
            'name': 'Extension',
            'var': {},
        },
    )
    responses.add(
        'GET',
        'https://localhost/public/v1/devops/services?eq(package_id,p.id)&limit=1&offset=0',
        json=[],
        status=200,
    )
    mocker.patch(
        'connect.eaas.core.deployment.extension.create_extension',
        return_value=None,
    )

    with caplog.at_level(logging.DEBUG):
        deploy_extension(
            'https://github.com/dummy',
            CLIENT,
            LOGGER.info,
            '1.2',
        )

    assert 'Extension with package_id p.id successfully deployed' not in caplog.text


def test_deploy_extension_update_local_connected(caplog, responses, mocker):
    mocker.patch(
        'connect.eaas.core.deployment.extension.get_git_data',
        return_value={'tag': '1.2', 'commit': 'commit_hash', 'url': 'https://github.com/dummy'},
    )
    mocker.patch(
        'connect.eaas.core.deployment.extension.extract_arguments',
        return_value={
            'package_id': 'p.id',
            'env': 'test',
            'type': 'multiaccount',
            'name': 'Extension',
            'var': {},
        },
    )
    responses.add(
        'GET',
        'https://localhost/public/v1/devops/services?eq(package_id,p.id)&limit=1&offset=0',
        json=[
            {
                'id': 'SRV-001',
                'environments': {
                    'test': {'id': 'ENV-001', 'status': 'connected', 'runtime': 'local'},
                },
            },
        ],
        status=200,
    )
    mocker.patch(
        'connect.eaas.core.deployment.extension.update_extension',
        return_value={
            'id': 'SRV-001',
            'environments': {
                'test': {
                    'id': 'ENV-001', 'status': 'connected', 'runtime': 'local', 'type': 'test',
                },
            },
        },
    )

    with caplog.at_level(logging.DEBUG):
        deploy_extension(
            'https://github.com/dummy',
            CLIENT,
            LOGGER.info,
            '1.2',
        )

    assert 'test environment is in local mode and connected' in caplog.text


def test_deploy_extension_update_hasnt_stopped(caplog, responses, mocker):
    mocker.patch(
        'connect.eaas.core.deployment.extension.get_git_data',
        return_value={'tag': '1.2', 'commit': 'commit_hash', 'url': 'https://github.com/dummy'},
    )
    mocker.patch(
        'connect.eaas.core.deployment.extension.extract_arguments',
        return_value={
            'package_id': 'p.id',
            'env': 'test',
            'type': 'multiaccount',
            'name': 'Extension',
            'var': {},
        },
    )
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
    mocker.patch(
        'connect.eaas.core.deployment.extension.update_extension',
        return_value={
            'id': 'SRV-001',
            'environments': {
                'test': {'id': 'ENV-001', 'status': 'running', 'runtime': 'cloud'},
            },
        },
    )
    mocker.patch(
        'connect.eaas.core.deployment.extension.stop_environment',
        return_value={
            'id': 'ENV-001',
            'type': 'test',
            'runtime': 'cloud',
            'status': 'stopping',
        },
    )
    mocker.patch('connect.eaas.core.deployment.extension.process_variables')

    with caplog.at_level(logging.DEBUG):
        deploy_extension(
            'https://github.com/dummy',
            CLIENT,
            LOGGER.info,
            '1.2',
        )

    assert 'Extension with package_id p.id successfully deployed' not in caplog.text
