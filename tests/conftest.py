import pytest
import responses as sentry_responses
from fastapi import Depends
from fastapi.routing import APIRouter

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

        @router.get('/config')
        def config(self, config: dict = Depends(common.get_config)) -> dict:
            return config

        @router.get('/context')
        def context(self, context: Context = Depends(common.get_call_context)):
            return context

    return MyWebApplication
