import os
from logging import Logger

from fastapi import Depends, Header

from connect.client import ConnectClient
from connect.eaas.core.inject.common import get_logger
from connect.eaas.core.logging import RequestLogger


def get_installation_client(
    logger: Logger = Depends(get_logger),
    x_connect_installation_api_key: str = Header(),
    x_connect_api_gateway_url: str = Header(),
    x_connect_user_agent: str = Header(),
):
    return ConnectClient(
        x_connect_installation_api_key,
        endpoint=x_connect_api_gateway_url,
        use_specs=False,
        default_headers={'User-Agent': x_connect_user_agent},
        logger=RequestLogger(logger),
    )


def get_extension_client(
    logger: Logger = Depends(get_logger),
    x_connect_api_gateway_url: str = Header(),
    x_connect_user_agent: str = Header(),
):
    return ConnectClient(
        os.getenv('API_KEY'),
        endpoint=x_connect_api_gateway_url,
        use_specs=False,
        default_headers={'User-Agent': x_connect_user_agent},
        logger=RequestLogger(logger),
    )


def get_installation(
    client: ConnectClient = Depends(get_installation_client),
    x_connect_installation_id: str = Header(),
):
    return client('devops').installations[x_connect_installation_id].get()


def get_environment(
    client: ConnectClient = Depends(get_extension_client),
    x_connect_extension_id: str = Header(),
    x_connect_environment_id: str = Header(),
):
    extension = client('devops').services[x_connect_extension_id]
    return {
        variable['name']: variable['value']
        for variable in extension.environments[x_connect_environment_id].variables.all()
    }
