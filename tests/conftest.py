import inspect
import os

import pytest
import responses as sentry_responses
from fastapi import Depends, Request
from fastapi.routing import APIRouter

from connect.client import ConnectClient
from connect.eaas.core.decorators import guest, web_app
from connect.eaas.core.extension import WebApplicationBase
from connect.eaas.core.inject.synchronous import get_installation, get_installation_client


@pytest.fixture
def responses():
    with sentry_responses.RequestsMock() as rsps:
        yield rsps


@pytest.fixture
def webapp_mock(mocker):

    router = APIRouter()
    mocker.patch('connect.eaas.core.extension.router', router)

    @web_app(router)
    class MyWebExtension(WebApplicationBase):

        @router.get('/settings')
        def retrieve_settings(self, installation: dict = Depends(get_installation)) -> dict:
            return installation

        @router.delete('/settings/{item_id}')
        def delete_settings(
            self,
            item_id,
        ) -> str:
            return item_id

        @router.post('/settings')
        async def update_settings(
            self,
            request: Request,
            installation_client: ConnectClient = Depends(get_installation_client),
            installation: dict = Depends(get_installation),
        ):
            settings = await request.json()

            installation_client('devops').installations[installation['id']].update(
                {'settings': settings},
            )
            return installation_client('devops').installations[installation['id']].get()

        @guest()
        @router.get('/whoami')
        def whoami(self) -> dict:
            return {'test': 'client'}

        @classmethod
        def get_static_root(cls):
            static_root = os.path.abspath(
                os.path.join(
                    os.path.dirname(inspect.getfile(cls)),
                    'static_root',
                ),
            )
            if os.path.exists(static_root) and os.path.isdir(static_root):
                return static_root
            return None

    yield MyWebExtension
