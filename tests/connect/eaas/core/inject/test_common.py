import json
import logging

from connect.eaas.core.inject import common
from connect.eaas.core.logging import ExtensionLogHandler


def test_get_logger_with_logz_handler():
    some_metadata = {'data': 'value'}

    logger = common.get_logger('api_key', json.dumps(some_metadata), 'INFO')

    assert logger.level == logging.INFO
    assert logger.name == 'eaas.webapp'
    assert common._LOGGING_HANDLER in logger.handlers
    assert isinstance(common._LOGGING_HANDLER, ExtensionLogHandler)
    assert common._LOGGING_HANDLER.default_extra_fields == some_metadata
    assert common._LOGGING_HANDLER.logzio_sender.token == 'api_key'

    logger.removeHandler(common._LOGGING_HANDLER)
    common._LOGGING_HANDLER = None


def test_get_logger_without_logz_handler(mocker):
    logger = common.get_logger(None, None, 'DEBUG')

    assert logger.level == logging.DEBUG
    assert logger.name == 'eaas.webapp'
    assert common._LOGGING_HANDLER not in logger.handlers
