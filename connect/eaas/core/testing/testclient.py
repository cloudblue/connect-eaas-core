import inspect
import json
from urllib.parse import urlparse

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from starlette.routing import Match
from starlette.testclient import TestClient

from connect.client import ClientError
from connect.client.testing import AsyncConnectClientMocker, ConnectClientMocker
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
        to provide the endpoint with a specific call context.
        If this kwarg is omitted a default context is provided.
    * **installation**: an installation object to receive inside the called endpoint,
        defaults to None.
    * **config**: a dictionary with key/value pairs representing environment variables.
    * **log_level**: allow to simulate a specific log level for such endpoint call
        default to INFO.


    Usage:

    ```python
    from connect.eaas.core.testing.testclient import WebAppTestClient

    from myext.webapp import MyWebApplication

    client = WebAppTestClient(MyWebApplication)
    response = client.get('/my/endpoint')
    ```

    **Parameters:**

    * **webapp** - The web application class.
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
        headers = self._populate_internal_headers(
            headers or {},
            context=context,
            installation=installation,
            config=config,
            log_level=log_level,
        )
        mocker = self._get_client_mocker(method, url)
        if installation and mocker:
            with mocker(self.base_url) as mocker:
                mocker.ns('devops').collection('installations').resource(
                    installation['id'],
                ).get(return_value=installation)
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

    def _get_client_mocker(self, method, url):
        path = urlparse(url).path
        for route in self.app.router.routes:
            match, child_scope = route.matches({'type': 'http', 'method': method, 'path': path})
            if match == Match.FULL:
                if inspect.iscoroutinefunction(child_scope['endpoint']):
                    return AsyncConnectClientMocker
                return ConnectClientMocker

    def _generate_call_context(self, installation):
        return Context(**{
            'installation_id': installation['id'] if installation else 'EIN-000',
            'user_id': 'UR-000',
            'account_id': 'VA-000',
            'account_role': 'vendor',
            'call_source': 'ui',
            'call_type': 'user',
        })

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

        context: Context = context or self._generate_call_context(installation)
        headers['X-Connect-Installation-id'] = context.installation_id
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

        static_root = self._webapp_class.get_static_root()
        if static_root:
            app.mount('/static', StaticFiles(directory=static_root), name='static')

        return app
