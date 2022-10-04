import json

from connect.eaas.core.testing import WebAppTestClient


def test_get_settings(webapp_mock, client_mocker_factory):
    mocker = client_mocker_factory('https://localhost/public/v1')
    mocker('devops').installations['installation_id'].get(return_value={'id': 'EIN-000-000'})

    client = WebAppTestClient(
        webapp_mock,
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


def test_delete_settings(webapp_mock):
    client = WebAppTestClient(webapp_mock)
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


def test_update_settings(webapp_mock, client_mocker_factory):
    mocker = client_mocker_factory('https://localhost/public/v1')
    mocker('devops').installations['installation_id'].get(return_value={'id': 'EIN-000-000'})
    mocker('devops').installations['EIN-000-000'].update(return_value={'id': 'EIN-000-000'})
    mocker('devops').installations['EIN-000-000'].get(
        return_value={'id': 'EIN-000-000', 'settings': {'attr': 'new_value'}},
    )

    client = WebAppTestClient(
        webapp_mock,
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


def test_whoami(webapp_mock):
    client = WebAppTestClient(
        webapp_mock,
        default_headers={
            'X-Connect-Api-Gateway-Url': 'https://localhost/public/v1',
            'X-Connect-User-Agent': 'user-agent',
        },
    )

    response = client.get('/guest/whoami')
    assert response.json() == {'test': 'client'}


def test_static_files(webapp_mock):
    client = WebAppTestClient(
        webapp_mock,
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
