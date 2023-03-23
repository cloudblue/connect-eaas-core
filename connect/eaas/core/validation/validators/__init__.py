from connect.eaas.core.validation.validators.anvilapp import validate_anvilapp  # noqa
from connect.eaas.core.validation.validators.base import (  # noqa
    validate_docker_compose_yml,
    validate_extension_json,
    validate_pyproject_toml,
    validate_variables,
)
from connect.eaas.core.validation.validators.eventsapp import validate_eventsapp  # noqa
from connect.eaas.core.validation.validators.webapp import validate_webapp  # noqa
from connect.eaas.core.validation.validators.tfnapp import validate_tfnapp  # noqa


def get_validators():
    return [
        validate_pyproject_toml,
        validate_extension_json,
        validate_docker_compose_yml,
        validate_eventsapp,
        validate_anvilapp,
        validate_webapp,
        validate_tfnapp,
        validate_variables,
    ]
