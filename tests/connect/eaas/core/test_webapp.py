import json

from fastapi import Depends, Request

from connect.client import ConnectClient
from connect.eaas.core.webapp_client import WebAppTestClient
from connect.eaas.core.decorators import router, web_app
from connect.eaas.core.extension import WebAppExtension
from connect.eaas.core.inject.synchronous import get_installation, get_installation_client


@web_app(router)
class MyWebExtension(WebAppExtension):
    installation: dict = Depends(get_installation)

    @router.get('/settings')
    def retrieve_settings(self) -> dict:
        return self.installation

    @router.delete('/settings/{item_id}')
    def delete_settings(self, item_id) -> str:
        return item_id

    @router.post('/settings')
    async def update_settings(
        self,
        request: Request,
        installation_client: ConnectClient = Depends(get_installation_client),
    ):
        settings = await request.json()

        installation_client('devops').installations[self.installation['id']].update(
            {'settings': settings},
        )
        return installation_client('devops').installations[self.installation['id']].get()


def test_get_settings(responses, mocker):
    mocker.patch(
        'connect.eaas.core.extension.WebAppExtension.get_static_root',
        return_value='./',
    )
    mocker.patch(
        'connect.eaas.core.webapp_client.FastAPI.mount',
    )

    responses.add(
        'GET',
        'https://localhost/public/v1/devops/installations/installation_id',
        json={'id': 'EIN-000-000'},
        status=200,
    )

    client = WebAppTestClient(
        MyWebExtension,
        default_headers={
            'X-Connect-Api-Gateway-Url': 'https://localhost/public/v1',
            'X-Connect-User-Agent': 'user-agent',
        },
    )

    response = client.get(
        '/settings',
        headers={
            'X-Connect-Installation-Api-Key': 'installation_api_key',
            'X-Connect-Installation-Id': 'installation_id',
        },
    )
    data = response.json()

    assert response.status_code == 200
    assert data == {'id': 'EIN-000-000'}


def test_delete_settings(responses):
    responses.add(
        'GET',
        'https://localhost/public/v1/devops/installations/installation_id',
        json={'id': 'EIN-000-000'},
        status=200,
    )

    client = WebAppTestClient(MyWebExtension)
    response = client.delete(
        '/settings/123',
        headers={
            'X-Connect-Installation-Api-Key': 'installation_api_key',
            'X-Connect-Installation-Id': 'installation_id',
            'X-Connect-Api-Gateway-Url': 'https://localhost/public/v1',
            'X-Connect-User-Agent': 'user-agent',
        },
    )
    data = response.json()

    assert response.status_code == 200
    assert data == '123'


def test_update_settings(responses):
    responses.add(
        'GET',
        'https://localhost/public/v1/devops/installations/installation_id',
        json={'id': 'EIN-000-000'},
        status=200,
    )
    responses.add(
        'PUT',
        'https://localhost/public/v1/devops/installations/EIN-000-000',
        json={'id': 'EIN-000-000'},
        status=200,
    )
    responses.add(
        'GET',
        'https://localhost/public/v1/devops/installations/EIN-000-000',
        json={'id': 'EIN-000-000', 'settings': {'attr': 'new_value'}},
        status=200,
    )

    client = WebAppTestClient(
        MyWebExtension,
        default_headers={
            'X-Connect-Api-Gateway-Url': 'https://localhost/public/v1',
            'X-Connect-User-Agent': 'user-agent',
        },
    )
    response = client.post(
        '/settings',
        headers={
            'X-Connect-Installation-Api-Key': 'installation_api_key',
            'X-Connect-Installation-Id': 'installation_id',
        },
        data=json.dumps({'attr': 'new_value'}).encode('utf-8'),
    )
    data = response.json()

    assert response.status_code == 200
    assert data == {'id': 'EIN-000-000', 'settings': {'attr': 'new_value'}}

    assert len(responses.calls) == 3

    payload = json.loads(responses.calls[1].request.body)
    assert payload == {'settings': {'attr': 'new_value'}}
