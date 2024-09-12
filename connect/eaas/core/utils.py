import os

from fastapi import Request
from fastapi.responses import JSONResponse, PlainTextResponse

from connect.client import ClientError


def obfuscate_header(key, value):
    if key in ('authorization', 'authentication'):
        if value.startswith('ApiKey '):
            return value.split(':')[0] + ':' + '*' * 10
        else:
            return '*' * 20
    if key in ('cookie', 'set-cookie') and 'api_key="' in value:
        start_idx = value.index('api_key="') + len('api_key="')
        end_idx = value.index('"', start_idx)
        return f'{value[0:start_idx + 2]}******{value[end_idx - 2:]}'
    return value


def client_error_exception_handler(request: Request, exc: ClientError):
    status_code = exc.status_code or 500
    if not exc.error_code:
        return PlainTextResponse(status_code=status_code, content=str(exc))
    else:
        return JSONResponse(
            status_code=status_code,
            content={
                'error_code': exc.error_code,
                'errors': exc.errors,
            },
        )


def get_correlation_id(connect_correlation_id):
    if type(connect_correlation_id) is not str:
        return None
    operation_id = connect_correlation_id[3:34]
    span_id = os.urandom(8).hex()
    return f'00-{operation_id}-{span_id}-01'
