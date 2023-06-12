import logging
import time

import pytest
import responses as sentry_responses
from fastapi import Depends
from fastapi.exceptions import RequestValidationError
from fastapi.responses import Response
from fastapi.routing import APIRouter

from connect.client import AsyncConnectClient, ClientError, ConnectClient
from connect.eaas.core.decorators import web_app
from connect.eaas.core.extension import WebApplicationBase
from connect.eaas.core.inject import asynchronous, common, synchronous
from connect.eaas.core.inject.models import Context
from connect.eaas.core.testing.fixtures import test_client_factory  # noqa


logger = logging.getLogger('connect-eaas-core')


@pytest.fixture
def responses():
    with sentry_responses.RequestsMock() as rsps:
        yield rsps


async def middleware_timing(request, call_next):
    """
    Middleware that logs all the call timings in seconds.
    """
    start_time = time.time()
    request = await call_next(request)
    elapsed = time.time() - start_time
    logger.info(f'Request processed. Elapsed time {elapsed}s')
    return request


class MiddlewareTimingClass:
    """
    Middleware that logs all the call timings in seconds.
    """
    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        start_time = time.time()
        await self.app(scope, receive, send)
        elapsed = time.time() - start_time
        logger.info(f'Request processed. Elapsed time {elapsed}s')


class MiddlewareTimingClassWithParams:
    """
    Middleware that logs the calls that are longer than the specified
     threshold in seconds. Also the logging level could be configured.
    """

    _log_fn = {
        logging.CRITICAL: logger.critical,
        logging.ERROR: logger.error,
        logging.WARNING: logger.warning,
        logging.INFO: logger.info,
        logging.DEBUG: logger.debug,
    }

    def __init__(self, app, log_level=logging.INFO, threshold=60.0):
        self.app = app
        self.log_level = log_level
        self.threshold = threshold

    async def __call__(self, scope, receive, send):
        start_time = time.time()
        await self.app(scope, receive, send)
        elapsed = time.time() - start_time
        if elapsed >= self.threshold:
            self._log_fn[self.log_level](
                f'Request processed. Elapsed time {elapsed}s',
            )


async def custom_http_exception_handler(request, exc):
    data = request.json()
    key = data['detail'][0]['loc'][-1]
    msg = data['detail'][0]['msg'].replace('value', f'The {key} field')
    return Response(msg, status_code=400)


@pytest.fixture
def webapp_mock(mocker):

    router = APIRouter()
    mocker.patch('connect.eaas.core.extension.router', router)

    @web_app(router)
    class MyWebApplication(WebApplicationBase):

        @classmethod
        def get_middlewares(cls):
            return [
                middleware_timing,
                MiddlewareTimingClass,
                (
                    MiddlewareTimingClassWithParams,
                    {
                        'log_level': logging.ERROR,
                        'threshold': 40.0,
                    },
                ),
            ]

        @classmethod
        def get_exception_handlers(cls, exception_handlers):
            exception_handlers[RequestValidationError] = custom_http_exception_handler
            return exception_handlers

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


@pytest.fixture
def empty_webapp_mock(mocker):

    router = APIRouter()
    mocker.patch('connect.eaas.core.extension.router', router)

    @web_app(router)
    class MyWebApplication(WebApplicationBase):
        pass

    return MyWebApplication
