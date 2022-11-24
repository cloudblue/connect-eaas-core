The CloudBlue Connect release 26 introduces the version 2 of EaaS SDK specifications. The 26th release of the Connect platform support both version 1 and version 2 of EaaS SDK specifications. Note, however, that the version 1 support will be stopped in future releases.

The following article will help you to migrate from SDK version 1 specification to 
SDK version 2.


## Migrate `pyproject.toml`

### Events application setuptools entrypoint name

In SDK version 1, entrypoint names are used to load classes with event handlers that are collectively called an `extension`. 
The following example demonstrates this concept: 

``` toml title="EaaS SDK v1" hl_lines="3"
...
[tool.poetry.plugins."connect.eaas.ext"]
"extension" = "mypkg.extension:MyExtension"
...
```

In SDK version 2, `extension` is deprecated in favour of `eventapp` as demonstrated below:

``` toml title="EaaS SDK v2" hl_lines="3"
...
[tool.poetry.plugins."connect.eaas.ext"]
"eventsapp" = "mypkg.extension:MyExtension"
...
```

### EaaS SDK dependency

In version 1, an extension project depends on the `connect-extension-runner` library:

``` toml title="EaaS SDK v1" hl_lines="4"
...
[tool.poetry.dependencies]
python = "^3.8"
connect-extension-runner = "24.*"
...
```

In version 2, it depends on the `connect-eaas-core` library:

``` toml title="EaaS SDK v2" hl_lines="4"
...
[tool.poetry.dependencies]
python = "^3.8"
connect-eaas-core = "26.*"
...
```

## Migrate python code

### Base class

Version 1 includes the following base class for Events Applications:

``` python title="EaaS SDK v1" hl_lines="1 4"
from connect.eaas.extension import Extension


class MyExtension(Extension):
    pass
```


In version 2, the name of the base class changes from `Extension` to `EventsApplicationBase`:

``` python title="EaaS SDK v2" hl_lines="1 4"
from connect.eaas.core.extension import EventsApplicationBase


class MyEventsApplication(EventsApplicationBase):
    pass
```

### Response classes

In SDK version 1, the response classes are used to return event processing results:

``` python title="EaaS SDK v1" hl_lines="1-7"
from connect.eaas.extension import (
    ProcessingResponse,
    ValidationResponse,
    ProductActionResponse,
    CustomEventResponse,
    ScheduledExecutionResponse,
)
```

In SDK version 2, the responses classes are declared as follows:

``` python title="EaaS SDK v2" hl_lines="1-5"
from connect.eaas.core.responses import (
    BackgroundResponse,
    InteractiveResponse,
    ScheduledExecutionResponse,
)
```

The following table summarizes all response classes replacements:

|SDK v1|SDK v2|
|------|------|
|ProcessingResponse|BackgroundResponse|
|ValidationResponse|InteractiveResponse|
|ProductActionResponse|InteractiveResponse|
|CustomEventResponse|InteractiveResponse|
|ScheduledExecutionResponse|ScheduledExecutionResponse|


### Event handlers

In EaaS SDK v1, events are subscribed through the **extension.json** descriptor file. Each event has a predefined
method name to handle it:

``` json title="EaaS SDK v1" hl_lines="7-9"
{
  "name": "Old extension",
  "description": "This extension is based on SDK v1",
  "version": "1.0.0",
  "readme_url": "https://example.org/README.md",
  "changelog_url": "https://example.org/CHANGELOG.md",
  "capabilities": {
    "asset_purchase_request_processing": ["pending", "approved", "failed", "inquiring", "scheduled", "revoking", "revoked"]
  }
}
```

In addition, each event includes the `asset_purchase_request_processing` maps to the `process_asset_purchase_request` method:

``` python title="EaaS SDK v1" hl_lines="5"
from connect.eaas.extension import Extension


class MyExtension(Extension):
    def process_asset_purchase_request(self, request):
        pass
```

In EaaS SDK v2, in order to define a method of the `Events Application` class for a given event type and statuses, it must be
decorated via the **`@event`** decorator from the `connect.eaas.core.decorators` package. The following provides such an example:

``` python title="EaaS SDK v2" hl_lines="7-14"
from connect.eaas.core.decorators import event
from connect.eaas.core.extension import EventsApplicationBase


class MyEventsApplication(EventsApplicationBase):

    @event(
        'asset_purchase_request_processing',
        statuses=[
            'pending', 'approved', 'failed', 
            'inquiring', 'scheduled', 'revoking',
            'revoked',
        ],
    )
    def handle_purchase_request(self, request):
        pass
```

Therefore, in version 2, a name of a method that handles a given event is not enforced by an event type.

Use the following table to review event types and method names mapping:

|Event type|Method name|
|----------|-----------|
|asset_purchase_request_processing|process_asset_purchase_request|
|asset_change_request_processing|process_asset_change_request|
|asset_suspend_request_processing|process_asset_suspend_request|
|asset_resume_request_processing|process_asset_resume_request|
|asset_cancel_request_processing|process_asset_cancel_request|
|asset_adjustment_request_processing|process_asset_adjustment_request|
|asset_purchase_request_validation|validate_asset_purchase_request|
|asset_change_request_validation|validate_asset_change_request|
|product_action_execution|execute_product_action|
|product_custom_event_processing|process_product_custom_event|
|tier_config_setup_request_processing|process_tier_config_setup_request|
|tier_config_change_request_processing|process_tier_config_change_request|
|tier_config_adjustment_request_processing|process_tier_config_adjustment_request|
|tier_config_setup_request_validation|validate_tier_config_setup_request|
|tier_config_change_request_validation|validate_tier_config_change_request|
|listing_new_request_processing|process_new_listing_request|
|listing_remove_request_processing|process_remove_listing_request|
|tier_account_update_request_processing|process_tier_account_update_request|
|usage_file_request_processing|process_usage_file|
|part_usage_file_request_processing|process_usage_chunk_file|


!!! warning
    In order to allow the `Runner` from release 26 to execute
    extensions that are created via SDK version 1, your events declared in the
    **extension.json** descriptor take precedence over your events declared by using
    the SDK version 2 `@event` decorator. Therefore, **it is required to remove** the `capabilities`
    attribute from the **extension.json** descriptor to make it work.


### Schedulables

In EaaS SDK version 1, the schedulable methods are declared within the `extension.json` file:

``` json title="EaaS SDK v1" hl_lines="7-13"
{
  "name": "Old extension",
  "description": "This extension is based on SDK v1",
  "version": "1.0.0",
  "readme_url": "https://example.org/README.md",
  "changelog_url": "https://example.org/CHANGELOG.md",
  "schedulables": [
    {
      "name": "Schedulable method mock",
      "description": "It can be used to test DevOps scheduler.",
      "method": "execute_scheduled_processing"
    }
  ]
}
```

In EaaS SDK version 2, your schedulable methods must be decorated via the `@schedulable` decorators:

``` python title="EaaS SDK v2" hl_lines="1 6-9"
from connect.eaas.core.decorators import schedulable
from connect.eaas.core.extension import EventsApplicationBase

class MyEventsApplication(EventsApplicationBase):

    @schedulable(
        'Schedulable method mock',
        'It can be used to test DevOps scheduler.',
    )
    def execute_scheduled_processing(self, schedule):
        pass
```

!!! warning
    In order to allow the `Runner` from release 26 to execute
    extensions that are created via SDK version 1, your events declared in the
    **extension.json** descriptor take precedence over your events declared by using the
    SDK version 2 `@schedulable` decorator. Thus, **make sure to remove** the 
    `schedulables` attribute from the **extension.json** descriptor to make it work.


### Environment variables

An extension application can automatically declare environment variables that are required for the launch. 
Once your extension is started, all variables declared for your application will be assigned and 
initialized with values provided by the `inital_value` attribute. 

In the EaaS SDK version 1, all variables should be declared within the `extension.json` descriptor:

``` json title="EaaS SDK v1" hl_lines="7-20"
{
  "name": "Old extension",
  "description": "This extension is based on SDK v1",
  "version": "1.0.0",
  "readme_url": "https://example.org/README.md",
  "changelog_url": "https://example.org/CHANGELOG.md",
  "variables": [
    {
      "name": "ASSET_REQUEST_APPROVE_TEMPLATE_ID",
      "initial_value": "<change_with_purchase_request_approve_template_id>"
    },
    {
      "name": "ASSET_REQUEST_CHANGE_TEMPLATE_ID",
      "initial_value": "<change_with_change_request_approve_template_id>"
    },
    {
      "name": "TIER_REQUEST_APPROVE_TEMPLATE_ID",
      "initial_value": "<change_with_tier_request_approve_template_id>"
    }
  ]
}
```

In EaaS SDK version 2, it is required to use the `@variables` class decorator:

``` python title="EaaS SDK v2" hl_lines="1 5-20"
from connect.eaas.core.decorators import variables
from connect.eaas.core.extension import EventsApplicationBase


@variables(
    [
        {
        "name": "ASSET_REQUEST_APPROVE_TEMPLATE_ID",
        "initial_value": "<change_with_purchase_request_approve_template_id>"
        },
        {
        "name": "ASSET_REQUEST_CHANGE_TEMPLATE_ID",
        "initial_value": "<change_with_change_request_approve_template_id>"
        },
        {
        "name": "TIER_REQUEST_APPROVE_TEMPLATE_ID",
        "initial_value": "<change_with_tier_request_approve_template_id>"
        },
    ],
)
class MyEventsApplication(EventsApplicationBase):
    pass
```

!!! warning
    In order to allow the `Runner` from release 26 to execute
    extensions that are created via SDK version 1, your events declared in the
    **extension.json** descriptor take precedence over your events declared by using the
    SDK version 2  `@variables` decorator. Consequently, **make sure to remove** the `variables`
    attribute from the **extension.json** descriptor to make it work.
