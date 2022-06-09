import inspect

import pytest

from connect.client import AsyncConnectClient
from connect.eaas.core.inject import asynchronous


def test_get_installation_client():
    client = asynchronous.get_installation_client(
        x_connect_installation_api_key='api_key',
        x_connect_api_gateway_url='http://api_gw_url',
        x_connect_user_agent='My User Agent',
    )
    assert isinstance(client, AsyncConnectClient)
    assert client.api_key == 'api_key'
    assert client.endpoint == 'http://api_gw_url'
    assert 'User-Agent' in client.default_headers
    assert client.default_headers['User-Agent'] == 'My User Agent'


def test_get_extension_client(mocker):
    mocker.patch('connect.eaas.core.inject.synchronous.os.getenv', return_value='api_key')
    client = asynchronous.get_extension_client(
        x_connect_api_gateway_url='http://api_gw_url',
        x_connect_user_agent='My User Agent',
    )
    assert isinstance(client, AsyncConnectClient)
    assert client.api_key == 'api_key'
    assert client.endpoint == 'http://api_gw_url'
    assert 'User-Agent' in client.default_headers
    assert client.default_headers['User-Agent'] == 'My User Agent'


@pytest.mark.asyncio
async def test_get_installation(httpx_mock):
    httpx_mock.add_response(
        method='GET',
        url='https://localhost/devops/services/extension_id/installations/installation_id',
        json={
            'id': 'EIN-000-000',
        },
    )

    client = AsyncConnectClient(
        'api_key',
        endpoint='https://localhost',
        use_specs=False,
    )

    installation = await asynchronous.get_installation(client, 'extension_id', 'installation_id')

    assert installation['id'] == 'EIN-000-000'

    signature = inspect.signature(asynchronous.get_installation)
    client_param = signature.parameters['client']
    assert client_param.annotation == AsyncConnectClient
    assert client_param.default.dependency == asynchronous.get_installation_client


@pytest.mark.asyncio
async def test_get_environment(httpx_mock):
    variables = [
        {
            'id': 'VAR-001',
            'name': 'MY_VAR',
            'value': 'my val',
        },
    ]
    httpx_mock.add_response(
        method='GET',
        url=(
            'https://localhost/devops/services'
            '/extension_id/environments/env_id/variables?limit=100&offset=0'
        ),
        json=variables,
        headers={'Content-Range': 'items 0-9/10'},
    )

    client = AsyncConnectClient(
        'api_key',
        endpoint='https://localhost',
        use_specs=False,
    )

    environment = await asynchronous.get_environment(client, 'extension_id', 'env_id')

    assert environment == variables

    signature = inspect.signature(asynchronous.get_environment)
    client_param = signature.parameters['client']
    assert client_param.annotation == AsyncConnectClient
    assert client_param.default.dependency == asynchronous.get_extension_client
