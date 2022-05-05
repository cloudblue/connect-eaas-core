import inspect
import json

import pkg_resources

from connect.eaas.core.constants import (
    EVENT_INFO_ATTR_NAME,
    SCHEDULABLE_INFO_ATTR_NAME,
    VARIABLES_INFO_ATTR_NAME,
)


class Extension:
    def __init__(self, client, logger, config):
        self.client = client
        self.logger = logger
        self.config = config

    @classmethod
    def get_descriptor(cls):  # pragma: no cover
        return json.load(
            pkg_resources.resource_stream(
                cls.__module__,
                'extension.json',
            ),
        )

    @classmethod
    def get_events(cls):
        return cls._get_methods_info(EVENT_INFO_ATTR_NAME)

    @classmethod
    def get_schedulables(cls):
        return cls._get_methods_info(SCHEDULABLE_INFO_ATTR_NAME)

    @classmethod
    def get_variables(cls):
        return getattr(cls, VARIABLES_INFO_ATTR_NAME, [])

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
