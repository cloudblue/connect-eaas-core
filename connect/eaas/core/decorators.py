from fastapi_utils.cbv import cbv
from fastapi_utils.inferring_router import InferringRouter

from connect.eaas.core.constants import (
    ANVIL_CALLABLE_ATTR_NAME,
    ANVIL_KEY_VAR_ATTR_NAME,
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
        if hasattr(cls, VARIABLES_INFO_ATTR_NAME):
            declared_vars = getattr(cls, VARIABLES_INFO_ATTR_NAME)
            for variable in variables:
                name = variable['name']
                if len(list(filter(lambda x: x['name'] == name, declared_vars))) == 0:
                    declared_vars.append(variable)
            return cls
        setattr(cls, VARIABLES_INFO_ATTR_NAME, variables)
        return cls
    return wrapper


def anvil_key_variable(name):
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


def anvil_callable():
    def wrapper(func):
        setattr(func, ANVIL_CALLABLE_ATTR_NAME, True)
        return func
    return wrapper


router = InferringRouter()
web_app = cbv
