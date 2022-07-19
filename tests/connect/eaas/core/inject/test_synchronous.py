import inspect

from connect.client import ConnectClient
from connect.eaas.core.inject import synchronous


def test_get_installation_client():
    client = synchronous.get_installation_client(
        x_connect_installation_api_key='api_key',
        x_connect_api_gateway_url='http://api_gw_url',
        x_connect_user_agent='My User Agent',
    )
    assert isinstance(client, ConnectClient)
    assert client.api_key == 'api_key'
    assert client.endpoint == 'http://api_gw_url'
    assert 'User-Agent' in client.default_headers
    assert client.default_headers['User-Agent'] == 'My User Agent'


def test_get_extension_client(mocker):
    mocker.patch('connect.eaas.core.inject.synchronous.os.getenv', return_value='api_key')
    client = synchronous.get_extension_client(
        x_connect_api_gateway_url='http://api_gw_url',
        x_connect_user_agent='My User Agent',
    )
    assert isinstance(client, ConnectClient)
    assert client.api_key == 'api_key'
    assert client.endpoint == 'http://api_gw_url'
    assert 'User-Agent' in client.default_headers
    assert client.default_headers['User-Agent'] == 'My User Agent'


def test_get_installation(responses):
    responses.add(
        'GET',
        'https://localhost/public/v1/devops/installations/installation_id',
        json={
            'id': 'EIN-000-000',
        },
        status=200,
    )

    client = ConnectClient(
        'api_key',
        endpoint='https://localhost/public/v1',
        use_specs=False,
    )

    installation = synchronous.get_installation(client, 'installation_id')

    assert installation['id'] == 'EIN-000-000'

    signature = inspect.signature(synchronous.get_installation)
    client_param = signature.parameters['client']
    assert client_param.annotation == ConnectClient
    assert client_param.default.dependency == synchronous.get_installation_client


def test_get_environment(responses):
    variables = [
        {
            'id': 'VAR-001',
            'name': 'MY_VAR',
            'value': 'my val',
        },
    ]
    responses.add(
        'GET',
        (
            'https://localhost/public/v1/devops/services'
            '/extension_id/environments/env_id/variables?limit=100&offset=0'
        ),
        json=variables,
        status=200,
        headers={'Content-Range': 'items 0-9/10'},
    )

    client = ConnectClient(
        'api_key',
        endpoint='https://localhost/public/v1',
        use_specs=False,
    )

    environment = synchronous.get_environment(client, 'extension_id', 'env_id')

    assert environment == variables

    signature = inspect.signature(synchronous.get_environment)
    client_param = signature.parameters['client']
    assert client_param.annotation == ConnectClient
    assert client_param.default.dependency == synchronous.get_extension_client
