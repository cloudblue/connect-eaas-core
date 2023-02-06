import inspect

import pytest
from connect.client import AsyncConnectClient

from connect.eaas.core.inject import asynchronous
from connect.eaas.core.inject.models import Context


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
        url='https://localhost/devops/installations/installation_id',
        json={
            'id': 'EIN-000-000',
        },
    )

    client = AsyncConnectClient(
        'api_key',
        endpoint='https://localhost',
        use_specs=False,
    )

    installation = await asynchronous.get_installation(client, 'installation_id')

    assert installation['id'] == 'EIN-000-000'

    signature = inspect.signature(asynchronous.get_installation)
    client_param = signature.parameters['client']
    assert client_param.annotation == AsyncConnectClient
    assert client_param.default.dependency == asynchronous.get_installation_client


@pytest.mark.asyncio
async def test_get_installation_admin_client(mocker, async_client_mocker_factory):
    client_mocker = async_client_mocker_factory(base_url='https://localhost/public/v1')

    ctx = Context(extension_id='SRVC-0000')
    client_mocker('devops').services[ctx.extension_id].installations[
        'EIN-123'
    ].action('impersonate').post(
        return_value={'installation_api_key': 'my_inst_api_key'},
    )

    extension_client = AsyncConnectClient(
        'api_key',
        endpoint='https://localhost/public/v1',
        default_headers={'A': 'B'},
        logger=mocker.MagicMock(),
        use_specs=False,
    )

    installation_admin_client = await asynchronous.get_installation_admin_client(
        'EIN-123',
        ctx,
        extension_client,
    )

    assert isinstance(installation_admin_client, AsyncConnectClient)
    assert installation_admin_client.api_key == 'my_inst_api_key'
    assert installation_admin_client.endpoint == extension_client.endpoint
    assert installation_admin_client.default_headers == extension_client.default_headers
    assert installation_admin_client.logger == extension_client.logger
