import json
import logging

from connect.eaas.core.inject import common, models
from connect.eaas.core.logging import ExtensionLogHandler


def test_get_logger_with_logz_handler():
    some_metadata = {'data': 'value'}

    ctx = models.Context(
        installation_id='installation_id',
        user_id='user_id',
        account_id='account_id',
        account_role='account_role',
        call_source='ui',
        call_type='user',
    )

    adapter = common.get_logger('api_key', json.dumps(some_metadata), 'INFO', ctx)
    assert adapter.extra == ctx.dict()

    logger = adapter.logger

    assert logger.level == logging.INFO
    assert logger.name == 'eaas.webapp'
    assert common._LOGGING_HANDLER in logger.handlers
    assert isinstance(common._LOGGING_HANDLER, ExtensionLogHandler)
    assert common._LOGGING_HANDLER.default_extra_fields == some_metadata
    assert common._LOGGING_HANDLER.logzio_sender.token == 'api_key'

    logger.removeHandler(common._LOGGING_HANDLER)
    common._LOGGING_HANDLER = None


def test_get_logger_without_logz_handler(mocker):

    ctx = models.Context(
        installation_id='installation_id',
        user_id='user_id',
        account_id='account_id',
        account_role='account_role',
        call_source='ui',
        call_type='user',
    )

    adapter = common.get_logger(None, None, 'DEBUG', ctx)

    assert adapter.extra == ctx.dict()

    logger = adapter.logger

    assert logger.level == logging.DEBUG
    assert logger.name == 'eaas.webapp'
    assert common._LOGGING_HANDLER not in logger.handlers


def test_get_call_context():

    ctx = common.get_call_context(
        x_connect_installation_id='installation_id',
        x_connect_user_id='user_id',
        x_connect_account_id='account_id',
        x_connect_account_role='account_role',
        x_connect_call_source='ui',
        x_connect_call_type='user',
        x_connect_extension_id='SRVC-0000',
        x_connect_environment_id='ENV-0000-03',
        x_connect_environment_type='production',
    )

    assert ctx == models.Context(
        extension_id='SRVC-0000',
        environment_id='ENV-0000-03',
        environment_type='production',
        installation_id='installation_id',
        user_id='user_id',
        account_id='account_id',
        account_role='account_role',
        call_source='ui',
        call_type='user',
    )


def test_get_call_context_for_guest_eps():

    ctx = common.get_call_context(
        x_connect_installation_id=None,
        x_connect_user_id=None,
        x_connect_account_id=None,
        x_connect_account_role=None,
        x_connect_call_source=None,
        x_connect_call_type=None,
        x_connect_extension_id=None,
        x_connect_environment_id=None,
        x_connect_environment_type=None,
    )

    assert ctx == models.Context(
        extension_id=None,
        environment_id=None,
        environment_type=None,
        installation_id=None,
        user_id=None,
        account_id=None,
        account_role=None,
        call_source=None,
        call_type=None,
    )


def test_get_config():
    assert common.get_config('{}') == {}

    assert common.get_config('{"VAR": "value"}') == {'VAR': 'value'}
