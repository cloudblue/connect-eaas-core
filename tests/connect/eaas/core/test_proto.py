import copy

import pytest

from connect.eaas.core.proto import (
    EventDefinition,
    HttpRequest,
    Logging,
    LogMeta,
    Message,
    MessageType,
    Repository,
    Schedulable,
    SetupRequest,
    SetupResponse,
    Task,
    TaskInput,
    TaskOptions,
    Transformation,
    WebTaskOptions,
)


TASK_DATA = {
    'options': {
        'task_id': 'task_id',
        'task_category': 'task_category',
        'correlation_id': 'correlation_id',
        'reply_to': 'reply_to',
        'api_key': 'api_key',
        'installation_id': 'installation_id',
        'connect_correlation_id': 'connect_correlation_id',
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
        'message': 'output',
        'data': {'data': 'value'},
    },
    'model_type': 'task',
}


TASK_INPUT_DATA = {
    'options': {
        'task_id': 'task_id',
        'task_category': 'task_category',
        'correlation_id': 'correlation_id',
        'reply_to': 'reply_to',
        'connect_correlation_id': 'connect_correlation_id',
    },
    'input': {
        'event_type': 'task_type',
        'object_id': 'object_id',
        'data': {'data': 'value'},
    },
    'model_type': 'task',
}

TASK_INPUT_DATA_V1 = {
    'task_id': 'task_id',
    'task_category': 'task_category',
    'task_type': 'task_type',
    'object_id': 'object_id',
    'data': {'data': 'value'},
    'correlation_id': 'correlation_id',
    'reply_to': 'reply_to',
}


TASK_OUTPUT_DATA = {
    'options': {
        'task_id': 'task_id',
        'task_category': 'task_category',
        'correlation_id': 'correlation_id',
        'reply_to': 'reply_to',
        'api_key': None,
        'installation_id': None,
        'connect_correlation_id': None,
    },
    'input': {
        'event_type': 'task_type',
        'object_id': 'object_id',
        'data': None,
    },
    'output': {
        'result': 'result',
        'countdown': 10,
        'runtime': 3.2,
        'message': 'output',
        'data': {'output_data': 'value'},
    },
    'model_type': 'task',
}

TASK_OUTPUT_DATA_V1 = {
    'task_id': 'task_id',
    'task_category': 'task_category',
    'task_type': 'task_type',
    'object_id': 'object_id',
    'result': 'result',
    'data': {'output_data': 'value'},
    'countdown': 10,
    'runtime': 3.2,
    'output': 'output',
    'correlation_id': 'correlation_id',
    'reply_to': 'reply_to',
}


SETUP_REQUEST_DATA = {
    'ui_modules': None,
    'icon': None,
    'audience': None,
    'event_subscriptions': {'test': 'data'},
    'variables': [{'foo': 'value', 'bar': 'value'}],
    'schedulables': [{'method': 'method_name', 'name': 'Name', 'description': 'Description'}],
    'anvil_callables': [
        {'method': 'method_name', 'summary': 'Summary', 'description': 'Description'},
    ],
    'transformations': [{
        'name': 'Name',
        'description': 'Description',
        'edit_dialog_ui': '/static/edit.html',
        'class_fqn': 'package.ABC',
    }],
    'repository': {
        'readme_url': 'https://read.me',
        'changelog_url': 'https://change.log',
    },
    'runner_version': '3',
    'model_type': 'setup_request',
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
    'variables': [{'name': 'conf1', 'value': 'val1', 'secure': False}],
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
    'event_definitions': None,
    'model_type': 'setup_response',
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

SETUP_RESPONSE_DATA_V1_NO_META = {
    'configuration': {'conf1': 'val1'},
    'logging_api_key': 'logging-token',
    'environment_type': 'environ-type',
    'log_level': 'log-level',
    'runner_log_level': 'runner-log-level',
    'account_id': None,
    'account_name': None,
    'service_id': None,
    'product_id': None,
    'hub_id': None,
}


def test_deserialize_task_message():
    msg_data = {
        'version': 2,
        'message_type': 'task',
        'data': copy.deepcopy(TASK_DATA),
    }

    message = Message.deserialize(msg_data)
    assert isinstance(message, Message)
    assert message.message_type == MessageType.TASK
    assert isinstance(message.data, Task)
    assert message.dict() == msg_data
    assert isinstance(message.data.options, TaskOptions)
    assert isinstance(message.data.input, TaskInput)


def test_deserialize_setup_response_message():
    msg_data = {
        'version': 2,
        'message_type': 'setup_response',
        'data': copy.deepcopy(SETUP_RESPONSE_DATA),
    }

    message = Message.deserialize(msg_data)

    assert isinstance(message, Message)
    assert message.message_type == MessageType.SETUP_RESPONSE
    assert isinstance(message.data, SetupResponse)
    assert message.dict() == msg_data
    assert isinstance(message.data.logging, Logging)
    assert isinstance(message.data.logging.meta, LogMeta)


def test_deserialize_setup_request_message():
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

    message = Message.deserialize(msg_data)

    assert isinstance(message, Message)
    assert message.message_type == MessageType.SETUP_REQUEST
    assert isinstance(message.data, SetupRequest)
    assert message.dict() == msg_data
    assert isinstance(message.data.repository, Repository)


def test_deserialize_setup_request_message_with_vars_and_schedulables():
    msg_data = {
        'version': 2,
        'message_type': 'setup_request',
        'data': SETUP_REQUEST_DATA,
    }

    message = Message.deserialize(msg_data)

    assert message.dict() == msg_data
    assert message.data.variables == msg_data['data']['variables']
    assert message.data.schedulables == msg_data['data']['schedulables']
    assert isinstance(message.data.schedulables[0], Schedulable)
    assert message.data.variables[0]['foo'] == msg_data['data']['variables'][0]['foo']
    assert message.data.variables[0]['bar'] == msg_data['data']['variables'][0]['bar']
    assert message.data.transformations == msg_data['data']['transformations']
    assert isinstance(message.data.transformations[0], Transformation)


def test_deserialize_v1_shutdown():
    msg_data_v1 = {
        'message_type': MessageType.SHUTDOWN,
    }

    message = Message.deserialize(msg_data_v1)

    assert isinstance(message, Message)
    assert message.version == 1
    assert message.message_type == MessageType.SHUTDOWN


def test_serialize_v1_shutdown():
    msg = Message(version=1, message_type=MessageType.SHUTDOWN)

    serialized = msg.serialize(1)
    assert serialized['message_type'] == MessageType.SHUTDOWN


def test_serialize_v1_task_data():
    msg_data_v1 = {
        'message_type': MessageType.TASK,
        'data': copy.deepcopy(TASK_OUTPUT_DATA_V1),
    }

    message = Message.deserialize(msg_data_v1)

    assert isinstance(message, Message)
    assert message.version == 1
    assert message.message_type == MessageType.TASK
    assert isinstance(message.data, Task)

    assert message.dict()['data'] == TASK_OUTPUT_DATA


def test_deserialize_v1_setup_response_data():
    msg_data_v1 = {
        'message_type': MessageType.CONFIGURATION,
        'data': copy.deepcopy(SETUP_RESPONSE_DATA_V1),
    }

    message = Message.deserialize(msg_data_v1)

    assert isinstance(message, Message)
    assert message.version == 1
    assert message.message_type == MessageType.SETUP_RESPONSE
    assert isinstance(message.data, SetupResponse)

    assert message.dict()['data'] == SETUP_RESPONSE_DATA


def test_deserialize_v1_setup_request_data():
    msg_data_v1 = {
        'message_type': 'capabilities',
        'data': copy.deepcopy(SETUP_REQUEST_DATA_V1),
    }

    message = Message.deserialize(msg_data_v1)

    expected_data = copy.deepcopy(SETUP_REQUEST_DATA)
    expected_data['anvil_callables'] = None
    expected_data['transformations'] = None

    assert isinstance(message, Message)
    assert message.version == 1
    assert message.message_type == MessageType.SETUP_REQUEST
    assert isinstance(message.data, SetupRequest)

    assert message.dict()['data'] == expected_data


def test_serialize_setup_request_data_to_v1():
    msg = Message(
        version=2,
        message_type=MessageType.SETUP_REQUEST,
        data=copy.deepcopy(SETUP_REQUEST_DATA),
    )

    v1 = msg.serialize(1)

    assert v1['message_type'] == MessageType.CAPABILITIES
    assert v1['data'] == SETUP_REQUEST_DATA_V1


def test_serialize_setup_response_data_to_v1():
    msg = Message(
        version=2,
        message_type=MessageType.SETUP_RESPONSE,
        data=copy.deepcopy(SETUP_RESPONSE_DATA),
    )

    v1 = msg.serialize(1)

    assert v1['message_type'] == MessageType.CONFIGURATION
    assert v1['data'] == SETUP_RESPONSE_DATA_V1


def test_serialize_setup_response_data_to_v1_no_meta():
    data = copy.deepcopy(SETUP_RESPONSE_DATA)
    data['logging'].pop('meta')
    msg = Message(
        version=2,
        message_type=MessageType.SETUP_RESPONSE,
        data=data,
    )

    v1 = msg.serialize(1)

    assert v1['message_type'] == MessageType.CONFIGURATION
    assert v1['data'] == SETUP_RESPONSE_DATA_V1_NO_META


@pytest.mark.parametrize(
    ('products', 'expected_product_id'),
    (
        (['PRD-000'], 'PRD-000'),
        (['PRD-000', 'PRD-001'], 'PRD-000,PRD-001'),
    ),
)
def test_serialize_setup_response_data_to_v1_with_product(products, expected_product_id):
    new_settings = copy.deepcopy(SETUP_RESPONSE_DATA)
    new_settings['logging']['meta']['products'] = products

    msg = Message(
        version=2,
        message_type=MessageType.SETUP_RESPONSE,
        data=new_settings,
    )

    v1 = msg.serialize(1)

    legacy_settings = copy.deepcopy(SETUP_RESPONSE_DATA_V1)
    legacy_settings['product_id'] = expected_product_id
    assert v1['message_type'] == MessageType.CONFIGURATION
    assert v1['data'] == legacy_settings


def test_serialize_task_data_to_v1():
    msg = Message(
        version=2,
        message_type=MessageType.TASK,
        data=TASK_INPUT_DATA,
    )

    v1 = msg.serialize(1)

    assert v1['message_type'] == MessageType.TASK
    assert v1['data'] == TASK_INPUT_DATA_V1


@pytest.mark.parametrize(
    ('msg_type', 'data'),
    (
        (MessageType.SETUP_REQUEST, SETUP_REQUEST_DATA),
        (MessageType.SETUP_RESPONSE, SETUP_RESPONSE_DATA),
        (MessageType.TASK, TASK_DATA),
        (MessageType.SHUTDOWN, None),
    ),
)
def test_serialize_v2(msg_type, data):
    msg = Message(version=2, message_type=msg_type, data=data)

    serialized = msg.serialize()

    assert serialized['version'] == 2
    assert serialized['message_type'] == msg_type
    assert serialized['data'] == data


def test_serialize_setup_response_with_events_definitions():
    data = copy.deepcopy(SETUP_RESPONSE_DATA)
    data['event_definitions'] = [
        {
            'event_type': 'event_type',
            'api_resource_endpoint': 'api_resource_endpoint',
            'api_collection_endpoint': 'api_collection_endpoint',
            'api_collection_filter': 'api_collection_filter',
        },
    ]
    msg = Message(
        version=2,
        message_type=MessageType.SETUP_RESPONSE,
        data=data,
    )

    assert isinstance(msg.data.event_definitions[0], EventDefinition)

    serialized = msg.serialize()

    assert serialized['version'] == 2
    assert serialized['message_type'] == MessageType.SETUP_RESPONSE
    assert serialized['data'] == data


def test_obfuscate_task_options():
    task_options = TaskOptions(
        task_id='task_id',
        task_category='task_category',
        api_key='This is my API key',
    )
    assert next(filter(
        lambda x: x[0] == 'api_key', task_options.__repr_args__(),
    ))[1] == 'Th******ey'


def test_obfuscate_logging():
    logging = Logging(
        logging_api_key='This is my API key',
    )
    assert next(filter(
        lambda x: x[0] == 'logging_api_key', logging.__repr_args__(),
    ))[1] == 'Th******ey'


def test_obfuscate_setup_response():
    setup_response = SetupResponse(
        variables=[
            {
                'name': 'SECURE_VAR',
                'value': 'abcdefgh',
                'secure': True,
            },
            {
                'name': 'UNSECURE_VAR',
                'value': 'qwerty',
                'secure': False,
            },
        ],
    )
    assert next(filter(
        lambda x: x[0] == 'variables', setup_response.__repr_args__(),
    ))[1] == [
        {
            'name': 'SECURE_VAR',
            'value': 'ab******gh',
            'secure': True,
        },
        {
            'name': 'UNSECURE_VAR',
            'value': 'qwerty',
            'secure': False,
        },
    ]


def test_obfuscate_setup_request():
    setup_request = SetupRequest(variables=[{'VAR1': 'VAL1'}])
    assert next(filter(lambda x: x[0] == 'variables', setup_request.__repr_args__()))[1] == '******'


def test_obfuscate_http_request():
    http_request = HttpRequest(
        method='method',
        url='url',
        headers={'Authorization': 'ApiKey SU-0000:abcdef'},
    )
    assert next(filter(lambda x: x[0] == 'headers', http_request.__repr_args__()))[1] == {
        'Authorization': 'ApiKey SU-0000:**********',
    }


def test_obfuscate_webtask_options():
    webtask_options = WebTaskOptions(
        correlation_id='correlation_id',
        reply_to='reply_to',
        api_key='This is my API key',
    )
    assert next(filter(
        lambda x: x[0] == 'api_key', webtask_options.__repr_args__(),
    ))[1] == 'Th******ey'
