Starting from Connect release 26 the version 2 of the EaaS SDK specification
has been released.
Connect release 26 supports both version 1 and 2 of EaaS SDK specification but
the version 1 of the specification will be dropped in future releases.

This article will help you to migrate from the SDK version 1 specification to 
the SDK version 2.


## Migrate `pyproject.toml`

### Events application setuptools entrypoint name

In version 1 of the EaaS SDK specifications the name of the entrypoint used to
load the class with all the event handlers was called `extension` like in the
following example:

``` toml title="EaaS SDK v1" hl_lines="3"
...
[tool.poetry.plugins."connect.eaas.ext"]
"extension" = "mypkg.extension:MyExtension"
...
```

In version 2 `extension` is deprecated in favour of `eventapp`:

``` toml title="EaaS SDK v2" hl_lines="3"
...
[tool.poetry.plugins."connect.eaas.ext"]
"eventsapp" = "mypkg.extension:MyExtension"
...
```

### EaaS SDK dependency

In version 1 of the EaaS SDK specifications an extension project
depends on the `connect-extension-runner` library:

``` toml title="EaaS SDK v1" hl_lines="4"
...
[tool.poetry.dependencies]
python = "^3.8"
connect-extension-runner = "24.*"
...
```

In version 2 it must depend on the `connect-eaas-core` library:

``` toml title="EaaS SDK v2" hl_lines="4"
...
[tool.poetry.dependencies]
python = "^3.8"
connect-eaas-core = "26.*"
...
```

## Migrate python code

### Base class

In version 1 the base class for an Events Application was:

``` python title="EaaS SDK v1" hl_lines="1 4"
from connect.eaas.extension import Extension


class MyExtension(Extension):
    pass
```


In version 2 the name of the base class changes from `Extension` to `EventsApplicationBase`:

``` python title="EaaS SDK v2" hl_lines="1 4"
from connect.eaas.core.extension import EventsApplicationBase


class MyEventsApplication(EventsApplicationBase):
    pass
```

### Response classes

In version 1 the response classes used to return the result of processing an event were:

``` python title="EaaS SDK v1" hl_lines="1-7"
from connect.eaas.extension import (
    ProcessingResponse,
    ValidationResponse,
    ProductActionResponse,
    CustomEventResponse,
    ScheduledExecutionResponse,
)
```

In version 2 the responses classes are:

``` python title="EaaS SDK v2" hl_lines="1-5"
from connect.eaas.core.responses import (
    BackgroundResponse,
    InteractiveResponse,
    ScheduledExecutionResponse,
)
```

The following table summarize the replacements:

|SDK v1|SDK v2|
|------|------|
|ProcessingResponse|BackgroundResponse|
|ValidationResponse|InteractiveResponse|
|ProductActionResponse|InteractiveResponse|
|CustomEventResponse|InteractiveResponse|
|ScheduledExecutionResponse|ScheduledExecutionResponse|


### Event handlers

In EaaS SDK v1 events are subscribed through the **extension.json** descriptor file and each event has a predefined
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

And the `asset_purchase_request_processing` maps to the `process_asset_purchase_request` method:

``` python title="EaaS SDK v1" hl_lines="5"
from connect.eaas.extension import Extension


class MyExtension(Extension):
    def process_asset_purchase_request(self, request):
        pass
```

In EaaS SDK v2, to make a method of an Events Application class for a given event type and statuses, it must be
decorated using the `@event` decorator from the `connect.eaas.core.decorators` package like in the following
example:

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

So the name of the method that handle a given event is not enforced anymore by the event type.

In the following table you can see the event type to method name mapping:

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
    Please note that in order to allow the release 26 of the `Runner` to execute
    extensions created following the SDK version 1, the events declared in the
    **extension.json** descriptor take precedence on the events declared using
    the SDK version 2 `@event` decorator so you **must** remove the `capabilities`
    attribute from the **extension.json** descriptor to make it work.


### Schedulables

In EaaS SDK version 1 schedulable methods are declared within the `extension.json` file:

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

In EaaS SDK version 2 schedulable method must be decorated using the `@schedulable` decorators:

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
    Please note that in order to allow the release 26 of the `Runner` to execute
    extensions created following the SDK version 1, the schedulables declared in the
    **extension.json** descriptor take precedence on the schedulables declared using
    the SDK version 2 `@schedulable` decorator so you **must** remove the `schedulables`
    attribute from the **extension.json** descriptor to make it work.


### Environment variables

An extension application can declare the environment variables it needs in order to run.
When the extension is executed, the variables declared for an application that are not already created
for the related environment will be created and initialized with the value from the `initial_value` attribute.

In the EaaS SDK version 1 variables were declared within the `extension.json` descriptor:

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

In EaaS SDK version 2 you must use the `@variables` class decorator:

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
    Please note that in order to allow the release 26 of the `Runner` to execute
    extensions created following the SDK version 1, the variables declared in the
    **extension.json** descriptor take precedence on the variables declared using
    the SDK version 2 `@variables` decorator so you **must** remove the `variables`
    attribute from the **extension.json** descriptor to make it work.
