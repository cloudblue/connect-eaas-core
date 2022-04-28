import copy

from connect.eaas.core.dataclasses import (
    Logging,
    LogMeta,
    Message,
    MessageType,
    parse_message,
    Repository,
    Schedulable,
    SetupRequest,
    SetupResponse,
    Task,
    TaskInput,
    TaskOptions,
    transform_data_to_v1,
)


TASK_DATA = {
    'options': {
        'task_id': 'task_id',
        'task_category': 'task_category',
        'correlation_id': 'correlation_id',
        'reply_to': 'reply_to',
    },
    'input': {
        'event_type': 'task_type',
        'object_id': 'object_id',
        'data': {'data': 'value'},
    },
    'output': {
        'result': 'result',
        'countdown': 10,
        'runtime': 3.2,
        'error': 'output',
        'data': {'data': 'value'},
    },
}
TASK_DATA_V1 = {
    'task_id': 'task_id',
    'task_category': 'task_category',
    'task_type': 'task_type',
    'object_id': 'object_id',
    'result': 'result',
    'data': {'data': 'value'},
    'countdown': 10,
    'runtime': 3.2,
    'output': 'output',
    'correlation_id': 'correlation_id',
    'reply_to': 'reply_to',
}

SETUP_REQUEST_DATA = {
    'event_subscriptions': {'test': 'data'},
    'variables': [{'foo': 'value', 'bar': 'value'}],
    'schedulables': [{'method': 'method_name', 'name': 'Name', 'description': 'Description'}],
    'repository': {
        'readme_url': 'https://read.me',
        'changelog_url': 'https://change.log',
    },
    'runner_version': '3',
}
SETUP_REQUEST_DATA_V1 = {
    'capabilities': {'test': 'data'},
    'variables': [{'foo': 'value', 'bar': 'value'}],
    'schedulables': [{'method': 'method_name', 'name': 'Name', 'description': 'Description'}],
    'readme_url': 'https://read.me',
    'changelog_url': 'https://change.log',
    'runner_version': '3',
}

SETUP_RESPONSE_DATA = {
    'variables': {'conf1': 'val1'},
    'environment_type': 'environ-type',
    'logging': {
        'logging_api_key': 'logging-token',
        'log_level': 'log-level',
        'runner_log_level': 'runner-log-level',
        'meta': {
            'account_id': 'account_id',
            'account_name': 'account_name',
            'service_id': 'service_id',
            'products': None,
            'hub_id': None,
        },
    },
}
SETUP_RESPONSE_DATA_V1 = {
    'configuration': {'conf1': 'val1'},
    'logging_api_key': 'logging-token',
    'environment_type': 'environ-type',
    'log_level': 'log-level',
    'runner_log_level': 'runner-log-level',
    'account_id': 'account_id',
    'account_name': 'account_name',
    'service_id': 'service_id',
    'product_id': None,
    'hub_id': None,
}


def test_parse_task_message():
    msg_data = {
        'version': 2,
        'message_type': 'task',
        'data': copy.deepcopy(TASK_DATA),
    }

    message = parse_message(msg_data)

    assert isinstance(message, Message)
    assert message.message_type == MessageType.TASK
    assert isinstance(message.data, Task)
    assert message.dict() == msg_data
    assert isinstance(message.data.options, TaskOptions)
    assert isinstance(message.data.input, TaskInput)


def test_parse_settings_message():
    msg_data = {
        'version': 2,
        'message_type': 'setup_response',
        'data': copy.deepcopy(SETUP_RESPONSE_DATA),
    }

    message = parse_message(msg_data)

    assert isinstance(message, Message)
    assert message.message_type == MessageType.SETUP_RESPONSE
    assert isinstance(message.data, SetupResponse)
    assert message.dict() == msg_data
    assert isinstance(message.data.logging, Logging)
    assert isinstance(message.data.logging.meta, LogMeta)


def test_parse_extension_message():
    msg_data = {
        'version': 2,
        'message_type': 'setup_request',
        'data': {
            **copy.deepcopy(SETUP_REQUEST_DATA),
            'variables': None,
            'schedulables': None,
            'runner_version': None,
        },
    }

    message = parse_message(msg_data)

    assert isinstance(message, Message)
    assert message.message_type == MessageType.SETUP_REQUEST
    assert isinstance(message.data, SetupRequest)
    assert message.dict() == msg_data
    assert isinstance(message.data.repository, Repository)


def test_parse_extension_message_with_vars_and_schedulables():
    msg_data = {
        'version': 2,
        'message_type': 'setup_request',
        'data': SETUP_REQUEST_DATA,
    }

    message = parse_message(msg_data)

    assert message.dict() == msg_data
    assert message.data.variables == msg_data['data']['variables']
    assert message.data.schedulables == msg_data['data']['schedulables']
    assert isinstance(message.data.schedulables[0], Schedulable)
    assert message.data.variables[0]['foo'] == msg_data['data']['variables'][0]['foo']
    assert message.data.variables[0]['bar'] == msg_data['data']['variables'][0]['bar']


def test_parse_pause_message():
    msg_data = {'message_type': 'pause', 'data': {}}

    message = parse_message(msg_data)

    assert isinstance(message, Message)
    assert message.message_type == MessageType.PAUSE
    assert message.data is None


def test_transform_v1_task_data():
    msg_data_v1 = {
        'message_type': 'task',
        'data': copy.deepcopy(TASK_DATA_V1),
    }

    message = parse_message(msg_data_v1)

    assert isinstance(message, Message)
    assert message.version == 1
    assert message.message_type == MessageType.TASK
    assert isinstance(message.data, Task)

    assert message.dict()['data'] == TASK_DATA


def test_transform_v1_settings_data():
    msg_data_v1 = {
        'message_type': 'configuration',
        'data': copy.deepcopy(SETUP_RESPONSE_DATA_V1),
    }

    message = parse_message(msg_data_v1)

    assert isinstance(message, Message)
    assert message.version == 1
    assert message.message_type == MessageType.SETUP_RESPONSE
    assert isinstance(message.data, SetupResponse)

    assert message.dict()['data'] == SETUP_RESPONSE_DATA


def test_transform_v1_extension_data():
    msg_data_v1 = {
        'message_type': 'capabilities',
        'data': copy.deepcopy(SETUP_REQUEST_DATA_V1),
    }

    message = parse_message(msg_data_v1)

    assert isinstance(message, Message)
    assert message.version == 1
    assert message.message_type == MessageType.SETUP_REQUEST
    assert isinstance(message.data, SetupRequest)

    assert message.dict()['data'] == SETUP_REQUEST_DATA


def test_transform_extension_data_to_legacy():
    message_type, transformed_data = transform_data_to_v1(
        message_type=MessageType.SETUP_REQUEST,
        data=copy.deepcopy(SETUP_REQUEST_DATA),
    )

    assert message_type == MessageType.CAPABILITIES
    assert transformed_data == SETUP_REQUEST_DATA_V1


def test_transform_settings_data_to_legacy():
    message_type, transformed_data = transform_data_to_v1(
        message_type=MessageType.SETUP_RESPONSE,
        data=copy.deepcopy(SETUP_RESPONSE_DATA),
    )

    assert message_type == MessageType.CONFIGURATION
    assert transformed_data == SETUP_RESPONSE_DATA_V1


def test_transform_settings_data_to_legacy_with_product():
    new_settings = copy.deepcopy(SETUP_RESPONSE_DATA)
    new_settings['logging']['meta']['products'] = ['PRD-000']
    message_type, transformed_data = transform_data_to_v1(
        message_type=MessageType.SETUP_RESPONSE,
        data=new_settings,
    )
    legacy_settings = copy.deepcopy(SETUP_RESPONSE_DATA_V1)
    legacy_settings['product_id'] = 'PRD-000'
    assert message_type == MessageType.CONFIGURATION
    assert transformed_data == legacy_settings


def test_transform_task_data_to_legacy():
    message_type, transformed_data = transform_data_to_v1(
        message_type=MessageType.TASK,
        data=copy.deepcopy(TASK_DATA),
    )

    assert transformed_data == TASK_DATA_V1
