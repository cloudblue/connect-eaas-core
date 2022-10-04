import os
from logging import Logger

from fastapi import Depends, Header

from connect.client import AsyncConnectClient
from connect.eaas.core.inject.common import get_logger
from connect.eaas.core.logging import RequestLogger


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
        default_headers['traceparent'] = x_connect_correlation_id

    return AsyncConnectClient(
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
        default_headers['traceparent'] = x_connect_correlation_id

    return AsyncConnectClient(
        os.getenv('API_KEY'),
        endpoint=x_connect_api_gateway_url,
        use_specs=False,
        default_headers=default_headers,
        logger=RequestLogger(logger),
    )


async def get_installation(
    client: AsyncConnectClient = Depends(get_installation_client),
    x_connect_installation_id: str = Header(),
):
    return await client("devops").installations[x_connect_installation_id].get()
