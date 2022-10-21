import pytest

from connect.eaas.core.inject.models import Context
from connect.eaas.core.testing import WebAppTestClient


@pytest.mark.parametrize(
    'url',
    (
        '/api/sync/installation',
        '/api/async/installation',
        '/api/sync/installation?param=param',
        '/api/async/installation?param=param',
    ),
)
def test_get_installation(webapp_mock, url):
    client = WebAppTestClient(webapp_mock)

    installation = {
        'id': 'EIN-012',
        'settings': {'test': 'settings'},
    }

    resp = client.get(url, installation=installation)

    assert resp.status_code == 200
    assert resp.json() == installation


def test_get_config_default(webapp_mock):
    client = WebAppTestClient(webapp_mock)
    resp = client.get('/api/config')

    assert resp.status_code == 200
    assert resp.json() == {}


def test_get_config_custom(webapp_mock):
    client = WebAppTestClient(webapp_mock)
    config = {'VAR1': 'value1'}

    resp = client.get('/api/config', config=config)

    assert resp.status_code == 200
    assert resp.json() == config


def test_get_call_context_default(webapp_mock):
    client = WebAppTestClient(webapp_mock)

    resp = client.get('/api/context')

    assert resp.status_code == 200
    assert resp.json() == {
        'installation_id': 'EIN-000',
        'user_id': 'UR-000',
        'account_id': 'VA-000',
        'account_role': 'vendor',
        'call_source': 'ui',
        'call_type': 'user',
    }


def test_get_call_context_custom(webapp_mock):
    client = WebAppTestClient(webapp_mock)

    ctx = {
        'installation_id': 'EIN-111',
        'user_id': 'UR-222',
        'account_id': 'PA-333',
        'account_role': 'distributor',
        'call_source': 'api',
        'call_type': 'admin',
    }

    resp = client.get('/api/context', context=Context(**ctx))

    assert resp.status_code == 200
    assert resp.json() == ctx


def test_not_found(webapp_mock):
    client = WebAppTestClient(webapp_mock)
    installation = {
        'id': 'EIN-012',
        'settings': {'test': 'settings'},
    }
    resp = client.get('/not/fonund', installation=installation)

    assert resp.status_code == 404


def test_method_not_allowed(webapp_mock):
    client = WebAppTestClient(webapp_mock)
    installation = {
        'id': 'EIN-012',
        'settings': {'test': 'settings'},
    }
    resp = client.post('/api/async/installation', installation=installation)

    assert resp.status_code == 405


def test_static(webapp_mock):
    client = WebAppTestClient(webapp_mock)
    resp = client.get('/static/example.html')
    assert resp.status_code == 200


def test_client_error_unexpected(webapp_mock):
    client = WebAppTestClient(webapp_mock)
    resp = client.get('/api/errors/unexpected')
    assert resp.status_code == 500
    assert resp.content == b'Unexpected error'


def test_client_error_no_json_body(webapp_mock):
    client = WebAppTestClient(webapp_mock)
    resp = client.get('/api/errors/no_json_body')
    assert resp.status_code == 401
    assert resp.content == b'401 Unauthorized'


def test_client_error_json_body(webapp_mock):
    client = WebAppTestClient(webapp_mock)
    resp = client.get('/api/errors/json_body')
    assert resp.status_code == 400
    assert resp.json() == {
        'error_code': 'ERR-000',
        'errors': ['this is an error'],
    }
