from fastapi_utils.cbv import cbv
from fastapi_utils.inferring_router import InferringRouter

from connect.eaas.core.constants import (
    ACCOUNT_SETTINGS_PAGE_ATTR_NAME,
    ADMIN_PAGES_ATTR_NAME,
    ANVIL_CALLABLE_ATTR_NAME,
    ANVIL_KEY_VAR_ATTR_NAME,
    EVENT_INFO_ATTR_NAME,
    GUEST_ENDPOINT_ATTR_NAME,
    MODULE_PAGES_ATTR_NAME,
    SCHEDULABLE_INFO_ATTR_NAME,
    TRANSFORMATION_ATTR_NAME,
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


def guest():
    """
    Mark an endpoint of a Web Application as not subject to
    the Connect authentication.

    Usage:

    ``` py3
    from connect.eaas.core.decorators import guest, router, web_app
    from connect.eaas.core.extension import WebApplicationBase


    @web_app(router)
    class MyWebApp(WebApplicationBase):

        @guest()
        @router.get('/my_endpoint')
        def my_endpoint(self):
            pass
    ```

    !!! warning
        Non authenticated endpoints must be authorized by CloudBlue.
        If your extension need to expose some, please contact the
        CloudBlue support.
    """
    def wrapper(func):
        setattr(func, GUEST_ENDPOINT_ATTR_NAME, True)
        return func
    return wrapper


def account_settings_page(label, url):
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
    """
    def wrapper(cls):
        setattr(cls, ACCOUNT_SETTINGS_PAGE_ATTR_NAME, {'label': label, 'url': url})
        return cls
    return wrapper


def module_pages(label, url, children=None):
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
        children=[
            {
                'label': 'Child page 1',
                'url': '/static/child1.html',
            },
        ],
    )
    class MyWebApp(WebApplicationBase):
        pass
    ```

    Args:
        label (str): The label to use for such page.
        url (str): The url path to the html page including `/static`.
        children (List[Dict]): Optional list of children pages.

    !!! note
        Your extension pages will be rendered using a `Tabs` component
        of the Connect UI.
        The main page will be the first tab and the label will be the tab
        label. For each child in children a tab will be added to the `Tabs`
        component using its label as the tab label.
    """
    def wrapper(cls):
        data = {
            'label': label,
            'url': url,
        }
        if children:
            data['children'] = children
        setattr(cls, MODULE_PAGES_ATTR_NAME, data)
        return cls
    return wrapper


def admin_pages(pages):
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


def transformation(name, description, edit_dialog_ui):
    def wrapper(cls):
        setattr(cls, TRANSFORMATION_ATTR_NAME, {
            'name': name,
            'description': description,
            'edit_dialog_ui': edit_dialog_ui,
            'class_fqn': f'{cls.__module__}.{cls.__name__}',
        })
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
