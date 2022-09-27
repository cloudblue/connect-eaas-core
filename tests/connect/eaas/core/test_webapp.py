import inspect
import json
import os

from fastapi import Depends, Request

from connect.client import ConnectClient
from connect.eaas.core.decorators import guest, router, web_app
from connect.eaas.core.extension import WebAppExtension
from connect.eaas.core.inject.synchronous import get_installation, get_installation_client
from connect.eaas.core.testing import WebAppTestClient


@web_app(router)
class MyWebExtension(WebAppExtension):

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
                '..',
                '..',
                '..',
                'static_root',
            ),
        )
        if os.path.exists(static_root) and os.path.isdir(static_root):
            return static_root
        return None


def test_get_settings(client_mocker_factory):
    mocker = client_mocker_factory('https://localhost/public/v1')
    mocker('devops').installations['installation_id'].get(return_value={'id': 'EIN-000-000'})

    client = WebAppTestClient(
        MyWebExtension,
        default_headers={
            'X-Connect-Api-Gateway-Url': 'https://localhost/public/v1',
            'X-Connect-User-Agent': 'user-agent',
        },
    )

    response = client.get(
        '/api/settings',
        headers={
            'X-Connect-Installation-Api-Key': 'installation_api_key',
            'X-Connect-Installation-Id': 'installation_id',
            'X-Connect-Account-Id': 'account_id',
            'X-Connect-Account-Role': 'account_role',
            'X-Connect-User-Id': 'user_id',
            'X-Connect-Call-Source': 'ui',
            'X-Connect-Call-Type': 'user',

        },
    )
    data = response.json()

    assert response.status_code == 200
    assert data == {'id': 'EIN-000-000'}


def test_delete_settings():
    client = WebAppTestClient(MyWebExtension)
    response = client.delete(
        '/api/settings/123',
        headers={
            'X-Connect-Installation-Api-Key': 'installation_api_key',
            'X-Connect-Installation-Id': 'installation_id',
            'X-Connect-Api-Gateway-Url': 'https://localhost/public/v1',
            'X-Connect-User-Agent': 'user-agent',
            'X-Connect-Account-Id': 'account_id',
            'X-Connect-Account-Role': 'account_role',
            'X-Connect-User-Id': 'user_id',
            'X-Connect-Call-Source': 'ui',
            'X-Connect-Call-Type': 'user',
        },
    )
    data = response.json()

    assert response.status_code == 200
    assert data == '123'


def test_update_settings(client_mocker_factory):
    mocker = client_mocker_factory('https://localhost/public/v1')
    mocker('devops').installations['installation_id'].get(return_value={'id': 'EIN-000-000'})
    mocker('devops').installations['EIN-000-000'].update(return_value={'id': 'EIN-000-000'})
    mocker('devops').installations['EIN-000-000'].get(
        return_value={'id': 'EIN-000-000', 'settings': {'attr': 'new_value'}},
    )

    client = WebAppTestClient(
        MyWebExtension,
        default_headers={
            'X-Connect-Api-Gateway-Url': 'https://localhost/public/v1',
            'X-Connect-User-Agent': 'user-agent',
        },
    )
    response = client.post(
        '/api/settings',
        headers={
            'X-Connect-Installation-Api-Key': 'installation_api_key',
            'X-Connect-Installation-Id': 'installation_id',
            'X-Connect-Account-Id': 'account_id',
            'X-Connect-Account-Role': 'account_role',
            'X-Connect-User-Id': 'user_id',
            'X-Connect-Call-Source': 'ui',
            'X-Connect-Call-Type': 'user',
        },
        data=json.dumps({'attr': 'new_value'}).encode('utf-8'),
    )
    data = response.json()

    assert response.status_code == 200
    assert data == {'id': 'EIN-000-000', 'settings': {'attr': 'new_value'}}


def test_whoami():
    client = WebAppTestClient(
        MyWebExtension,
        default_headers={
            'X-Connect-Api-Gateway-Url': 'https://localhost/public/v1',
            'X-Connect-User-Agent': 'user-agent',
        },
    )

    response = client.get('/guest/whoami')
    assert response.json() == {'test': 'client'}


def test_static_files():
    client = WebAppTestClient(
        MyWebExtension,
        default_headers={
            'X-Connect-Api-Gateway-Url': 'https://localhost/public/v1',
            'X-Connect-User-Agent': 'user-agent',
        },
    )

    response = client.get(
        '/static/example.html',
        headers={
            'X-Connect-Installation-Api-Key': 'installation_api_key',
            'X-Connect-Installation-Id': 'installation_id',
        },
    )

    assert response.text == '<html><body>Hello world!</body></html>'
