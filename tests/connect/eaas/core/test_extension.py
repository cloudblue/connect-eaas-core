import os

import pytest
from fastapi_utils.inferring_router import InferringRouter
from pkg_resources import EntryPoint

from connect.eaas.core.constants import GUEST_ENDPOINT_ATTR_NAME
from connect.eaas.core.decorators import (
    anvil_callable, anvil_key_variable, event, guest, schedulable, variables, web_app,
)
from connect.eaas.core.extension import _invoke, AnvilExtension, EventsExtension, WebAppExtension


def test_get_events():

    class MyExtension(EventsExtension):

        @event(
            'asset_purchase_request_processing',
            statuses=['pending', 'inquiring'],
        )
        def process_purchase(self, request):
            """This process purchases"""
            pass

        @event(
            'asset_change_request_processing',
            statuses=['pending', 'inquiring'],
        )
        async def process_change(self, request):
            pass

    assert sorted(MyExtension.get_events(), key=lambda x: x['method']) == [
        {
            'method': 'process_change',
            'event_type': 'asset_change_request_processing',
            'statuses': ['pending', 'inquiring'],
        },
        {
            'method': 'process_purchase',
            'event_type': 'asset_purchase_request_processing',
            'statuses': ['pending', 'inquiring'],
        },
    ]

    assert MyExtension(None, None, None).process_purchase.__name__ == 'process_purchase'
    assert MyExtension(None, None, None).process_purchase.__doc__ == 'This process purchases'


def test_get_schedulables():

    class MyExtension(EventsExtension):

        @schedulable(
            'schedulable1_name',
            'schedulable1_description',
        )
        def schedulable1(self, request):
            """This is schedulable"""
            pass

        @schedulable(
            'schedulable2_name',
            'schedulable2_description',
        )
        async def schedulable2(self, request):
            pass

    assert sorted(MyExtension.get_schedulables(), key=lambda x: x['method']) == [
        {
            'method': 'schedulable1',
            'name': 'schedulable1_name',
            'description': 'schedulable1_description',
        },
        {
            'method': 'schedulable2',
            'name': 'schedulable2_name',
            'description': 'schedulable2_description',
        },
    ]

    assert MyExtension(None, None, None).schedulable1.__name__ == 'schedulable1'
    assert MyExtension(None, None, None).schedulable1.__doc__ == 'This is schedulable'


def test_get_variables():

    vars = [
        {
            'name': 'var1',
            'initial_value': 'val1',
        },
        {
            'name': 'var2',
            'initial_value': 'val2',
            'secure': True,
        },
    ]

    @variables(vars)
    class MyExtension(EventsExtension):
        """this is my extension"""
        pass

    assert MyExtension.get_variables() == vars
    assert MyExtension.__name__ == 'MyExtension'
    assert MyExtension.__doc__ == 'this is my extension'


def test_get_static_root(mocker):
    mocker.patch('connect.eaas.core.extension.os.path.exists', return_value=True)
    mocker.patch('connect.eaas.core.extension.os.path.isdir', return_value=True)

    class MyWebAppExtension(WebAppExtension):
        pass

    assert MyWebAppExtension.get_static_root() == os.path.abspath(
        os.path.join(
            os.path.dirname(__file__),
            'static_root',
        ),
    )


def test_get_static_root_not_exists(mocker):
    mocker.patch('connect.eaas.core.extension.os.path.exists', return_value=False)

    class MyWebAppExtension(WebAppExtension):
        pass

    assert MyWebAppExtension.get_static_root() is None


def test_get_anvil_key_variable():

    @anvil_key_variable('ANVIL_API_KEY')
    class MyAnvilExtension(AnvilExtension):
        pass

    assert MyAnvilExtension.get_anvil_key_variable() == 'ANVIL_API_KEY'
    assert MyAnvilExtension.get_variables()[0] == {
        'name': 'ANVIL_API_KEY',
        'initial_value': 'changeme!',
        'secure': True,
    }


def test_setup_anvil_callables(mocker):

    mocked_callable = mocker.patch(
        'connect.eaas.core.extension.anvil.server.callable',
    )

    class MyAnvilExtension(AnvilExtension):

        @anvil_callable()
        def my_anvil_callable(self, arg1):
            pass

    ext = MyAnvilExtension(None, None, None)

    ext.setup_anvil_callables()

    assert callable(mocked_callable.mock_calls[0].args[0])
    assert mocked_callable.mock_calls[0].args[0].__name__ == 'my_anvil_callable'


def test_invoke(mocker):

    kwargs = {
        'kw1': 'value1',
        'kw2': 'value2',
    }

    mocked_method = mocker.MagicMock()

    _invoke(mocked_method, **kwargs)

    mocked_method.assert_called_once_with(**kwargs)


@pytest.mark.parametrize(
    'vars',
    (
        [
            {
                'name': 'MY_VAR',
                'initial_value': 'my_val',
            },
        ],
        [
            {
                'name': 'MY_VAR',
                'initial_value': 'my_val',
            },
            {
                'name': 'ANVIL_API_KEY',
                'initial_value': 'changeme!',
                'secure': True,
            },
        ],
        [
            {
                'name': 'MY_VAR',
                'initial_value': 'my_val',
            },
            {
                'name': 'ANVIL_API_KEY',
                'initial_value': 'test!',
                'secure': False,
            },
        ],
    ),
)
def test_get_anvil_key_variable_with_variables_after(vars):

    @anvil_key_variable('ANVIL_API_KEY')
    @variables(vars)
    class MyAnvilExtension(AnvilExtension):
        pass

    vars_dict = {v['name']: v for v in MyAnvilExtension.get_variables()}

    for var in vars:
        assert vars_dict[var['name']] == var


@pytest.mark.parametrize(
    'vars',
    (
        [
            {
                'name': 'MY_VAR',
                'initial_value': 'my_val',
            },
        ],
        [
            {
                'name': 'MY_VAR',
                'initial_value': 'my_val',
            },
            {
                'name': 'ANVIL_API_KEY',
                'initial_value': 'changeme!',
                'secure': True,
            },
        ],
        [
            {
                'name': 'MY_VAR',
                'initial_value': 'my_val',
            },
            {
                'name': 'ANVIL_API_KEY',
                'initial_value': 'test!',
                'secure': False,
            },
        ],
    ),
)
def test_get_anvil_key_variable_with_variables_before(vars):

    @variables(vars)
    @anvil_key_variable('ANVIL_API_KEY')
    class MyAnvilExtension(AnvilExtension):
        pass

    vars_dict = {v['name']: v for v in MyAnvilExtension.get_variables()}

    for var in vars:
        if var['name'] != 'ANVIL_API_KEY':
            assert vars_dict[var['name']] == var

    assert vars_dict['ANVIL_API_KEY'] == {
        'name': 'ANVIL_API_KEY',
        'initial_value': 'changeme!',
        'secure': True,
    }


def test_guest_endpoint(mocker):

    class MyWebAppExtension(WebAppExtension):

        @guest()
        def my_endpoint(self, arg1):
            pass

    ext = MyWebAppExtension()

    assert getattr(ext.my_endpoint, GUEST_ENDPOINT_ATTR_NAME, False) is True


def test_get_routers(mocker):

    router = InferringRouter()

    @web_app(router)
    class MyExtension(WebAppExtension):

        @router.get('/authenticated')
        def test_url(self):
            pass

        @guest()
        @router.get('/unauthenticated')
        def test_guest(self):
            pass

    mocker.patch('connect.eaas.core.extension.router', router)

    mocker.patch.object(
        EntryPoint,
        'load',
        return_value=MyExtension,
    )

    auth_router, no_auth_router = MyExtension.get_routers()

    assert len(auth_router.routes) == 1
    assert len(no_auth_router.routes) == 1
    assert auth_router.routes[0].path == '/authenticated'
    assert no_auth_router.routes[0].path == '/unauthenticated'
