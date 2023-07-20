from typing import (
    Any,
    List,
    Literal,
    Optional,
    Union,
)

from pydantic import BaseModel as PydanticBaseModel, Field
from pydantic.utils import DUNDER_ATTRIBUTES

from connect.eaas.core.utils import obfuscate_header


class BaseModel(PydanticBaseModel):

    def get_sensitive_fields(self):
        return []  # pragma: no cover

    def __obfuscate_args__(self, k, v):
        if k not in self.get_sensitive_fields() or not v:
            return k, v

        if hasattr(self, f'obfuscate_{k}'):
            return getattr(self, f'obfuscate_{k}')(k, v)

        if isinstance(v, str):
            return k, f'{v[0:2]}******{v[-2:]}'

        if isinstance(v, (list, dict)):
            return k, '******'

        return k, v  # pragma: no cover

    def __repr_args__(self):
        return [
            self.__obfuscate_args__(k, v)
            for k, v in self.__dict__.items()
            if (
                k not in DUNDER_ATTRIBUTES
                and (k not in self.__fields__ or self.__fields__[k].field_info.repr)
            )
        ]


class MessageType:
    SETUP_REQUEST = 'setup_request'
    SETUP_RESPONSE = 'setup_response'
    WEB_SETUP_REQUEST = 'web_setup_request'
    WEB_SETUP_RESPONSE = 'web_setup_response'
    WEB_TASK = 'web_task'
    TASK = 'task'
    SHUTDOWN = 'shutdown'
    # delete after stop using version 1
    CAPABILITIES = 'capabilities'
    CONFIGURATION = 'configuration'


class TaskOptions(BaseModel):
    task_id: str
    task_category: str
    correlation_id: Optional[str]
    reply_to: Optional[str]
    api_key: Optional[str]
    installation_id: Optional[str]
    connect_correlation_id: Optional[str]

    def get_sensitive_fields(self):
        return ['api_key']


class TaskOutput(BaseModel):
    result: str
    data: Optional[Any]
    countdown: int = 0
    runtime: float = 0.0
    message: Optional[str]


class TaskInput(BaseModel):
    event_type: str
    object_id: str
    data: Optional[Any]


class Task(BaseModel):
    options: TaskOptions
    input: TaskInput
    output: Optional[TaskOutput]
    model_type: Literal['task'] = 'task'


class LogMeta(BaseModel):
    account_id: Optional[str]
    account_name: Optional[str]
    service_id: Optional[str]
    # delete after stop using version 1
    products: Optional[List[str]]
    hub_id: Optional[str]


class Logging(BaseModel):
    logging_api_key: Optional[str]
    log_level: Optional[str]
    runner_log_level: Optional[str]
    meta: Optional[LogMeta]

    def get_sensitive_fields(self):
        return ['logging_api_key']


class EventDefinition(BaseModel):
    event_type: str
    api_resource_endpoint: str
    api_collection_endpoint: str
    api_collection_filter: str


class SetupResponse(BaseModel):
    variables: Optional[list]
    # delete after stop using version 1
    environment_type: Optional[str]
    logging: Optional[Logging]
    event_definitions: Optional[List[EventDefinition]]
    environment_runtime: Optional[str]
    environment_hostname: Optional[str]
    environment_domain: Optional[str]
    model_type: Literal['setup_response'] = 'setup_response'

    def get_sensitive_fields(self):
        return ['variables']

    def obfuscate_variables(self, k, v):
        return k, [
            {
                'name': item['name'],
                'value': (
                    f'{item["value"][0:2]}******{item["value"][-2:]}'
                    if item['secure'] else item['value']
                ),
                'secure': item['secure'],
            }
            for item in v
        ]


class Schedulable(BaseModel):
    method: str
    name: str
    description: str


class Transformation(BaseModel):
    method: str
    name: str
    description: str
    edit_dialog_ui: str
    manual: bool = False


class Repository(BaseModel):
    readme_url: Optional[str]
    changelog_url: Optional[str]


class SetupRequest(BaseModel):
    # for version 1 'capabilities' renaming to 'event_subscriptions'
    event_subscriptions: Optional[dict]
    ui_modules: Optional[dict]
    icon: Optional[str]
    variables: Optional[list]
    schedulables: Optional[List[Schedulable]]
    anvil_callables: Optional[list]
    transformations: Optional[List[Transformation]]
    audience: Optional[List[Literal['vendor', 'distributor', 'reseller']]]
    repository: Optional[Repository]
    runner_version: Optional[str]
    proxied_connect_api: Optional[Union[list, dict]]
    model_type: Literal['setup_request'] = 'setup_request'

    def get_sensitive_fields(self):
        return ['variables']


class HttpResponse(BaseModel):
    status: int
    headers: dict
    content: Optional[Any]


class HttpRequest(BaseModel):
    method: str
    url: str
    headers: dict
    content: Optional[Any]

    def get_sensitive_fields(self):
        return ['headers']

    def obfuscate_headers(self, k, v):
        return k, {key: obfuscate_header(key.lower(), value) for key, value in v.items()}


class WebTaskOptions(BaseModel):
    correlation_id: str
    reply_to: str
    api_key: Optional[str]
    installation_id: Optional[str]
    tier_account_id: Optional[str]
    connect_correlation_id: Optional[str]
    user_id: Optional[str]
    account_id: Optional[str]
    account_role: Optional[str]
    call_type: Optional[Literal['admin', 'user']]
    call_source: Optional[Literal['ui', 'api']]

    def get_sensitive_fields(self):
        return ['api_key']


class WebTask(BaseModel):
    options: WebTaskOptions
    request: Optional[HttpRequest]
    response: Optional[HttpResponse]
    model_type: Literal['web_task'] = 'web_task'


class Message(BaseModel):
    version: Literal[1, 2] = 1
    message_type: str
    data: Union[
        WebTask, Task,
        SetupRequest, SetupResponse,
        None,
    ] = Field(discriminator='model_type')

    def serialize(self, protocol_version=2):
        if protocol_version == 2:
            return self.dict()

        if self.message_type == MessageType.SETUP_REQUEST:
            return {
                'message_type': MessageType.CAPABILITIES,
                'data': {
                    'capabilities': self.data.event_subscriptions,
                    'variables': self.data.variables,
                    'schedulables': [
                        {
                            'method': schedulable.method,
                            'name': schedulable.name,
                            'description': schedulable.description,
                        }
                        for schedulable in (self.data.schedulables or [])
                    ],
                    'readme_url': self.data.repository.readme_url,
                    'changelog_url': self.data.repository.changelog_url,
                    'runner_version': self.data.runner_version,
                },
            }
        if self.message_type == MessageType.SETUP_RESPONSE:
            if not self.data.logging.meta:
                self.data.logging.meta = LogMeta()
            return {
                'message_type': MessageType.CONFIGURATION,
                'data': {
                    'configuration': {item['name']: item['value'] for item in self.data.variables},
                    'environment_type': self.data.environment_type,
                    'logging_api_key': self.data.logging.logging_api_key,
                    'log_level': self.data.logging.log_level,
                    'runner_log_level': self.data.logging.runner_log_level,
                    'account_id': self.data.logging.meta.account_id,
                    'account_name': self.data.logging.meta.account_name,
                    'service_id': self.data.logging.meta.service_id,
                    'product_id': (
                        ','.join(self.data.logging.meta.products)
                        if self.data.logging.meta.products
                        else None
                    ),
                    'hub_id': self.data.logging.meta.hub_id,
                },
            }

        if self.message_type == MessageType.TASK:
            return {
                'message_type': self.message_type,
                'data': {
                    'task_id': self.data.options.task_id,
                    'task_category': self.data.options.task_category,
                    'correlation_id': self.data.options.correlation_id,
                    'reply_to': self.data.options.reply_to,
                    'task_type': self.data.input.event_type,
                    'object_id': self.data.input.object_id,
                    'data': self.data.input.data,
                },
            }
        return {
            'message_type': self.message_type,
        }

    @classmethod
    def deserialize(cls, raw):
        version = raw.get('version', 1)

        message_type = raw['message_type']
        raw_data = raw.get('data')

        if version == 2:
            return cls(**raw)

        if message_type == MessageType.CAPABILITIES:
            return cls(
                version=version,
                message_type=MessageType.SETUP_REQUEST,
                data=SetupRequest(
                    event_subscriptions=raw_data['capabilities'],
                    runner_version=raw_data.get('runner_version'),
                    variables=raw_data.get('variables'),
                    schedulables=[
                        Schedulable(**schedulable)
                        for schedulable in (raw_data.get('schedulables', []) or [])
                    ],
                    repository=Repository(
                        readme_url=raw_data.get('readme_url'),
                        changelog_url=raw_data.get('changelog_url'),
                    ),
                ),
            )
        if message_type == MessageType.CONFIGURATION:
            return cls(
                version=version,
                message_type=MessageType.SETUP_RESPONSE,
                data=SetupResponse(
                    environment_type=raw_data.get('environment_type'),
                    variables=[
                        {'name': name, 'value': value, 'secure': False}
                        for name, value in raw_data.get('configuration', {}).items()
                    ],
                    logging=Logging(
                        logging_api_key=raw_data.get('logging_api_key'),
                        log_level=raw_data.get('log_level'),
                        runner_log_level=raw_data.get('runner_log_level'),
                        meta=LogMeta(
                            account_id=raw_data.get('account_id'),
                            account_name=raw_data.get('account_name'),
                            service_id=raw_data.get('service_id'),
                            products=[raw_data['product_id']] if 'product_id' in raw else None,
                            hub_id=raw_data.get('hub_id'),
                        ),
                    ),
                ),
            )
        if message_type == MessageType.TASK:
            return cls(
                version=version,
                message_type=message_type,
                data=Task(
                    options=TaskOptions(
                        task_id=raw_data['task_id'],
                        task_category=raw_data['task_category'],
                        correlation_id=raw_data.get('correlation_id'),
                        reply_to=raw_data.get('reply_to'),
                    ),
                    input=TaskInput(
                        event_type=raw_data['task_type'],
                        object_id=raw_data['object_id'],
                    ),
                    output=TaskOutput(
                        result=raw_data['result'],
                        data=raw_data.get('data'),
                        countdown=raw_data['countdown'],
                        runtime=raw_data.get('runtime'),
                        message=raw_data.get('output'),
                    ),
                ),
            )

        return cls(version=version, message_type=message_type)
