import functools
import inspect
import json
import os

import anvil.server
import pkg_resources
from fastapi import APIRouter


from connect.eaas.core.constants import (
    ACCOUNT_SETTINGS_PAGE_ATTR_NAME,
    ADMIN_PAGES_ATTR_NAME,
    ANVIL_CALLABLE_ATTR_NAME,
    ANVIL_KEY_VAR_ATTR_NAME,
    EVENT_INFO_ATTR_NAME,
    GUEST_ENDPOINT_ATTR_NAME,
    MODULE_PAGES_ATTR_NAME,
    SCHEDULABLE_INFO_ATTR_NAME,
    VARIABLES_INFO_ATTR_NAME,
)
from connect.eaas.core.decorators import router


class ApplicationBase:

    @classmethod
    def get_descriptor(cls):  # pragma: no cover
        return json.load(
            pkg_resources.resource_stream(
                cls.__module__,
                'extension.json',
            ),
        )

    @classmethod
    def get_variables(cls):
        return getattr(cls, VARIABLES_INFO_ATTR_NAME, [])


class EventsApplicationBase(ApplicationBase):
    def __init__(self, client, logger, config, installation_client=None, installation=None):
        self.client = client
        self.logger = logger
        self.config = config
        self.installation_client = installation_client
        self.installation = installation

    @classmethod
    def get_events(cls):
        return cls._get_methods_info(EVENT_INFO_ATTR_NAME)

    @classmethod
    def get_schedulables(cls):
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

    @classmethod
    def get_static_root(cls):
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
    def get_routers(cls):
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

        return ui_modules


def _invoke(method, **kwargs):
    return method(**kwargs)


class AnvilApplicationBase(ApplicationBase):

    def __init__(self, client, logger, config, installation_client=None, installation=None):
        self.client = client
        self.logger = logger
        self.config = config
        self.installation_client = installation_client
        self.installation = installation

    @classmethod
    def get_anvil_key_variable(cls):
        return getattr(cls, ANVIL_KEY_VAR_ATTR_NAME, [])

    @classmethod
    def get_anvil_callables(cls):
        callables = []
        members = inspect.getmembers(cls)
        for _, value in members:
            if not inspect.isfunction(value):
                continue

            if hasattr(value, ANVIL_CALLABLE_ATTR_NAME):
                callables.append(getattr(value, ANVIL_CALLABLE_ATTR_NAME))
        return callables

    def setup_anvil_callables(self):
        members = inspect.getmembers(self)
        for _, value in members:
            if not inspect.ismethod(value):
                continue

            if getattr(value, ANVIL_CALLABLE_ATTR_NAME, False):
                fn = functools.partial(_invoke, value)
                fn.__name__ = value.__name__
                anvil.server.callable(fn)
