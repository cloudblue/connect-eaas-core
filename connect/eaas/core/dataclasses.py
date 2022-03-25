from pydantic import BaseModel

from typing import Any, List, Literal, Optional, Union


class EventType:
    ASSET_PURCHASE_REQUEST_PROCESSING = 'asset_purchase_request_processing'
    ASSET_CHANGE_REQUEST_PROCESSING = 'asset_change_request_processing'
    ASSET_SUSPEND_REQUEST_PROCESSING = 'asset_suspend_request_processing'
    ASSET_RESUME_REQUEST_PROCESSING = 'asset_resume_request_processing'
    ASSET_CANCEL_REQUEST_PROCESSING = 'asset_cancel_request_processing'
    ASSET_ADJUSTMENT_REQUEST_PROCESSING = 'asset_adjustment_request_processing'
    ASSET_PURCHASE_REQUEST_VALIDATION = 'asset_purchase_request_validation'
    ASSET_CHANGE_REQUEST_VALIDATION = 'asset_change_request_validation'
    PRODUCT_ACTION_EXECUTION = 'product_action_execution'
    PRODUCT_CUSTOM_EVENT_PROCESSING = 'product_custom_event_processing'
    TIER_CONFIG_SETUP_REQUEST_PROCESSING = 'tier_config_setup_request_processing'
    TIER_CONFIG_CHANGE_REQUEST_PROCESSING = 'tier_config_change_request_processing'
    TIER_CONFIG_ADJUSTMENT_REQUEST_PROCESSING = 'tier_config_adjustment_request_processing'
    TIER_CONFIG_SETUP_REQUEST_VALIDATION = 'tier_config_setup_request_validation'
    TIER_CONFIG_CHANGE_REQUEST_VALIDATION = 'tier_config_change_request_validation'
    SCHEDULED_EXECUTION = 'scheduled_execution'
    LISTING_NEW_REQUEST_PROCESSING = 'listing_new_request_processing'
    LISTING_REMOVE_REQUEST_PROCESSING = 'listing_remove_request_processing'
    TIER_ACCOUNT_UPDATE_REQUEST_PROCESSING = 'tier_account_update_request_processing'
    USAGE_FILE_REQUEST_PROCESSING = 'usage_file_request_processing'
    PART_USAGE_FILE_REQUEST_PROCESSING = 'part_usage_file_request_processing'


class TaskCategory:
    BACKGROUND = 'background'
    INTERACTIVE = 'interactive'
    SCHEDULED = 'scheduled'


class ResultType:
    SUCCESS = 'success'
    RESCHEDULE = 'reschedule'
    SKIP = 'skip'
    RETRY = 'retry'
    FAIL = 'fail'


class MessageType:
    EXTENSION = 'extension'
    SETTINGS = 'settings'
    TASK = 'task'
    PAUSE = 'pause'
    RESUME = 'resume'
    SHUTDOWN = 'shutdown'
    # delete after stop using version 1
    CAPABILITIES = 'capabilities'
    CONFIGURATION = 'configuration'


class TaskOptions(BaseModel):
    task_id: str
    task_category: str
    result: Optional[str]
    countdown: int = 0
    runtime: float = 0.0
    output: Optional[str]
    correlation_id: Optional[str]
    reply_to: Optional[str]


class TaskInput(BaseModel):
    event_type: str
    object_id: str
    data: Optional[Any]


class TaskPayload(BaseModel):
    options: TaskOptions
    input: TaskInput


class Logging(BaseModel):
    logging_api_key: Optional[str]
    log_level: Optional[str]
    runner_log_level: Optional[str]


class Service(BaseModel):
    account_id: Optional[str]
    account_name: Optional[str]
    service_id: Optional[str]
    # delete after stop using version 1
    product_id: Optional[str]
    hub_id: Optional[str]


class SettingsPayload(BaseModel):
    variables: Optional[dict]
    # delete after stop using version 1
    environment_type: Optional[str]
    logging: Optional[Logging]
    service: Optional[Service]


class Schedulable(BaseModel):
    method: str
    name: str
    description: str


class Repository(BaseModel):
    readme_url: Optional[str]
    changelog_url: Optional[str]


class ExtensionPayload(BaseModel):
    # for version 1 'capabilities' renaming to 'event_subscriptions'
    event_subscriptions: dict
    variables: Optional[list]
    schedulables: Optional[List[Schedulable]]
    repository: Optional[Repository]
    runner_version: Optional[str]


class Message(BaseModel):
    version: Literal[1, 2] = 1
    message_type: str
    data: Union[TaskPayload, ExtensionPayload, SettingsPayload, None]


def transform_data(message_type, data):
    if message_type == MessageType.CONFIGURATION:
        message_type = MessageType.SETTINGS
        data.update(
            variables=data.get('configuration'),
            logging=Logging(**data).dict(),
            service=Service(**data).dict(),
        )
    elif message_type == MessageType.TASK:
        data.update(
            options=TaskOptions(**data).dict(),
            input=TaskInput(**data, event_type=data['task_type']).dict(),
        )
    elif message_type == MessageType.CAPABILITIES:
        message_type = MessageType.EXTENSION
        data.update(
            event_subscriptions=data.get('capabilities'),
            repository=Repository(**data).dict(),
        )

    return message_type, data


def transform_data_to_legacy(message_type, data):
    if message_type == MessageType.SETTINGS:
        message_type = MessageType.CONFIGURATION
        data.update(
            configuration=data.get('variables'),
            **data.get('logging', {}),
            **data.get('service', {}),
        )

        data.pop('logging', None)
        data.pop('service', None)
        data.pop('variables', None)

    elif message_type == MessageType.TASK:
        data.update(
            task_type=data['input']['event_type'],
            **data.get('input', {}),
            **data.get('options', {}),
        )

        data.pop('event_type', None)
        data.pop('input', None)
        data.pop('options', None)

    elif message_type == MessageType.EXTENSION:
        message_type = MessageType.CAPABILITIES
        data.update(
            capabilities=data.get('event_subscriptions'),
            **data.get('repository', {}),
        )

        data.pop('event_subscriptions', None)
        data.pop('repository', None)

    return message_type, data


def parse_message(payload):
    message_type = payload['message_type']
    version = payload.get('version', 1)
    data = payload.get('data')

    if version == 1:
        message_type, data = transform_data(message_type, data)

    if message_type not in [MessageType.TASK, MessageType.EXTENSION, MessageType.SETTINGS]:
        data = None

    return Message(version=version, message_type=message_type, data=data)
