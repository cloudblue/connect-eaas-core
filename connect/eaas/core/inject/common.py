import json
import logging

from fastapi import Header

from connect.eaas.core.logging import ExtensionLogHandler


_LOGGING_HANDLER = None


def get_logger(
    x_connect_logging_api_key: str = Header(),
    x_connect_logging_metadata: str = Header(),
    x_connect_logging_level: str = Header(),
):
    global _LOGGING_HANDLER

    logger = logging.getLogger('eaas.webapp')
    if _LOGGING_HANDLER is None and x_connect_logging_api_key is not None:
        _LOGGING_HANDLER = ExtensionLogHandler(
            x_connect_logging_api_key,
            default_extra_fields=json.loads(x_connect_logging_metadata),
        )
        logger.addHandler(_LOGGING_HANDLER)

    logger.setLevel(
        getattr(logging, x_connect_logging_level),
    )

    return logger
