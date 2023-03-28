import pytest
import responses as sentry_responses
from fastapi import Depends
from fastapi.routing import APIRouter

from connect.client import AsyncConnectClient, ClientError, ConnectClient
from connect.eaas.core.decorators import web_app
from connect.eaas.core.extension import WebApplicationBase
from connect.eaas.core.inject import asynchronous, common, synchronous
from connect.eaas.core.inject.models import Context
from connect.eaas.core.testing.fixtures import test_client_factory  # noqa


@pytest.fixture
def responses():
    with sentry_responses.RequestsMock() as rsps:
        yield rsps


@pytest.fixture
def webapp_mock(mocker):

    router = APIRouter()
    mocker.patch('connect.eaas.core.extension.router', router)

    @web_app(router)
    class MyWebApplication(WebApplicationBase):

        @router.get('/sync/installation')
        def sync_installation(
            self, installation: dict = Depends(synchronous.get_installation),
        ) -> dict:
            return installation

        @router.get('/async/installation')
        async def async_installation(
            self, installation: dict = Depends(asynchronous.get_installation),
        ) -> dict:
            return installation

        @router.get('/sync/installation_and_call')
        def sync_installation_and_call(
            self,
            installation: dict = Depends(synchronous.get_installation),
            client: ConnectClient = Depends(synchronous.get_installation_client),
        ) -> dict:
            list(client.products.all())
            return installation

        @router.get('/async/installation_and_call')
        async def async_installation_and_call(
            self,
            installation: dict = Depends(asynchronous.get_installation),
            client: AsyncConnectClient = Depends(asynchronous.get_installation_client),
        ) -> dict:
            [item async for item in client.products.all()]
            return installation

        @router.get('/config')
        def config(self, config: dict = Depends(common.get_config)) -> dict:
            return config

        @router.get('/context')
        def context(self, context: Context = Depends(common.get_call_context)):
            return context

        @router.get('/errors/unexpected')
        def client_error_unexpected(self):
            raise ClientError()

        @router.get('/errors/no_json_body')
        def client_error_no_json_body(self):
            raise ClientError(
                status_code=401,
            )

        @router.get('/errors/json_body')
        def client_error_json_body(self):
            raise ClientError(
                status_code=400,
                error_code='ERR-000',
                errors=['this is an error'],
            )

        @router.get('/sync/admin/{installation_id}/doit')
        def sync_installation_admin_client(
            self,
            installation_id: str,
            client: ConnectClient = Depends(synchronous.get_installation_admin_client),
        ):
            return client('devops').installations[installation_id].get()

    return MyWebApplication
