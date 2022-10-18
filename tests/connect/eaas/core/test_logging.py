import logging

import pytest
from requests.models import Response
from urllib3.response import HTTPResponse

from connect.eaas.core.logging import ExtensionLogHandler, RequestLogger


def test_extension_log_handler():

    handler = ExtensionLogHandler('api_key', default_extra_fields={'field': 'value'})
    assert handler.logzio_sender.token == 'api_key'
    extra_fields = handler.extra_fields(logging.LogRecord(
        'name',
        logging.INFO,
        'path',
        10,
        'message',
        None,
        None,
    ))
    assert extra_fields['field'] == 'value'


def test_request_logger_request(caplog):
    rl = RequestLogger(logging.getLogger('eaas.runner.extension'))

    with caplog.at_level(logging.DEBUG):
        rl.log_request('POST', 'https://example.com', {})

    assert '\n'.join(
        [
            '--- HTTP Request ---',
            "POST https://example.com ",
            '',
        ],
    ) == caplog.records[0].message


def test_request_logger_request_params(caplog):
    rl = RequestLogger(logging.getLogger('eaas.runner.extension'))

    with caplog.at_level(logging.DEBUG):
        rl.log_request('POST', 'https://example.com', {'params': {'a': 'va'}})

    assert '\n'.join(
        [
            '--- HTTP Request ---',
            "POST https://example.com?a=va ",
            '',
        ],
    ) == caplog.records[0].message


def test_request_logger_request_with_qs(caplog):
    rl = RequestLogger(logging.getLogger('eaas.runner.extension'))

    with caplog.at_level(logging.DEBUG):
        rl.log_request('GET', 'https://example.com?queryparam=value', {})

    assert '\n'.join(
        [
            '--- HTTP Request ---',
            "GET https://example.com?queryparam=value ",
            '',
        ],
    ) == caplog.records[0].message


@pytest.mark.parametrize(
    ('authorization', 'expected_auth'),
    (
        ('ApiKey SU-000:**********', 'ApiKey SU-000:**********'),
        ('custom_token', '*' * 20),
    ),
)
def test_request_logger_request_with_headers(caplog, authorization, expected_auth):
    rl = RequestLogger(logging.getLogger('eaas.runner.extension'))

    headers = {
        'Authorization': authorization,
    }

    with caplog.at_level(logging.DEBUG):
        rl.log_request('GET', 'https://example.com', {'headers': headers})

    assert '\n'.join(
        [
            '--- HTTP Request ---',
            "GET https://example.com ",
            f'Authorization: {expected_auth}',
            '',
        ],
    ) == caplog.records[0].message


@pytest.mark.parametrize(
    ('cookie', 'expected_cookie'),
    (
        (
            '_ga=wathever; api_key="test@example.com:abcdefg"; _gid=whatever',
            '_ga=wathever; api_key="te******fg"; _gid=whatever',
        ),
        (
            '_ga=wathever; _gid=whatever',
            '_ga=wathever; _gid=whatever',
        ),
    ),
)
def test_request_logger_request_with_cookie(caplog, cookie, expected_cookie):
    rl = RequestLogger(logging.getLogger('eaas.runner.extension'))

    headers = {
        'Cookie': cookie,
    }

    with caplog.at_level(logging.DEBUG):
        rl.log_request('GET', 'https://example.com', {'headers': headers})

    assert '\n'.join(
        [
            '--- HTTP Request ---',
            "GET https://example.com ",
            f'Cookie: {expected_cookie}',
            '',
        ],
    ) == caplog.records[0].message


def test_request_logger_request_with_json_body(caplog):
    rl = RequestLogger(logging.getLogger('eaas.runner.extension'))

    json = {
        'test': 'data',
    }

    with caplog.at_level(logging.DEBUG):
        rl.log_request('GET', 'https://example.com', {'json': json})

    assert '\n'.join(
        [
            '--- HTTP Request ---',
            "GET https://example.com ",
            '{',
            '    "test": "data"',
            '}',
            '',
        ],
    ) == caplog.records[0].message


def test_request_logger_response(caplog):
    rl = RequestLogger(logging.getLogger('eaas.runner.extension'))

    rsp = Response()
    rsp.raw = HTTPResponse()

    rsp.status_code = 200
    rsp.raw.reason = 'OK'

    with caplog.at_level(logging.DEBUG):
        rl.log_response(rsp)

    assert '\n'.join(
        [
            '--- HTTP Response ---',
            '200 OK',
            '',
        ],
    ) == caplog.records[0].message

    rsp = Response()
    rsp.status_code = 200
    rsp.reason_phrase = 'OK'

    with caplog.at_level(logging.DEBUG):
        rl.log_response(rsp)

    assert '\n'.join(
        [
            '--- HTTP Response ---',
            '200 OK',
            '',
        ],
    ) == caplog.records[0].message


def test_request_logger_response_json(mocker, caplog):
    json = {'id': 'XX-1234', 'name': 'XXX'}
    mocker.patch('requests.models.Response.json', return_value=json)

    rl = RequestLogger(logging.getLogger('eaas.runner.extension'))

    rsp = Response()
    rsp.raw = HTTPResponse()
    rsp.headers = {
        'Content-Type': 'application/json',
        'Set-Cookie': (
            'api_key="test@example.com:abcdefg"; '
            'expires=Wed, 19 Oct 2022 06:56:08 GMT; HttpOnly;'
        ),
    }
    rsp.status_code = 200
    rsp.raw.reason = 'OK'

    with caplog.at_level(logging.DEBUG):
        rl.log_response(rsp)
    assert '\n'.join(
        [
            '--- HTTP Response ---',
            '200 OK',
            'Content-Type: application/json',
            'Set-Cookie: api_key="te******fg"; expires=Wed, 19 Oct 2022 06:56:08 GMT; HttpOnly;',
            '{',
            '    "id": "XX-1234",',
            '    "name": "XXX"',
            '}',
            '',
        ],
    ) == caplog.records[0].message
