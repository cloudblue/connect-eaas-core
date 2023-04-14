import pytest

from connect.eaas.core.enums import ResultType
from connect.eaas.core.responses import (
    BackgroundResponse,
    CustomEventResponse,
    InteractiveResponse,
    ProcessingResponse,
    ProductActionResponse,
    RowTransformationResponse,
    ScheduledExecutionResponse,
    TransformationResponse,
    ValidationResponse,
)


def test_result_ok():
    assert BackgroundResponse.done().status == ResultType.SUCCESS
    assert ScheduledExecutionResponse.done().status == ResultType.SUCCESS


@pytest.mark.parametrize(
    'response_cls',
    (
        BackgroundResponse, TransformationResponse, RowTransformationResponse,
    ),
)
def test_result_skip(response_cls):
    assert response_cls.skip().status == ResultType.SKIP


@pytest.mark.parametrize(
    'response_cls',
    (
        BackgroundResponse, TransformationResponse,
    ),
)
def test_result_skip_with_output(response_cls):
    skip = response_cls.skip('output')
    assert skip.status == ResultType.SKIP
    assert skip.output == 'output'


@pytest.mark.parametrize(
    ('countdown', 'expected'),
    (
        (0, 30),
        (-1, 30),
        (1, 30),
        (30, 30),
        (31, 31),
        (100, 100),
    ),
)
def test_result_reschedule(countdown, expected):
    r = BackgroundResponse.reschedule(countdown)

    assert r.status == ResultType.RESCHEDULE
    assert r.countdown == expected


@pytest.mark.parametrize(
    ('countdown', 'expected'),
    (
        (0, 300),
        (-1, 300),
        (1, 300),
        (30, 300),
        (300, 300),
        (600, 600),
    ),
)
def test_result_slow_reschedule(countdown, expected):
    r = BackgroundResponse.slow_process_reschedule(countdown)

    assert r.status == ResultType.RESCHEDULE
    assert r.countdown == expected


@pytest.mark.parametrize(
    'response_cls',
    (
        BackgroundResponse, InteractiveResponse,
        ScheduledExecutionResponse, TransformationResponse,
        RowTransformationResponse,
    ),
)
def test_result_fail(response_cls):
    r = response_cls.fail(output='reason of failure')

    assert r.status == ResultType.FAIL
    assert r.output == 'reason of failure'


def test_interactive_response():
    r = InteractiveResponse.done(headers={'X-Custom-Header': 'value'}, body='text')

    assert r.status == ResultType.SUCCESS
    assert r.data == {
        'http_status': 200,
        'headers': {'X-Custom-Header': 'value'},
        'body': 'text',
    }


def test_v1_responses():
    r = ProcessingResponse.done()
    assert isinstance(r, BackgroundResponse)

    r = ValidationResponse.done({'key': 'value'})
    assert isinstance(r, InteractiveResponse)
    assert r.data == {
        'http_status': 200,
        'headers': None,
        'body': {'key': 'value'},
    }

    r = ValidationResponse.fail(data={'key': 'value'}, output='invalid data')
    assert isinstance(r, InteractiveResponse)
    assert r.data == {
        'http_status': 400,
        'headers': None,
        'body': {'key': 'value'},
    }
    assert r.output == 'invalid data'

    r = CustomEventResponse.done(headers={'X-Custom-Header': 'value'}, body='text')
    assert isinstance(r, InteractiveResponse)
    assert r.data == {
        'http_status': 200,
        'headers': {'X-Custom-Header': 'value'},
        'body': 'text',
    }

    r = ProductActionResponse.done(headers={'X-Custom-Header': 'value'}, body='text')
    assert isinstance(r, InteractiveResponse)
    assert r.data == {
        'http_status': 200,
        'headers': {'X-Custom-Header': 'value'},
        'body': 'text',
    }


def test_row_transformation_respose():
    transformed_row = {'col1': 'res1', 'col2': 'res2'}
    response = RowTransformationResponse.done(transformed_row)

    assert response.status == ResultType.SUCCESS
    assert response.transformed_row == transformed_row
