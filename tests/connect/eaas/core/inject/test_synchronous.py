import inspect

from connect.client import ConnectClient
from connect.eaas.core.inject import synchronous


def test_get_installation_client():
    client = synchronous.get_installation_client(
        x_connect_installation_api_key='api_key',
        x_connect_api_gateway_url='http://api_gw_url',
        x_connect_user_agent='My User Agent',
        x_connect_correlation_id='connect-correlation-id-of-task-for-installation-client',
    )
    assert isinstance(client, ConnectClient)
    assert client.api_key == 'api_key'
    assert client.endpoint == 'http://api_gw_url'
    assert 'User-Agent' in client.default_headers
    assert client.default_headers['User-Agent'] == 'My User Agent'
    assert 'ext-traceparent' in client.default_headers
    assert 'nect-correlation-id-of-task-for' in client.default_headers['ext-traceparent']


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
