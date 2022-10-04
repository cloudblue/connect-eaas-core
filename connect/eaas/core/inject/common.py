import json
import logging

from fastapi import Depends, Header

from connect.eaas.core.inject.models import Context
from connect.eaas.core.logging import ExtensionLogHandler

_LOGGING_HANDLER = None


def get_call_context(
    x_connect_installation_id: str = Header(),
    x_connect_user_id: str = Header(),
    x_connect_account_id: str = Header(),
    x_connect_account_role: str = Header(),
    x_connect_call_source: str = Header(),
    x_connect_call_type: str = Header(),
) -> Context:
    return Context(
        installation_id=x_connect_installation_id,
        user_id=x_connect_user_id,
        account_id=x_connect_account_id,
        account_role=x_connect_account_role,
        call_source=x_connect_call_source,
        call_type=x_connect_call_type,
    )


def get_logger(
    x_connect_logging_api_key: str = Header(None),
    x_connect_logging_metadata: str = Header('{}'),
    x_connect_logging_level: str = Header('INFO'),
    context: Context = Depends(get_call_context),
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
    return logging.LoggerAdapter(
        logger,
        context.dict(),
    )


def get_config(x_connect_config: str = Header('{}')):
    return json.loads(x_connect_config)
