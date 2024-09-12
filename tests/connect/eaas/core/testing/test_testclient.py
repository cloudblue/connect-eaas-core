import pytest
from fastapi.exceptions import RequestValidationError
from starlette.middleware.base import BaseHTTPMiddleware

from connect.client.exceptions import ClientError
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


def test_get_installation_and_call_sync(webapp_mock, client_mocker_factory):
    client = WebAppTestClient(webapp_mock)

    installation = {
        'id': 'EIN-012',
        'settings': {'test': 'settings'},
    }
    mocker = client_mocker_factory()
    mocker.products.all().mock(return_value=[])
    resp = client.get('/api/sync/installation_and_call', installation=installation)
    assert resp.status_code == 200
    assert resp.json() == installation


def test_get_installation_and_call_async(webapp_mock, async_client_mocker_factory):
    client = WebAppTestClient(webapp_mock)

    installation = {
        'id': 'EIN-012',
        'settings': {'test': 'settings'},
    }
    mocker = async_client_mocker_factory()
    mocker.products.all().mock(return_value=[])
    resp = client.get('/api/async/installation_and_call', installation=installation)

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
        'extension_id': 'SRVC-0000',
        'environment_id': 'ENV-0000-03',
        'environment_type': 'production',
        'installation_id': None,
        'tier_account_id': None,
        'user_id': 'UR-000',
        'account_id': 'VA-000',
        'account_role': 'vendor',
        'call_source': 'ui',
        'call_type': 'user',
    }


def test_get_call_context_custom(webapp_mock):
    client = WebAppTestClient(webapp_mock)

    ctx = {
        'extension_id': 'SRVC-0001',
        'environment_id': 'ENV-0001-01',
        'environment_type': 'development',
        'installation_id': 'EIN-111',
        'tier_account_id': None,
        'user_id': 'UR-222',
        'account_id': 'PA-333',
        'account_role': 'distributor',
        'call_source': 'api',
        'call_type': 'admin',
    }

    resp = client.get('/api/context', context=Context(**ctx))

    assert resp.status_code == 200
    assert resp.json() == ctx


def test_get_call_context_merge(webapp_mock):
    client = WebAppTestClient(webapp_mock)

    ctx = {
        'installation_id': 'EIN-111',
        'call_type': 'admin',
        'environment_id': 'ENV-0001-01',
    }

    resp = client.get('/api/context', context=ctx)

    assert resp.status_code == 200
    assert resp.json() == {
        'extension_id': 'SRVC-0000',
        'environment_id': 'ENV-0001-01',
        'environment_type': 'production',
        'installation_id': 'EIN-111',
        'tier_account_id': None,
        'user_id': 'UR-000',
        'account_id': 'VA-000',
        'account_role': 'vendor',
        'call_source': 'ui',
        'call_type': 'admin',
    }


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


def test_get_installation_admin_client(webapp_mock, client_mocker_factory):
    installation = {'settings': {'a': 'b'}}
    client_mocker = client_mocker_factory()
    client_mocker('devops').installations['EIN-01234'].get(
        return_value=installation,
    )
    client = WebAppTestClient(webapp_mock)
    resp = client.get('/api/sync/admin/EIN-01234/doit')
    assert resp.json() == installation


def test_shortcuts(mocker, webapp_mock):
    mocked_request = mocker.patch.object(WebAppTestClient, 'request')
    client = WebAppTestClient(webapp_mock)
    for idx, method in enumerate(('get', 'post', 'put', 'patch', 'delete', 'options', 'head')):
        getattr(client, method)('url')
        assert mocked_request.mock_calls[idx].args[0] == method.upper()


def test_middlewares(webapp_mock):
    client = WebAppTestClient(webapp_mock)

    assert len(client.app.user_middleware) == 3
    assert client.app.user_middleware[0].cls.__name__ == 'MiddlewareTimingClassWithParams'
    assert client.app.user_middleware[0].kwargs['log_level'] == 40
    assert client.app.user_middleware[0].kwargs['threshold'] == 40.0
    assert client.app.user_middleware[1].cls.__name__ == 'MiddlewareTimingClass'
    assert client.app.user_middleware[1].kwargs == {}
    assert client.app.user_middleware[2].cls.__name__ == 'BaseHTTPMiddleware'
    assert 'dispatch' in client.app.user_middleware[2].kwargs
    assert client.app.user_middleware[2].kwargs['dispatch'].__name__ == 'middleware_timing'


def test_exception_handlers(webapp_mock):
    client = WebAppTestClient(webapp_mock)

    assert len(client.app.exception_handlers) == 4
    assert ClientError in client.app.exception_handlers
    assert RequestValidationError in client.app.exception_handlers


def test_webapp_test_client_setup_middlewares(webapp_mock, mocker):
    client = WebAppTestClient(webapp_mock)

    mocked_app = mocker.Mock()

    def func_mid():
        pass

    class ClassMiddleware:
        pass

    middlewares = [
        func_mid,
        ClassMiddleware,
        (ClassMiddleware, {'args': 'x'}),
        {'invalid': 'middleware'},
    ]
    client._setup_middlewares(mocked_app, middlewares)

    expected_arg_list = [
        mocker.call(BaseHTTPMiddleware, dispatch=func_mid),
        mocker.call(ClassMiddleware),
        mocker.call(ClassMiddleware, args='x'),
    ]
    assert mocked_app.add_middleware.call_args_list == expected_arg_list


def test_webapp_test_client_empty(empty_webapp_mock, mocker):
    fast_mock = mocker.patch('connect.eaas.core.testing.testclient.FastAPI')
    setup_mock = mocker.patch.object(WebAppTestClient, '_setup_middlewares')

    WebAppTestClient(empty_webapp_mock)

    assert fast_mock.call_count == 1
    assert 'exception_handlers' in fast_mock.call_args.kwargs
    assert len(fast_mock.call_args.kwargs['exception_handlers']) == 1
    setup_mock.assert_not_called()
