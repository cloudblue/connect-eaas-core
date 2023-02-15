import functools
import inspect
import json
import os

import anvil.server
import pkg_resources
from connect.client import AsyncConnectClient, ConnectClient
from fastapi import APIRouter

from connect.eaas.core.constants import (
    ACCOUNT_SETTINGS_PAGE_ATTR_NAME,
    ADMIN_PAGES_ATTR_NAME,
    ANVIL_CALLABLE_ATTR_NAME,
    ANVIL_KEY_VAR_ATTR_NAME,
    DEVOPS_PAGES_ATTR_NAME,
    EVENT_INFO_ATTR_NAME,
    GUEST_ENDPOINT_ATTR_NAME,
    MODULE_PAGES_ATTR_NAME,
    SCHEDULABLE_INFO_ATTR_NAME,
    TRANSFORMATION_ATTR_NAME,
    VARIABLES_INFO_ATTR_NAME,
)
from connect.eaas.core.decorators import router


class ApplicationBase:

    @classmethod
    def get_descriptor(cls) -> dict:  # pragma: no cover
        """
        Returns the **extension.json** extension descriptor.

        !!! example

            ``` python
            {
                'name': 'My extension',
                'description': 'This extension My Extension',
                'version': '1.0.0',
                'audience': ['distributor', 'vendor', 'reseller'],
                'readme_url': 'https://example.org/README.md',
                'changelog_url': 'https://example.org/CHANGELOG.md',
                'icon': 'bar_chart',
            }
            ```
        """
        return json.load(
            pkg_resources.resource_stream(
                cls.__module__,
                'extension.json',
            ),
        )

    @classmethod
    def get_variables(cls) -> dict:
        """
        Inspects the Events Application class returning the list of environment
        variables declared using the `@variables` class decorator.

        !!! example

            ``` python
            [
                {
                    'name': 'MY_ENV_VAR',
                    'initial_value': '<<change me>>',
                    'secure': False,
                },
                {
                    'name': 'MY_SECURE_ENV_VAR',
                    'initial_value': '<<change me>>',
                    'secure': True,
                },
            ]
            ```
        """
        return getattr(cls, VARIABLES_INFO_ATTR_NAME, [])


class InstallationAdminClientMixin:
    def get_installation_admin_client(self, installation_id):
        data = (
            self.client('devops')
            .services[self.context.extension_id]
            .installations[installation_id]
            .action('impersonate')
            .post()
        )

        return ConnectClient(
            data['installation_api_key'],
            endpoint=self.client.endpoint,
            default_headers=self.client.default_headers,
            logger=self.client.logger,
        )

    async def get_installation_admin_async_client(self, installation_id):
        data = (
            await self.client('devops')
            .services[self.context.extension_id]
            .installations[installation_id]
            .action('impersonate')
            .post()
        )
        return AsyncConnectClient(
            data['installation_api_key'],
            endpoint=self.client.endpoint,
            default_headers=self.client.default_headers,
            logger=self.client.logger,
        )


class EventsApplicationBase(ApplicationBase, InstallationAdminClientMixin):
    """Base class to implements an Events Application."""

    def __init__(
        self,
        client,
        logger,
        config,
        installation_client=None,
        installation=None,
        context=None,
    ):
        self.client = client
        self.logger = logger
        self.config = config
        self.installation_client = installation_client
        self.installation = installation
        self.context = context

    @classmethod
    def get_events(cls) -> dict:
        """
        Inspects the Events Application class for methods
        decorated with the `@event` decorator and return a list of
        objects like in the following example:

        !!! example

            ``` python
            [
                {
                    'method': 'handle_purchase_request',
                    'event_type': 'asset_purchase_request_processing',
                    'statuses': ['pending', 'approved'],
                },
            ]
            ```
        """
        return cls._get_methods_info(EVENT_INFO_ATTR_NAME)

    @classmethod
    def get_schedulables(cls) -> dict:
        """
        Inspects the Events Application class for methods
        decorated with the `@schedulable` decorator and return a list of
        objects like in the following example:

        !!! example

            ``` python
            [
                {
                    'method': 'refresh_oauth_token',
                    'name': 'Refresh OAuth Token',
                    'description': 'This schedulable refresh the GCP OAuth toke',
                },
            ]
            ```
        """
        return cls._get_methods_info(SCHEDULABLE_INFO_ATTR_NAME)

    @classmethod
    def _get_methods_info(cls, attr_name):
        info = []
        members = inspect.getmembers(cls)
        for _, value in members:
            if not (inspect.isfunction(value) or inspect.iscoroutinefunction(value)):
                continue
            if hasattr(value, attr_name):
                info.append(getattr(value, attr_name))
        return info


class Extension(EventsApplicationBase):
    pass


class WebApplicationBase(ApplicationBase):
    """Base class to implements an Events Application."""
    @classmethod
    def get_static_root(cls):
        """Returns the absolute path to the `static` root folder."""
        static_root = os.path.abspath(
            os.path.join(
                os.path.dirname(inspect.getfile(cls)),
                'static',
            ),
        )
        if os.path.exists(static_root) and os.path.isdir(static_root):
            return static_root
        return None

    @classmethod
    def get_routers(cls) -> tuple:
        """
        Inspect the Web Application class for routes and return a tuple
        or two routers, the first one contains authenticated API routes,
        the second the non-authenticated ones.

        !!! warning
            Non authenticated endpoints must be authorized by CloudBlue.
            If your extension need to expose some, please contact the
            CloudBlue support.
        """
        auth = APIRouter()
        no_auth = APIRouter()
        for route in router.routes:
            if getattr(route.endpoint, GUEST_ENDPOINT_ATTR_NAME, False):
                no_auth.routes.append(route)
            else:
                auth.routes.append(route)
        return auth, no_auth

    @classmethod
    def get_ui_modules(cls):
        ui_modules = {}
        if hasattr(cls, ACCOUNT_SETTINGS_PAGE_ATTR_NAME):
            ui_modules['settings'] = getattr(cls, ACCOUNT_SETTINGS_PAGE_ATTR_NAME)

        if hasattr(cls, MODULE_PAGES_ATTR_NAME):
            ui_modules['modules'] = getattr(cls, MODULE_PAGES_ATTR_NAME)

        if hasattr(cls, ADMIN_PAGES_ATTR_NAME):
            ui_modules['admins'] = getattr(cls, ADMIN_PAGES_ATTR_NAME)

        if hasattr(cls, DEVOPS_PAGES_ATTR_NAME):
            ui_modules['devops'] = getattr(cls, DEVOPS_PAGES_ATTR_NAME)

        return ui_modules


def _invoke(method, **kwargs):
    return method(**kwargs)


class AnvilApplicationBase(ApplicationBase):
    """Base class to implements an Anvil Application."""
    def __init__(self, client, logger, config, installation_client=None, installation=None):
        self.client = client
        self.logger = logger
        self.config = config
        self.installation_client = installation_client
        self.installation = installation

    @classmethod
    def get_anvil_key_variable(cls) -> str:
        """
        Returns the name of the environment variable that
        stores the Anvil Server Uplink key.
        """
        return getattr(cls, ANVIL_KEY_VAR_ATTR_NAME, [])

    @classmethod
    def get_anvil_callables(cls):
        """
        Inspect the Anvil Application class to searching for
        method decorated with the `@anvil_callable` decorator and
        return a list of discovered anvil callable like in the following
        example:

        !!! example

            ``` python
            [
                {
                    'method': 'my_anvil_callable',
                    'summary': 'This callable sum two integer.',
                    'description': 'Example anvil callable.',
                },
            ]
            ```
        """
        callables = []
        members = inspect.getmembers(cls)
        for _, value in members:
            if not inspect.isfunction(value):
                continue

            if hasattr(value, ANVIL_CALLABLE_ATTR_NAME):
                callables.append(getattr(value, ANVIL_CALLABLE_ATTR_NAME))
        return callables

    def setup_anvil_callables(self):
        """
        Setup the Anvil Server Uplink instance with the discovered
        Anvil callables.
        """
        members = inspect.getmembers(self)
        for _, value in members:
            if not inspect.ismethod(value):
                continue

            if getattr(value, ANVIL_CALLABLE_ATTR_NAME, False):
                fn = functools.partial(_invoke, value)
                fn.__name__ = value.__name__
                anvil.server.callable(fn)


class TransformationsApplicationBase(ApplicationBase, InstallationAdminClientMixin):

    def __init__(
        self,
        client,
        logger,
        config,
        installation_client=None,
        installation=None,
        context=None,
        transformation_request=None,
    ):
        self.client = client
        self.logger = logger
        self.config = config
        self.installation_client = installation_client
        self.installation = installation
        self.context = context
        self.transformation_request = transformation_request

    @classmethod
    def get_transformations(cls) -> dict:
        """
        Inspects the Transformations Application class for methods
        decorated with the `@transformation` decorator and return a list of
        objects like in the following example:

        !!! example

            ``` python
            [
                {
                    'method': 'split_by_delimiter',
                    'name': 'Split column by delimiter',
                    'description': 'This schedulable refresh the GCP OAuth toke',
                },
            ]
            ```
        """
        return cls._get_methods_info(TRANSFORMATION_ATTR_NAME)

    @classmethod
    def _get_methods_info(cls, attr_name):
        info = []
        members = inspect.getmembers(cls)
        for _, value in members:
            if not (inspect.isfunction(value) or inspect.iscoroutinefunction(value)):
                continue
            if hasattr(value, attr_name):
                info.append(getattr(value, attr_name))
        return info
