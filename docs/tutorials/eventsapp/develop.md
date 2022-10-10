## Create the events application class

Now it's time to create our python module that will contain our events application:

```
$ touch tshirt_extension/eventsapp.py
```

Open the `tshirt_extension/eventsapp.py` with your favorite editor and put the following content inside it:

```python hl_lines="1 4"
from connect.eaas.core.extension import EventsApplicationBase


class TShirtEventsApplication(EventsApplicationBase):
    pass
```

## Declare the events application class in your pyproject.toml file

Your extension will be executed by the EaaS runtime called [Connect Extension Runner](https://github.com/cloudblue/connect-extension-runner).

The runner uses setuptools entrypoints to discover the features that your extensions implements, so we have to modify our **pyproject.toml** add an entrypoint for our events application:


```toml hl_lines="13 14"
[tool.poetry]
name = "tshirt-extension"
version = "0.1.0"
description = "T-Shirt extension"
authors = ["Globex corporation"]
readme = "README.md"
packages = [{include = "tshirt_extension"}]

[tool.poetry.dependencies]
python = ">=3.8,<3.11"
connect-eaas-core = ">=26.12,<27"

[tool.poetry.plugins."connect.eaas.ext"]
"eventsapp" = "tshirt_extension.eventsapp:TShirtEventsApplication"

[build-system]
requires = ["poetry-core"]
build-backend = "poetry.core.masonry.api"
```


## Declare the variable needed to track the out of stock size

You will track the size that is out of stock using an environment variable.

For that you can declare this variable so when the extension starts for the
first time this variable will be automatically created with an initial value:


```python hl_lines="1 5-12"
from connect.eaas.core.decorators import variables
from connect.eaas.core.extension import EventsApplicationBase


@variables(
    [
        {
            'name': 'OUT_OF_STOCK_SIZE',
            'initial_value': 'm',
        },
    ],
)
class TShirtEventsApplication(EventsApplicationBase):
    pass
```


## Create a schedulable method to update the `OUT_OF_STOCK_SIZE` variable

Let's add a schedulable method that will be scheduled to run once a day.

This method will get a random size from a list with all the available sizes
and update the `OUT_OF_STOCK_SIZE` variable:


```python hl_lines="1 3 20-43"
import random

from connect.eaas.core.decorators import schedulable, variables
from connect.eaas.core.extension import EventsApplicationBase
from connect.eaas.core.responses import ScheduledExecutionResponse


TSHIRT_SIZES = ['xs', 's', 'm', 'l', 'xl']


@variables(
    [
        {
            'name': 'OUT_OF_STOCK_SIZE',
            'initial_value': 'm',
        },
    ],
)
class TShirtEventsApplication(EventsApplicationBase):
    @schedulable(
        'Update stock',
        'Set the OUT_OF_STOCK_SIZE variable with a random size that will be considered out of stock',
    )
    def update_stock(self, schedule):
        current_oos_size = random.choice(TSHIRT_SIZES)
        self.client.ns(
            'devops',
        ).collection(
            'services',
        ).resource(
            '',
        ).collection(
            'environments',
        ).resource(
            '',
        ).collection(
            'variables',
        ).resource(
            'OUT_OF_STOCK_SIZE',
        ).update(
            payload={'value': current_oos_size},
        )
        return ScheduledExecutionResponse.done()
```

## Create an method to handle the draft validation event


Now let's add the event handler for draft validation that check if the choosed size is out of stock or not.

For draft validation, the event type is `asset_purchase_request_validation` and the status is `draft`:



```python hl_lines="3 44-54"
import random

from connect.eaas.core.decorators import event, schedulable, variables
from connect.eaas.core.extension import EventsApplicationBase
from connect.eaas.core.responses import InteractiveResponse, ScheduledExecutionResponse

TSHIRT_SIZES = ['xs', 's', 'm', 'l', 'xl']


@variables(
    [
        {
            'name': 'OUT_OF_STOCK_SIZE',
            'initial_value': 'm',
        },
    ],
)
class TShirtEventsApplication(EventsApplicationBase):
    @schedulable(
        'Update stock',
        'Set the OUT_OF_STOCK_SIZE variable with a random size that will be considered out of stock',
    )
    def update_stock(self, schedule):
        current_oos_size = random.choice(TSHIRT_SIZES)
        self.client.ns(
            'devops',
        ).collection(
            'services',
        ).resource(
            '',
        ).collection(
            'environments',
        ).resource(
            '',
        ).collection(
            'variables',
        ).resource(
            'OUT_OF_STOCK_SIZE',
        ).update(
            payload={'value': current_oos_size},
        )
        return ScheduledExecutionResponse.done()

    @event('asset_purchase_request_validation')
    def validate_tshirt_size(self, request):
        if request['asset']['params'][0]['value'] == self.config['OUT_OF_STOCK_SIZE']:
            request['asset']['params'][0]['value_error'] = (
                f"Sorry, the size {self.config['OUT_OF_STOCK_SIZE']} is out of stock"
            )
        else:
            request['asset']['params'][0]['value_error'] = ''
        
        return InteractiveResponse.done(body=request)
```

## Create an method to approve the pending purchase requests

To complete this tutorial let's add the event handler for the pending purchase requests to autoapprove them.

For pending purchase, the event type is `asset_purchase_request_processing` and the status is `pending`:


```python hl_lines="55-67"
import random

from connect.eaas.core.decorators import event, schedulable, variables
from connect.eaas.core.extension import EventsApplicationBase
from connect.eaas.core.responses import (
    BackgroundResponse,
    InteractiveResponse,
    ScheduledExecutionResponse,
)

TSHIRT_SIZES = ['xs', 's', 'm', 'l', 'xl']


@variables(
    [
        {
            'name': 'OUT_OF_STOCK_SIZE',
            'initial_value': 'm',
        },
    ],
)
class TShirtEventsApplication(EventsApplicationBase):
    @schedulable(
        'Update stock',
        'Set the OUT_OF_STOCK_SIZE variable with a random size that will be considered out of stock',
    )
    def update_stock(self, schedule):
        current_oos_size = random.choice(TSHIRT_SIZES)
        self.client.ns(
            'devops',
        ).collection(
            'services',
        ).resource(
            '',
        ).collection(
            'environments',
        ).resource(
            '',
        ).collection(
            'variables',
        ).resource(
            'OUT_OF_STOCK_SIZE',
        ).update(
            payload={'value': current_oos_size},
        )
        return ScheduledExecutionResponse.done()

    @event('asset_purchase_request_validation', statuses=['draft'])
    def validate_tshirt_size(self, request):
        if request['asset']['params'][0]['value'] == self.config['OUT_OF_STOCK_SIZE']:
            request['asset']['params'][0]['value_error'] = f"Sorry, the size {self.config['OUT_OF_STOCK_SIZE']} is out of stock"
        
        return InteractiveResponse.done(body=request)
    
    @event('asset_purchase_request_processing', statuses=['pending'])
    def approve_purchase_request(self, request):
        product_id = request['asset']['product']['id']
        template = self.client.products[product_id].templates.filter(
            scope='asset',
            type='fulfillment',
        ).first()

        self.client.requests[request['id']]('approve').post(
            {'template_id': template['id']},
        )
        return BackgroundResponse.done()
```


!!! success "Congratulations"
    :partying_face: your first `Events Application` is ready to be tested :beers:
