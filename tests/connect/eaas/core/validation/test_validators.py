from connect.eaas.core.validation.validators import get_validators
from connect.eaas.core.validation.validators.anvilapp import validate_anvilapp
from connect.eaas.core.validation.validators.base import (
    validate_docker_compose_yml,
    validate_extension_json,
    validate_pyproject_toml,
    validate_variables,
)
from connect.eaas.core.validation.validators.eventsapp import validate_eventsapp
from connect.eaas.core.validation.validators.tfnapp import validate_tfnapp
from connect.eaas.core.validation.validators.webapp import validate_webapp


def test_get_validators():
    assert get_validators() == [
        validate_pyproject_toml,
        validate_extension_json,
        validate_docker_compose_yml,
        validate_eventsapp,
        validate_anvilapp,
        validate_webapp,
        validate_tfnapp,
        validate_variables,
    ]
