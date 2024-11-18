import os

import pytest
from fastapi_utils.inferring_router import InferringRouter
from pkg_resources import EntryPoint

from connect.client import AsyncConnectClient, ConnectClient
from connect.eaas.core.constants import UNAUTHORIZED_ENDPOINT_ATTR_NAME
from connect.eaas.core.decorators import (
    account_settings_page,
    admin_pages,
    anvil_callable,
    anvil_key_variable,
    customer_pages,
    devops_pages,
    django_secret_key_variable,
    event,
    guest,
    manual_transformation,
    module_pages,
    proxied_connect_api,
    schedulable,
    transformation,
    unauthorized,
    variables,
    web_app,
)
from connect.eaas.core.extension import (
    AnvilApplicationBase,
    EventsApplicationBase,
    TransformationsApplicationBase,
    WebApplicationBase,
    _invoke,
)
from connect.eaas.core.models import Context


def test_get_events():

    class MyExtension(EventsApplicationBase):

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

        @event(
            'asset_renew_request_processing',
            statuses=['pending', 'inquiring'],
        )
        def process_renew(self, request):
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
        {
            'method': 'process_renew',
            'event_type': 'asset_renew_request_processing',
            'statuses': ['pending', 'inquiring'],
        },
    ]

    assert MyExtension(None, None, None).process_purchase.__name__ == 'process_purchase'
    assert MyExtension(None, None, None).process_purchase.__doc__ == 'This process purchases'


def test_get_schedulables():

    class MyExtension(EventsApplicationBase):

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
    class MyExtension(EventsApplicationBase):
        """this is my extension"""
        pass

    assert MyExtension.get_variables() == vars
    assert MyExtension.__name__ == 'MyExtension'
    assert MyExtension.__doc__ == 'this is my extension'


def test_get_static_root(mocker):
    mocker.patch('connect.eaas.core.extension.os.path.exists', return_value=True)
    mocker.patch('connect.eaas.core.extension.os.path.isdir', return_value=True)

    class MyWebApp(WebApplicationBase):
        pass

    assert MyWebApp.get_static_root() == os.path.abspath(
        os.path.join(
            os.path.dirname(__file__),
            'static',
        ),
    )


def test_get_static_root_not_exists(mocker):
    mocker.patch('connect.eaas.core.extension.os.path.exists', return_value=False)

    class MyWebApp(WebApplicationBase):
        pass

    assert MyWebApp.get_static_root() is None


def test_get_anvil_key_variable():

    @anvil_key_variable('ANVIL_API_KEY')
    class MyAnvilApp(AnvilApplicationBase):
        pass

    assert MyAnvilApp.get_anvil_key_variable() == 'ANVIL_API_KEY'
    assert MyAnvilApp.get_variables()[0] == {
        'name': 'ANVIL_API_KEY',
        'initial_value': 'changeme!',
        'secure': True,
    }


def test_setup_anvil_callables(mocker):

    mocked_callable = mocker.patch(
        'connect.eaas.core.extension.anvil.server.callable',
    )

    class MyAnvilApp(AnvilApplicationBase):

        @anvil_callable()
        def my_anvil_callable(self, arg1):
            pass

    ext = MyAnvilApp(None, None, None)

    ext.setup_anvil_callables()

    assert callable(mocked_callable.mock_calls[0].args[0])
    assert mocked_callable.mock_calls[0].args[0].__name__ == 'my_anvil_callable'


def test_get_anvil_callables(mocker):

    mocker.patch(
        'connect.eaas.core.extension.anvil.server.callable',
    )

    class MyAnvilApp(AnvilApplicationBase):

        @anvil_callable()
        def my_anvil_callable(self, arg1):
            pass

    callables = MyAnvilApp.get_anvil_callables()

    assert callables == [
        {
            'method': 'my_anvil_callable',
            'summary': 'My Anvil Callable',
            'description': '',
        },
    ]


def test_get_anvil_callables_with_summary_and_description(mocker):

    mocker.patch(
        'connect.eaas.core.extension.anvil.server.callable',
    )

    class MyAnvilApp(AnvilApplicationBase):

        @anvil_callable(summary='summary', description='description')
        def my_anvil_callable(self, arg1):
            pass

    callables = MyAnvilApp.get_anvil_callables()

    assert callables == [
        {
            'method': 'my_anvil_callable',
            'summary': 'summary',
            'description': 'description',
        },
    ]


def test_get_anvil_callables_description_from_docstring(mocker):

    mocker.patch(
        'connect.eaas.core.extension.anvil.server.callable',
    )

    class MyAnvilApp(AnvilApplicationBase):

        @anvil_callable()
        def my_anvil_callable(self, arg1):
            """This is the description."""

    callables = MyAnvilApp.get_anvil_callables()

    assert callables == [
        {
            'method': 'my_anvil_callable',
            'summary': 'My Anvil Callable',
            'description': 'This is the description.',
        },
    ]


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
    class MyAnvilApp(AnvilApplicationBase):
        pass

    vars_dict = {v['name']: v for v in MyAnvilApp.get_variables()}

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
    class MyAnvilApp(AnvilApplicationBase):
        pass

    vars_dict = {v['name']: v for v in MyAnvilApp.get_variables()}

    for var in vars:
        if var['name'] != 'ANVIL_API_KEY':
            assert vars_dict[var['name']] == var

    assert vars_dict['ANVIL_API_KEY'] == {
        'name': 'ANVIL_API_KEY',
        'initial_value': 'changeme!',
        'secure': True,
    }


def test_guest_endpoint(mocker):

    class MyWebApp(WebApplicationBase):

        @guest()
        def my_endpoint(self, arg1):
            pass

    ext = MyWebApp()

    assert getattr(ext.my_endpoint, UNAUTHORIZED_ENDPOINT_ATTR_NAME, False) is True


def test_unauthorized_endpoint(mocker):

    class MyWebApp(WebApplicationBase):

        @unauthorized()
        def my_endpoint(self, arg1):
            pass

    ext = MyWebApp()

    assert getattr(ext.my_endpoint, UNAUTHORIZED_ENDPOINT_ATTR_NAME, False) is True


def test_get_routers(mocker):

    router = InferringRouter()

    @web_app(router)
    class MyExtension(WebApplicationBase):

        @router.get('/authenticated')
        def test_url(self):
            pass

        @guest()
        @router.get('/unauthenticated-deprecated')
        def test_guest(self):
            pass

        @unauthorized()
        @router.get('/unauthenticated')
        def test_unauthorized(self):
            pass

    mocker.patch('connect.eaas.core.extension.router', router)

    auth_router, no_auth_router = MyExtension.get_routers()

    assert len(auth_router.routes) == 1
    assert len(no_auth_router.routes) == 2
    assert auth_router.routes[0].path == '/authenticated'
    assert no_auth_router.routes[0].path == '/unauthenticated-deprecated'
    assert no_auth_router.routes[1].path == '/unauthenticated'


def test_get_ui_modules(mocker):
    router = InferringRouter()

    @account_settings_page('Extension settings', '/static/settings.html')
    @module_pages('Main Page', '/static/main.html', '/static/icon.png')
    @admin_pages([{'label': 'Admin page', 'url': '/static/admin.html'}])
    @devops_pages([{'label': 'tab1', 'url': '/static/tab1.html'}])
    @customer_pages(
        pages=[
            {
                'label': 'Customer Home Page',
                'url': '/static/customer.html',
            },
        ],
    )
    @web_app(router)
    class MyExtension(WebApplicationBase):

        @router.get('/authenticated')
        def test_url(self):
            pass

        @guest()
        @router.get('/unauthenticated-deprecated')
        def test_guest(self):
            pass

        @unauthorized()
        @router.get('/unauthenticated')
        def test_unauthorized(self):
            pass

    mocker.patch('connect.eaas.core.extension.router', router)

    ui_modules = MyExtension.get_ui_modules()
    assert ui_modules == {
        'settings': {
            'label': 'Extension settings',
            'url': '/static/settings.html',
        },
        'modules': {
            'label': 'Main Page',
            'url': '/static/main.html',
            'icon': '/static/icon.png',
        },
        'admins': [{'label': 'Admin page', 'url': '/static/admin.html'}],
        'devops': [{'label': 'tab1', 'url': '/static/tab1.html'}],
        'customer': [{'label': 'Customer Home Page', 'url': '/static/customer.html'}],
    }


def test_get_ui_modules_with_children(mocker):
    router = InferringRouter()

    @account_settings_page('Extension settings', '/static/settings.html')
    @module_pages(
        'Main Page',
        '/static/main.html',
        '/static/icon.png',
        children=[
            {'label': 'Child page', 'url': '/static/child.html', 'icon': '/static/icon.png'},
        ],
    )
    @admin_pages([{'label': 'Admin page', 'url': '/static/admin.html'}])
    @web_app(router)
    class MyExtension(WebApplicationBase):

        @router.get('/authenticated')
        def test_url(self):
            pass

        @guest()
        @router.get('/unauthenticated-deprecated')
        def test_guest(self):
            pass

        @unauthorized()
        @router.get('/unauthenticated')
        def test_unauthorized(self):
            pass

    mocker.patch('connect.eaas.core.extension.router', router)

    mocker.patch.object(
        EntryPoint,
        'load',
        return_value=MyExtension,
    )

    ui_modules = MyExtension.get_ui_modules()
    assert ui_modules == {
        'settings': {
            'label': 'Extension settings',
            'url': '/static/settings.html',
        },
        'modules': {
            'label': 'Main Page',
            'url': '/static/main.html',
            'icon': '/static/icon.png',
            'children': [
                {'label': 'Child page', 'url': '/static/child.html', 'icon': '/static/icon.png'},
            ],
        },
        'admins': [{'label': 'Admin page', 'url': '/static/admin.html'}],
    }


def test_get_proxied_connect_api_not_set():
    class MyWebApp(WebApplicationBase):
        pass

    assert MyWebApp.get_proxied_connect_api() == []


@pytest.mark.parametrize(
    'endpoints',
    (
        [],
        ['/p/1'],
        ['/api/v1/ep', '/public/v2/ep/test'],
        {
            '/api/v1/ep': 'view',
            '/public/v2/ep/test': 'edit',
        },
    ),
)
def test_get_proxied_connect_api(endpoints):
    @proxied_connect_api(endpoints)
    class MyWebApp(WebApplicationBase):
        pass

    assert MyWebApp.get_proxied_connect_api() == endpoints


def test_get_transformations():

    class MyExtension(TransformationsApplicationBase):
        @transformation(
            name='my transformation',
            description='The my transformation',
            edit_dialog_ui='/static/my_settings.html',
        )
        def transform_row(self, row):
            pass

        @manual_transformation()
        @transformation(
            name='my manual transformation',
            description='The transformation',
            edit_dialog_ui='/static/settings.html',
        )
        def dummy(self, row):
            pass

        @transformation(
            name='another manual transformation',
            description='The transformation',
            edit_dialog_ui='/static/settings.html',
        )
        @manual_transformation()
        def dummy2(self, row):
            pass

    transformations = MyExtension.get_transformations()
    assert len(transformations) == 3
    assert {
        'method': 'transform_row',
        'name': 'my transformation',
        'description': 'The my transformation',
        'edit_dialog_ui': '/static/my_settings.html',
        'manual': False,
    } in transformations
    assert {
        'method': 'dummy',
        'name': 'my manual transformation',
        'description': 'The transformation',
        'edit_dialog_ui': '/static/settings.html',
        'manual': True,
    } in transformations
    assert {
        'method': 'dummy2',
        'name': 'another manual transformation',
        'description': 'The transformation',
        'edit_dialog_ui': '/static/settings.html',
        'manual': True,
    } in transformations


def test_get_installation_admin_client(mocker, client_mocker_factory):
    client_mocker = client_mocker_factory(base_url='https://localhost/public/v1')

    ctx = Context(
        extension_id='SRVC-0000',
        environment_id='ENV-0000-03',
        environment_type='production',
    )
    client_mocker('devops').services[ctx.extension_id].installations[
        'EIN-123'
    ].action('impersonate').post(
        return_value={'installation_api_key': 'my_inst_api_key'},
    )

    extension_client = ConnectClient(
        'api_key',
        endpoint='https://localhost/public/v1',
        default_headers={'A': 'B'},
        logger=mocker.MagicMock(),
        use_specs=False,
    )

    app = EventsApplicationBase(
        extension_client,
        None,
        None,
        None,
        None,
        ctx,
    )

    installation_admin_client = app.get_installation_admin_client('EIN-123')

    assert isinstance(installation_admin_client, ConnectClient)
    assert installation_admin_client.api_key == 'my_inst_api_key'
    assert installation_admin_client.endpoint == extension_client.endpoint
    assert installation_admin_client.default_headers == extension_client.default_headers
    assert installation_admin_client.logger == extension_client.logger


@pytest.mark.asyncio
async def test_get_installation_admin_async_client(mocker, async_client_mocker_factory):
    client_mocker = async_client_mocker_factory(base_url='https://localhost/public/v1')

    ctx = Context(
        extension_id='SRVC-0000',
        environment_id='ENV-0000-03',
        environment_type='production',
    )
    client_mocker('devops').services[ctx.extension_id].installations[
        'EIN-123'
    ].action('impersonate').post(
        return_value={'installation_api_key': 'my_inst_api_key'},
    )

    extension_client = AsyncConnectClient(
        'api_key',
        endpoint='https://localhost/public/v1',
        default_headers={'A': 'B'},
        logger=mocker.MagicMock(),
        use_specs=False,
    )

    app = EventsApplicationBase(
        extension_client,
        None,
        None,
        None,
        None,
        ctx,
    )

    installation_admin_client = await app.get_installation_admin_async_client('EIN-123')

    assert isinstance(installation_admin_client, AsyncConnectClient)
    assert installation_admin_client.api_key == 'my_inst_api_key'
    assert installation_admin_client.endpoint == extension_client.endpoint
    assert installation_admin_client.default_headers == extension_client.default_headers
    assert installation_admin_client.logger == extension_client.logger


def test_transformations_constructor(mocker):
    client = mocker.MagicMock()
    logger = mocker.MagicMock()
    config = mocker.MagicMock()
    installation_client = mocker.MagicMock()
    installation = mocker.MagicMock()
    context = mocker.MagicMock()
    transformation_request = mocker.MagicMock()

    class MyExtension(TransformationsApplicationBase):
        @transformation(
            name='my transformation',
            description='The my transformation',
            edit_dialog_ui='/static/my_settings.html',
        )
        def transform_row(self, row):
            pass

    ext = MyExtension(
        client=client,
        logger=logger,
        config=config,
        installation_client=installation_client,
        installation=installation,
        context=context,
        transformation_request=transformation_request,
    )

    assert ext.client == client
    assert ext.logger == logger
    assert ext.config == config
    assert ext.installation_client == installation_client
    assert ext.installation == installation
    assert ext.context == context
    assert ext.transformation_request == transformation_request


def test_get_installation_admin_client_for_transformations(mocker, client_mocker_factory):
    client_mocker = client_mocker_factory(base_url='https://localhost/public/v1')

    ctx = Context(
        extension_id='SRVC-0000',
        environment_id='ENV-0000-03',
        environment_type='production',
    )
    client_mocker('devops').services[ctx.extension_id].installations[
        'EIN-123'
    ].action('impersonate').post(
        return_value={'installation_api_key': 'my_inst_api_key'},
    )

    extension_client = ConnectClient(
        'api_key',
        endpoint='https://localhost/public/v1',
        default_headers={'A': 'B'},
        logger=mocker.MagicMock(),
        use_specs=False,
    )

    class MyExtension(TransformationsApplicationBase):
        @transformation(
            name='my transformation',
            description='The my transformation',
            edit_dialog_ui='/static/my_settings.html',
        )
        def transform_row(self, row):
            pass

    ext = MyExtension(
        client=extension_client,
        logger=None,
        config=None,
        installation_client=None,
        installation=None,
        context=ctx,
        transformation_request=None,
    )

    installation_admin_client = ext.get_installation_admin_client('EIN-123')

    assert isinstance(installation_admin_client, ConnectClient)
    assert installation_admin_client.api_key == 'my_inst_api_key'
    assert installation_admin_client.endpoint == extension_client.endpoint
    assert installation_admin_client.default_headers == extension_client.default_headers
    assert installation_admin_client.logger == extension_client.logger


@pytest.mark.asyncio
async def test_get_installation_admin_async_client_for_transformations(
    mocker,
    async_client_mocker_factory,
):
    client_mocker = async_client_mocker_factory(base_url='https://localhost/public/v1')

    ctx = Context(
        extension_id='SRVC-0000',
        environment_id='ENV-0000-03',
        environment_type='production',
    )
    client_mocker('devops').services[ctx.extension_id].installations[
        'EIN-123'
    ].action('impersonate').post(
        return_value={'installation_api_key': 'my_inst_api_key'},
    )

    extension_client = AsyncConnectClient(
        'api_key',
        endpoint='https://localhost/public/v1',
        default_headers={'A': 'B'},
        logger=mocker.MagicMock(),
        use_specs=False,
    )

    class MyExtension(TransformationsApplicationBase):
        @transformation(
            name='my transformation',
            description='The my transformation',
            edit_dialog_ui='/static/my_settings.html',
        )
        def transform_row(self, row):
            pass

    ext = MyExtension(
        client=extension_client,
        logger=None,
        config=None,
        installation_client=None,
        installation=None,
        context=ctx,
        transformation_request=None,
    )

    installation_admin_client = await ext.get_installation_admin_async_client('EIN-123')

    assert isinstance(installation_admin_client, AsyncConnectClient)
    assert installation_admin_client.api_key == 'my_inst_api_key'
    assert installation_admin_client.endpoint == extension_client.endpoint
    assert installation_admin_client.default_headers == extension_client.default_headers
    assert installation_admin_client.logger == extension_client.logger


@pytest.mark.parametrize(
    'app_base_class',
    (
        AnvilApplicationBase,
        EventsApplicationBase,
        TransformationsApplicationBase,
        WebApplicationBase,
    ),
)
def test_get_django_secret_key_variable(app_base_class):

    @django_secret_key_variable('DJANGO_SECRET_KEY')
    class MyApp(app_base_class):
        pass

    assert MyApp.get_django_secret_key_variable() == 'DJANGO_SECRET_KEY'
    assert MyApp.get_variables()[0] == {
        'name': 'DJANGO_SECRET_KEY',
        'initial_value': 'changeme!',
        'secure': True,
    }


@pytest.mark.parametrize(
    'vars',
    (
        [
            {
                'name': 'VAR',
                'initial_value': 'VALUE',
            },
        ],
        [
            {
                'name': 'DJANGO_SECRET_KEY',
                'initial_value': 'changeme!',
                'secure': True,
            },
        ],
    ),
)
@pytest.mark.parametrize(
    'app_base_class',
    (
        AnvilApplicationBase,
        EventsApplicationBase,
        TransformationsApplicationBase,
        WebApplicationBase,
    ),
)
def test_get_django_secret_key_variable_with_variables(app_base_class, vars):

    @django_secret_key_variable('DJANGO_SECRET_KEY')
    @variables(vars)
    class MyApp(app_base_class):
        pass

    assert MyApp.get_django_secret_key_variable() == 'DJANGO_SECRET_KEY'
    assert {
        'name': 'DJANGO_SECRET_KEY',
        'initial_value': 'changeme!',
        'secure': True,
    } in MyApp.get_variables()
