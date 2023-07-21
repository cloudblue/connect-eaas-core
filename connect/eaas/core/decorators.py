from typing import Dict, List, Union

from fastapi_utils.cbv import cbv
from fastapi_utils.inferring_router import InferringRouter

from connect.eaas.core.constants import (
    ACCOUNT_SETTINGS_PAGE_ATTR_NAME,
    ADMIN_PAGES_ATTR_NAME,
    ANVIL_CALLABLE_ATTR_NAME,
    ANVIL_KEY_VAR_ATTR_NAME,
    CUSTOMER_PAGES_ATTR_NAME,
    DEVOPS_PAGES_ATTR_NAME,
    DJANGO_SECRET_KEY_VAR_ATTR_NAME,
    EVENT_INFO_ATTR_NAME,
    MODULE_PAGES_ATTR_NAME,
    PROXIED_CONNECT_API_ATTR_NAME,
    SCHEDULABLE_INFO_ATTR_NAME,
    TRANSFORMATION_ATTR_NAME,
    UNAUTHORIZED_ENDPOINT_ATTR_NAME,
    VARIABLES_INFO_ATTR_NAME,
)


def event(event_type, statuses=None):
    """
    Mark a method of an Events Application as the handler
    for a given `event_type` eventually filtering the event
    by status.

    Usage:

    ``` py3
    from connect.eaas.core.decorators import event
    from connect.eaas.core.extension import EventsApplicationBase


    class MyEventsApplication(EventsApplicationBase):

        @event(
            'asset_purchase_request_processing',
            statuses=[
                'pending', 'approved', 'failed',
                'inquiring', 'scheduled', 'revoking',
                'revoked',
            ],
        )
        def handle_purchase_request(self, request):
            pass
    ```

    Args:
        event_type (str): The type of event this handler is for.
        statuses (List[str]): List of statuses of the event that this handler
            want to receive.

    !!! note
        The list of statuses is required for `background` event types
        only and must not be set for `interactive` events.
    """
    def wrapper(func):
        setattr(
            func,
            EVENT_INFO_ATTR_NAME,
            {
                'method': func.__name__,
                'event_type': event_type,
                'statuses': statuses,
            },
        )
        return func
    return wrapper


def schedulable(name, description):
    """
    Mark a method of an Events Application as that can be invoked
    on a scheduled basis.

    Usage:

    ``` py3
    from connect.eaas.core.decorators import schedulable
    from connect.eaas.core.extension import EventsApplicationBase

    class MyEventsApplication(EventsApplicationBase):

        @schedulable(
            'Schedulable method mock',
            'It can be used to test DevOps scheduler.',
        )
        def execute_scheduled_processing(self, schedule):
            pass
    ```

    Args:
        name (str): The name of this schedulable method.
        description (str): Description of what this schedulable method do.

    !!! note
        The `name` and `description` arguments are used by the
        `create new schedule` wizard of the Connect DevOps module
        to allow to identify the method when creating schedules for it.
    """
    def wrapper(func):
        setattr(
            func,
            SCHEDULABLE_INFO_ATTR_NAME,
            {
                'method': func.__name__,
                'name': name,
                'description': description,
            },
        )
        return func
    return wrapper


def variables(variables):
    """
    Class decorator to declare variables needed by your application.
    The declared variables will be created on the first run with the
    specified `initial_value` if they don't exist.

    Usage:

    ``` python
    from connect.eaas.core.decorators import variables
    from connect.eaas.core.extension import EventsApplicationBase


    @variables(
        [
            {
            "name": "ASSET_REQUEST_APPROVE_TEMPLATE_ID",
            "initial_value": "<change_with_purchase_request_approve_template_id>"
            },
            {
            "name": "ASSET_REQUEST_CHANGE_TEMPLATE_ID",
            "initial_value": "<change_with_change_request_approve_template_id>"
            },
            {
            "name": "TIER_REQUEST_APPROVE_TEMPLATE_ID",
            "initial_value": "<change_with_tier_request_approve_template_id>"
            },
        ],
    )
    class MyEventsApplication(EventsApplicationBase):
        pass
    ```

    Args:
        variables (List[Dict]): The list of environment variables you want to initialize.
    """
    def wrapper(cls):
        if hasattr(cls, VARIABLES_INFO_ATTR_NAME):
            declared_vars = getattr(cls, VARIABLES_INFO_ATTR_NAME)
            for variable in variables:
                name = variable['name']
                if len(list(filter(lambda x: x['name'] == name, declared_vars))) == 0:  # noqa: B023
                    declared_vars.append(variable)
            return cls
        setattr(cls, VARIABLES_INFO_ATTR_NAME, variables)
        return cls
    return wrapper


def anvil_key_variable(name):
    """
    Class decorator for an Anvil Application that declare the name
    of the environment variable that stores the Anvil Server Uplink
    key.

    Usage:

    ``` py3
    from connect.eaas.core.decorators import anvil_key_variable
    from connect.eaas.core.extension import AnvilApplicationBase


    @anvil_key_variable('ANVIL_SERVER_UPLINK_KEY')
    class MyAnvilApplication(AnvilApplicationBase):
        pass
    ```

    Args:
        name (str): Name of the environment variable.

    !!! note
        This environment variable does not need to be
        declared using the `@variables` decorator it will be
        automatically declared as a `secure` variable with
        the `initial_value` set to `changeme!`.
    """
    def wrapper(cls):
        setattr(cls, ANVIL_KEY_VAR_ATTR_NAME, name)
        variables = []
        if not hasattr(cls, VARIABLES_INFO_ATTR_NAME):
            setattr(cls, VARIABLES_INFO_ATTR_NAME, variables)
        else:
            variables = getattr(cls, VARIABLES_INFO_ATTR_NAME)
        if len(list(filter(lambda x: x['name'] == name, variables))) == 0:
            variables.append({'name': name, 'initial_value': 'changeme!', 'secure': True})
        return cls
    return wrapper


def anvil_callable(summary=None, description=None):
    """
    Mark a method of an Anvil Application class as a method that
    can be called from an Anvil frontend application.

    Usage:

    ``` py3
    from connect.eaas.core.decorators import anvil_callable, anvil_key_variable
    from connect.eaas.core.extension import AnvilApplicationBase


    @anvil_key_variable('ANVIL_SERVER_UPLINK_KEY')
    class MyAnvilApplication(AnvilApplicationBase):

        @anvil_callable(
            summary='This function say hello',
            decription='Description of what this function do',
        )
        def say_hello(self, name):
            return f'Hello {name}'
    ```

    Args:
        summary (str): Summary of the callable.
        description (str): Description of the callable.
    """
    def wrapper(func):
        setattr(
            func,
            ANVIL_CALLABLE_ATTR_NAME,
            {
                'method': func.__name__,
                'summary': summary or func.__name__.replace('_', ' ').title(),
                'description': description or func.__doc__ or '',
            },
        )
        return func
    return wrapper


def unauthorized():
    """
    Mark an endpoint of a Web Application as not subject to
    the Connect authentication.

    Usage:

    ``` py3
    from connect.eaas.core.decorators import unauthorized, router, web_app
    from connect.eaas.core.extension import WebApplicationBase


    @web_app(router)
    class MyWebApp(WebApplicationBase):

        @unauthorized()
        @router.get('/my_endpoint')
        def my_endpoint(self):
            pass
    ```

    !!! note
        In releases prior to 27, unauthenticated endpoints required authorization by CloudBlue.
        Although this feature is now enabled by default,
        if your extension was created using a version earlier than release 27,
        you must still contact CloudBlue support
        to enable unauthenticated endpoints for your extension.
    """
    def wrapper(func):
        setattr(func, UNAUTHORIZED_ENDPOINT_ATTR_NAME, True)
        return func
    return wrapper


guest = unauthorized
"""
!!! warning
    Deprecated: The 'guest' alias is maintained for backward compatibility purposes and
    will be deprecated in future releases. Use 'unauthorized' instead.
"""


def account_settings_page(label: str, url: str, icon: str = None):
    """
    Class decorator for Web Application that declare which html page
    must be rendererd within the `Account Settings` module of Connect UI
    to handle the extension installation settings.

    Usage:

    ``` py3
    from connect.eaas.core.decorators import (
        account_settings_page, router, web_app,
    )
    from connect.eaas.core.extension import WebApplicationBase


    @web_app(router)
    @account_settings_page('My settings', '/static/settings.html')
    class MyWebApp(WebApplicationBase):
        pass
    ```

    Args:
        label (str): The label to use for such page.
        url (str): The url path to the html page including `/static`.
        icon (str): The image path to the icon including `/static`.
    """
    def wrapper(cls):
        data = {'label': label, 'url': url}
        if icon:
            data['icon'] = icon
        setattr(cls, ACCOUNT_SETTINGS_PAGE_ATTR_NAME, data)
        return cls
    return wrapper


def module_pages(label: str, url: str, icon: str = None, children: List[Dict] = None):
    """
    Class decorator for Web Application that declare the main page
    for a web application and optionally a list of children pages.

    Usage:

    ``` py3
    from connect.eaas.core.decorators import (
        module_pages, router, web_app,
    )
    from connect.eaas.core.extension import WebApplicationBase


    @web_app(router)
    @module_pages(
        'Home',
        '/static/home.html',
        '/static/icon.png',
        children=[
            {
                'label': 'Child page 1',
                'url': '/static/child1.html',
                'icon': '/static/c1icon.png',
            },
        ],
    )
    class MyWebApp(WebApplicationBase):
        pass
    ```

    Args:
        label (str): The label to use for such page.
        url (str): The url path to the html page including `/static`.
        url (str): Optional icon url path including `/static`.
        children (List[Dict]): Optional list of children pages.

    !!! note
        Your extension pages will be rendered using a `Tabs` component
        of the Connect UI.
        The main page will be the first tab and the label will be the tab
        label. For each child in children a tab will be added to the `Tabs`
        component using its label as the tab label.
    """
    def wrapper(cls):
        data = {'label': label, 'url': url}
        if icon:
            data['icon'] = icon
        if children:
            data['children'] = children
        setattr(cls, MODULE_PAGES_ATTR_NAME, data)
        return cls
    return wrapper


def admin_pages(pages: List[Dict]):
    """
    Class decorator for Web Application that declare a list of
    admin pages.
    Admin pages are shown in the detail view of a specific installation
    of the Web Application inside your extension details view.

    Usage:

    ``` py3
    from connect.eaas.core.decorators import (
        admin_pages, router, web_app,
    )
    from connect.eaas.core.extension import WebApplicationBase


    @web_app(router)
    @admin_pages(
        [
            {
                'label': 'My Admin 1',
                'url': '/static/admin1.html',
                'icon': '/static/icon.png',
            },
        ],
    )
    class MyWebApp(WebApplicationBase):
        pass
    ```

    Args:
        pages (List[Dict]): Optional list of admin pages.
    """
    def wrapper(cls):
        setattr(cls, ADMIN_PAGES_ATTR_NAME, pages)
        return cls
    return wrapper


def transformation(name: str, description: str, edit_dialog_ui: str):
    """
    Mark a method of an Transformations Application as a tranformation
    function.

    Usage:

    ``` py3
    from connect.eaas.core.decorators import transformation
    from connect.eaas.core.extension import EventsApplicationBase

    class MyTransformationsApplication(TransformationsApplicationBase):

        @transformation(
            'Split column by delimiter',
            'Split a column into multiple columns based on a delimiter',
            '/static/configure_split_by_delimiter.html',
        )
        def split_by_delimiter(self, row):
            pass
    ```

    Args:
        name (str): The name of this transformation method.
        description (str): Description of what this transformation method do.
        edit_dialog_ui (str): Path to the html page that allow configuring
        this transformation.
    """
    def wrapper(func):
        manual = False
        if hasattr(func, TRANSFORMATION_ATTR_NAME):
            manual = getattr(func, TRANSFORMATION_ATTR_NAME)['manual']

        setattr(
            func,
            TRANSFORMATION_ATTR_NAME,
            {
                'method': func.__name__,
                'name': name,
                'description': description,
                'edit_dialog_ui': edit_dialog_ui,
                'manual': manual,
            },
        )
        return func
    return wrapper


def manual_transformation():
    """
    Mark a method of an Transformations Application as a manual tranformation.

    Usage:

    ``` py3
    from connect.eaas.core.decorators import manual_transformation, transformation
    from connect.eaas.core.extension import EventsApplicationBase

    class MyTransformationsApplication(TransformationsApplicationBase):

        @manual_transformation()
        @transformation(
            'Split column by delimiter',
            'Split a column into multiple columns based on a delimiter',
            '/static/configure_split_by_delimiter.html',
        )
        def manual(self, row):
            pass
    ```
    """
    def wrapper(func):
        if hasattr(func, TRANSFORMATION_ATTR_NAME):
            data = getattr(func, TRANSFORMATION_ATTR_NAME)
            data['manual'] = True
        else:
            data = {'manual': True}

        setattr(
            func,
            TRANSFORMATION_ATTR_NAME,
            data,
        )
        return func
    return wrapper


def devops_pages(pages: List[Dict]):
    """
    Class decorator for Web Application that declare a list of
    devops pages that will be displayed.
    These pages are shown as additional tabs in the main devops page.

    Usage:

    ``` py3
    from connect.eaas.core.decorators import (
        devops_pages, router, web_app,
    )
    from connect.eaas.core.extension import WebApplicationBase


    @web_app(router)
    @devops_pages(
        [
            {
                'label': 'My tab 1',
                'url': '/static/tab1.html',
                'icon': '/static/icon.png',
            },
        ],
    )
    class MyWebApp(WebApplicationBase):
        pass
    ```

    Args:
        pages (List[Dict]): List of devops pages including the label, the url and the icon.
    """
    def wrapper(cls):
        setattr(cls, DEVOPS_PAGES_ATTR_NAME, pages)
        return cls
    return wrapper


def proxied_connect_api(endpoints: Union[List[str], Dict]):
    """
    Class decorator for Web Application that declares a list (or dict) of
    Connect Public API endpoints, accessible on the hosts of the extension
    and its installations.
    Each item shall start with a / and contain a full API path of the endpoint.
    Nested API endpoints with dynamic IDs are not supported at the moment.

    Usage:

    ``` py3
    from connect.eaas.core.decorators import (
        proxied_connect_api, router, web_app,
    )
    from connect.eaas.core.extension import WebApplicationBase


    @web_app(router)
    @proxied_connect_api(
        [
            '/public/v1/marketplaces',
            '/public/v1/auth/context',
        ],
    )
    class MyWebApp(WebApplicationBase):
        pass


    @web_app(router)
    @proxied_connect_api(
        {
            '/public/v1/marketplaces': 'edit',
            '/public/v1/auth/context': 'view',
        },
    )
    class MyWebApp2(WebApplicationBase):
        pass
    ```

    Args:
        endpoints (Union[List[str], Dict]): List of endpoints.
    """
    def wrapper(cls):
        setattr(cls, PROXIED_CONNECT_API_ATTR_NAME, endpoints)
        return cls
    return wrapper


def customer_pages(pages: List[Dict]):
    """
    Class decorator for Web Application that declare the customer
     home pages (each includes label, url and icon). These pages will
     be used as customer home pages.

    Usage:

    ``` py3
    from connect.eaas.core.decorators import (
        customer_pages, router, web_app,
    )
    from connect.eaas.core.extension import WebApplicationBase


    @web_app(router)
    @customer_pages(
        [
            {
                'label': 'My page 1',
                'url': '/static/page1.html',
                'icon': '/static/pageIcon.png',
            },
        ],
    )
    class MyWebApp(WebApplicationBase):
        pass
    ```

    Args:
        pages (List[Dict]): List of customer home pages including the label, the url and the icon.
    """
    def wrapper(cls):
        setattr(cls, CUSTOMER_PAGES_ATTR_NAME, pages)
        return cls
    return wrapper


def django_secret_key_variable(name):
    def wrapper(cls):
        setattr(cls, DJANGO_SECRET_KEY_VAR_ATTR_NAME, name)
        variables = []
        if not hasattr(cls, VARIABLES_INFO_ATTR_NAME):
            setattr(cls, VARIABLES_INFO_ATTR_NAME, variables)
        else:
            variables = getattr(cls, VARIABLES_INFO_ATTR_NAME)
        if len(list(filter(lambda x: x['name'] == name, variables))) == 0:
            variables.append({'name': name, 'initial_value': 'changeme!', 'secure': True})
        return cls
    return wrapper


router = InferringRouter()
web_app = cbv
"""
This decorator is required to be used if you want to declare any
endpoint.

Usage:

``` py3
from connect.eaas.core.decorators import (
    router, web_app,
)
from connect.eaas.core.extension import WebApplicationBase


@web_app(router)
class MyWebApp(WebApplicationBase):
    pass
```
"""
