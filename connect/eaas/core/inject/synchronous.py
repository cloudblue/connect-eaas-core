import os
from logging import Logger

from fastapi import Depends, Header, Path

from connect.client import ConnectClient
from connect.eaas.core.inject.common import get_call_context, get_logger
from connect.eaas.core.inject.models import Context
from connect.eaas.core.logging import RequestLogger
from connect.eaas.core.utils import get_correlation_id


def get_installation_client(
    logger: Logger = Depends(get_logger),
    x_connect_installation_api_key: str = Header(),
    x_connect_api_gateway_url: str = Header(),
    x_connect_user_agent: str = Header(),
    x_connect_correlation_id: str = Header(None),
):

    default_headers = {
        'User-Agent': x_connect_user_agent,
    }
    if x_connect_correlation_id:
        default_headers['ext-traceparent'] = get_correlation_id(x_connect_correlation_id)

    return ConnectClient(
        x_connect_installation_api_key,
        endpoint=x_connect_api_gateway_url,
        use_specs=False,
        default_headers=default_headers,
        logger=RequestLogger(logger),
    )


def get_extension_client(
    logger: Logger = Depends(get_logger),
    x_connect_api_gateway_url: str = Header(),
    x_connect_user_agent: str = Header(),
    x_connect_correlation_id: str = Header(None),
):
    default_headers = {
        'User-Agent': x_connect_user_agent,
    }
    if x_connect_correlation_id:
        default_headers['ext-traceparent'] = get_correlation_id(x_connect_correlation_id)

    return ConnectClient(
        os.getenv('API_KEY'),
        endpoint=x_connect_api_gateway_url,
        use_specs=False,
        default_headers=default_headers,
        logger=RequestLogger(logger),
    )


def get_installation(
    client: ConnectClient = Depends(get_installation_client),
    x_connect_installation_id: str = Header(),
):
    return client('devops').installations[x_connect_installation_id].get()


def get_installation_admin_client(
    installation_id: str = Path(),
    context: Context = Depends(get_call_context),
    client: ConnectClient = Depends(get_extension_client),
):
    data = (
        client('devops')
        .services[context.extension_id]
        .installations[installation_id]
        .action('impersonate')
        .post()
    )

    return ConnectClient(
        data['installation_api_key'],
        endpoint=client.endpoint,
        default_headers=client.default_headers,
        logger=client.logger,
    )
