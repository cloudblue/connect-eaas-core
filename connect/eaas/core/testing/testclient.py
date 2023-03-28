import inspect
import json
import os
from unittest.mock import patch
from urllib.parse import urlparse

from fastapi import FastAPI
from fastapi.params import Depends
from fastapi.staticfiles import StaticFiles
from starlette.routing import Match
from starlette.testclient import TestClient

from connect.client import ClientError
from connect.client.testing import AsyncConnectClientMocker, ConnectClientMocker
from connect.eaas.core.inject import asynchronous, synchronous
from connect.eaas.core.inject.models import Context
from connect.eaas.core.utils import client_error_exception_handler


class WebAppTestClient(TestClient):
    """
    Create a new instance of the WebAppTestClient.
    The WebAppTestClient is based on the python requests library
    and will internally create a requests.Session.
    Each interface method (get, post, ...) accepts the following extra
        keyword arguments:

    * **context**: an instance of connect.eaas.core.inject.models.Context
        to provide the endpoint with a specific call context or a dict that will merged
        with a default context.
        If this kwarg is omitted a default context is provided.
    * **installation**: an installation object to receive inside the called endpoint,
        defaults to None.
    * **config**: a dictionary with key/value pairs representing environment variables.
    * **log_level**: allow to simulate a specific log level for such endpoint call
        default to INFO.


    Usage:

    ```py3
    from connect.eaas.core.testing.testclient import WebAppTestClient

    from myext.webapp import MyWebApplication

    client = WebAppTestClient(MyWebApplication)
    response = client.get('/my/endpoint')
    ```

    Args:
        webapp: The web application class.
        base_url (str): The base url to be used.
    """
    def __init__(self, webapp, base_url='https://example.org/public/v1'):
        self._webapp_class = webapp
        self._app = self._get_application()

        super().__init__(app=self._app, base_url=base_url)

        self.headers = {
            'X-Connect-Api-Gateway-Url': self.base_url,
            'X-Connect-User-Agent': 'eaas-test-client',
            'X-Connect-Installation-Api-Key': 'ApiKey XXXX',
        }

    def request(
        self,
        method,
        url,
        params=None,
        data=None,
        headers=None,
        cookies=None,
        files=None,
        auth=None,
        timeout=None,
        allow_redirects=True,
        proxies=None,
        hooks=None,
        stream=None,
        verify=None,
        cert=None,
        json=None,
        context=None,
        installation=None,
        config=None,
        log_level=None,
    ):

        if not context:
            context = Context(**self._generate_call_context(installation))
        elif isinstance(context, dict):
            ctx_data = self._generate_call_context(installation)
            ctx_data.update(context)
            context = Context(**ctx_data)

        headers = self._populate_internal_headers(
            headers or {},
            context=context,
            installation=installation,
            config=config,
            log_level=log_level,
        )

        handler, path_params = self._get_endpoint_handler_and_params(method, url)
        if not handler:
            return super().request(
                method,
                url,
                params=params,
                data=data,
                headers=headers,
                cookies=cookies,
                files=files,
                auth=auth,
                timeout=timeout,
                allow_redirects=allow_redirects,
                proxies=proxies,
                hooks=hooks,
                stream=stream,
                verify=verify,
                cert=cert,
                json=json,
            )

        injection_info = self._get_endpoint_injection_info(handler)

        need_mocking_calls = (
            injection_info['installation'] and installation
            or injection_info['installation_admin_client'] and 'installation_id' in path_params
        )

        if not need_mocking_calls:
            return super().request(
                method,
                url,
                params=params,
                data=data,
                headers=headers,
                cookies=cookies,
                files=files,
                auth=auth,
                timeout=timeout,
                allow_redirects=allow_redirects,
                proxies=proxies,
                hooks=hooks,
                stream=stream,
                verify=verify,
                cert=cert,
                json=json,
            )

        mocker = self._get_client_mocker(handler)

        with mocker(self.base_url) as mocker, patch.dict(
            os.environ, {'API_KEY': 'ApiKey SU-000:XXX'},
        ):
            if injection_info['installation'] and installation:
                mocker.ns('devops').collection('installations').resource(
                    installation['id'],
                ).get(return_value=installation)
            if injection_info['installation_admin_client'] and 'installation_id' in path_params:
                mocker('devops').services[
                    context.extension_id
                ].installations[
                    path_params['installation_id']
                ]('impersonate').post(
                    return_value={'installation_api_key': 'api-key'},
                )
            return super().request(
                method,
                url,
                params=params,
                data=data,
                headers=headers,
                cookies=cookies,
                files=files,
                auth=auth,
                timeout=timeout,
                allow_redirects=allow_redirects,
                proxies=proxies,
                hooks=hooks,
                stream=stream,
                verify=verify,
                cert=cert,
                json=json,
            )

    def _get_client_mocker(self, handler):
        if inspect.iscoroutinefunction(handler):
            return AsyncConnectClientMocker
        return ConnectClientMocker

    def _get_endpoint_injection_info(self, handler):
        inject_module = asynchronous if inspect.iscoroutinefunction(handler) else synchronous
        signature = inspect.signature(handler)
        info = {
            'extension_client': False,
            'installation_client': False,
            'installation_admin_client': False,
            'installation': False,
        }
        for param in signature.parameters.values():
            if param.default != inspect.Parameter.empty and isinstance(param.default, Depends):
                if param.default.dependency == inject_module.get_installation_client:
                    info['installation_client'] = True
                if param.default.dependency == inject_module.get_installation_admin_client:
                    info['installation_admin_client'] = True
                if param.default.dependency == inject_module.get_installation:
                    info['installation'] = True
        return info

    def _get_endpoint_handler_and_params(self, method, url):
        path = urlparse(url).path
        for route in self.app.router.routes:
            match, child_scope = route.matches({'type': 'http', 'method': method, 'path': path})
            if match == Match.FULL:
                return child_scope['endpoint'], child_scope['path_params']
        return None, None

    def _generate_call_context(self, installation):
        return {
            'extension_id': 'SRVC-0000',
            'environment_id': 'ENV-0000-03',
            'environment_type': 'production',
            'installation_id': installation['id'] if installation else None,
            'user_id': 'UR-000',
            'account_id': 'VA-000',
            'account_role': 'vendor',
            'call_source': 'ui',
            'call_type': 'user',
        }

    def _populate_internal_headers(
        self,
        headers,
        config=None,
        installation=None,
        context=None,
        log_level=None,
    ):

        headers['X-Connect-Logging-Level'] = log_level or 'INFO'
        if config:
            headers['X-Connect-Config'] = json.dumps(config)
        if context.installation_id:
            headers['X-Connect-Installation-id'] = context.installation_id
        headers['X-Connect-Extension-Id'] = context.extension_id
        headers['X-Connect-Environment-Id'] = context.environment_id
        headers['X-Connect-Environment-Type'] = context.environment_type
        headers['X-Connect-User-Id'] = context.user_id
        headers['X-Connect-Account-Id'] = context.account_id
        headers['X-Connect-Account-Role'] = context.account_role
        headers['X-Connect-Call-Source'] = context.call_source
        headers['X-Connect-Call-Type'] = context.call_type
        return headers

    def _get_application(self):
        app = FastAPI(
            exception_handlers={
                ClientError: client_error_exception_handler,
            },
        )
        auth_router, no_auth_router = self._webapp_class.get_routers()
        app.include_router(auth_router, prefix='/api')
        app.include_router(no_auth_router, prefix='/guest')
        app.include_router(no_auth_router, prefix='/unauthorized')

        static_root = self._webapp_class.get_static_root()
        if static_root:
            app.mount('/static', StaticFiles(directory=static_root), name='static')

        return app
