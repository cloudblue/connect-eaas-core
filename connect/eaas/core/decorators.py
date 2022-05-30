from fastapi_utils.cbv import cbv
from fastapi_utils.inferring_router import InferringRouter

from connect.eaas.core.constants import (
    EVENT_INFO_ATTR_NAME,
    SCHEDULABLE_INFO_ATTR_NAME,
    VARIABLES_INFO_ATTR_NAME,
)


def event(event_type, statuses=None):
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
    def wrapper(cls):
        setattr(cls, VARIABLES_INFO_ATTR_NAME, variables)
        return cls
    return wrapper


router = InferringRouter()
web_app = cbv
