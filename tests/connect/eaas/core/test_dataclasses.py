from connect.eaas.core.dataclasses import (
    ExtensionPayload,
    Logging,
    Message,
    MessageType,
    parse_message,
    Repository,
    Schedulable,
    Service,
    SettingsPayload,
    TaskInput,
    TaskOptions,
    TaskPayload,
    transform_data_to_legacy,
)


TASK_DATA = {
    'options': {
        'task_id': 'task_id',
        'task_category': 'task_category',
        'result': 'result',
        'countdown': 10,
        'output': 'output',
        'correlation_id': 'correlation_id',
        'reply_to': 'reply_to',
    },
    'input': {
        'event_type': 'task_type',
        'object_id': 'object_id',
        'data': {'data': 'value'},
    },
}
TASK_DATA_LEGACY = {
    'task_id': 'task_id',
    'task_category': 'task_category',
    'task_type': 'task_type',
    'object_id': 'object_id',
    'result': 'result',
    'data': {'data': 'value'},
    'countdown': 10,
    'output': 'output',
    'correlation_id': 'correlation_id',
    'reply_to': 'reply_to',
}

EXTENSION_DATA = {
    'event_subscriptions': {'test': 'data'},
    'variables': [{'foo': 'value', 'bar': 'value'}],
    'schedulables': [{'method': 'method_name', 'name': 'Name', 'description': 'Description'}],
    'repository': {
        'readme_url': 'https://read.me',
        'changelog_url': 'https://change.log',
    },
    'runner_version': '3',
}
EXTENSION_DATA_LEGACY = {
    'capabilities': {'test': 'data'},
    'variables': [{'foo': 'value', 'bar': 'value'}],
    'schedulables': [{'method': 'method_name', 'name': 'Name', 'description': 'Description'}],
    'readme_url': 'https://read.me',
    'changelog_url': 'https://change.log',
    'runner_version': '3',
}

SETTINGS_DATA = {
    'variables': {'conf1': 'val1'},
    'environment_type': 'environ-type',
    'logging': {
        'logging_api_key': 'logging-token',
        'log_level': 'log-level',
        'runner_log_level': 'runner-log-level',
    },
    'service': {
        'account_id': 'account_id',
        'account_name': 'account_name',
        'service_id': 'service_id',
        'product_id': None,
        'hub_id': None,
    },
}
SETTNIGS_DATA_LEGACY = {
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
        'data': TASK_DATA,
    }

    message = parse_message(msg_data)

    assert isinstance(message, Message)
    assert message.message_type == MessageType.TASK
    assert isinstance(message.data, TaskPayload)
    assert message.dict() == msg_data
    assert isinstance(message.data.options, TaskOptions)
    assert isinstance(message.data.input, TaskInput)


def test_parse_settings_message():
    msg_data = {
        'version': 2,
        'message_type': 'settings',
        'data': SETTINGS_DATA,
    }

    message = parse_message(msg_data)

    assert isinstance(message, Message)
    assert message.message_type == MessageType.SETTINGS
    assert isinstance(message.data, SettingsPayload)
    assert message.dict() == msg_data
    assert isinstance(message.data.logging, Logging)
    assert isinstance(message.data.service, Service)


def test_parse_extension_message():
    msg_data = {
        'version': 2,
        'message_type': 'extension',
        'data': {
            **EXTENSION_DATA,
            'variables': None,
            'schedulables': None,
            'runner_version': None,
        },
    }

    message = parse_message(msg_data)

    assert isinstance(message, Message)
    assert message.message_type == MessageType.EXTENSION
    assert isinstance(message.data, ExtensionPayload)
    assert message.dict() == msg_data
    assert isinstance(message.data.repository, Repository)


def test_parse_extension_message_with_vars_and_schedulables():
    msg_data = {
        'version': 2,
        'message_type': 'extension',
        'data': EXTENSION_DATA,
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
        'data': {**TASK_DATA_LEGACY},
    }

    message = parse_message(msg_data_v1)

    assert isinstance(message, Message)
    assert message.version == 1
    assert message.message_type == MessageType.TASK
    assert isinstance(message.data, TaskPayload)

    assert message.dict()['data'] == TASK_DATA


def test_transform_v1_settings_data():
    msg_data_v1 = {
        'message_type': 'configuration',
        'data': {**SETTNIGS_DATA_LEGACY},
    }

    message = parse_message(msg_data_v1)

    assert isinstance(message, Message)
    assert message.version == 1
    assert message.message_type == MessageType.SETTINGS
    assert isinstance(message.data, SettingsPayload)

    assert message.dict()['data'] == SETTINGS_DATA


def test_transform_v1_extension_data():
    msg_data_v1 = {
        'message_type': 'capabilities',
        'data': {**EXTENSION_DATA_LEGACY},
    }

    message = parse_message(msg_data_v1)

    assert isinstance(message, Message)
    assert message.version == 1
    assert message.message_type == MessageType.EXTENSION
    assert isinstance(message.data, ExtensionPayload)

    assert message.dict()['data'] == EXTENSION_DATA


def test_transform_extension_data_to_legacy():
    message_type, transformed_data = transform_data_to_legacy(
        message_type=MessageType.EXTENSION,
        data={**EXTENSION_DATA},
    )

    assert message_type == MessageType.CAPABILITIES
    assert transformed_data == EXTENSION_DATA_LEGACY


def test_transform_settings_data_to_legacy():
    message_type, transformed_data = transform_data_to_legacy(
        message_type=MessageType.SETTINGS,
        data={**SETTINGS_DATA},
    )

    assert message_type == MessageType.CONFIGURATION
    assert transformed_data == SETTNIGS_DATA_LEGACY


def test_transform_task_data_to_legacy():
    message_type, transformed_data = transform_data_to_legacy(
        message_type=MessageType.TASK,
        data={**TASK_DATA},
    )

    assert transformed_data == TASK_DATA_LEGACY
