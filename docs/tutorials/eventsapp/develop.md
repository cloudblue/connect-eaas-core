## Create an events application class

Define a python module that includes your application type. The following showcases how to create a module that implements an events application:

```
$ touch tshirt_extension/eventsapp.py
```

Open `tshirt_extension/eventsapp.py` with your code editor and provide the following specifications:

```python hl_lines="1 4"
from connect.eaas.core.extension import EventsApplicationBase


class TShirtEventsApplication(EventsApplicationBase):
    pass
```

## Declare events application class in `pyproject.toml`

Your extension will be executed by the EaaS runtime called [Connect Extension Runner](https://github.com/cloudblue/connect-extension-runner).

The extension runner utilizes setup tools entrypoints to discover all features that are provided by your extension. Consequently, it is required to modify **pyproject.toml** and add an entrypoint for your events application as follows:


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


## Track out of stock items

Track items that are out of stock by declaring corresponding environment variables. The following showcases how to create a variable that will be automatically created and assigned to its initial value once the extension is launched for the first time:


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


## Update the `OUT_OF_STOCK_SIZE` variable

Once your variable for tracking out of stock items is defined, create a schedule to automatically update this variable. The 
following demonstrates how to create a method that will run and check for updates once a day. This method will get a random size
from the list and update the `OUT_OF_STOCK_SIZE` variable:


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

## Method for draft validation events

The following showcases how to create an event handler for the draft purchase requests validation. This handler will check whether the selected t-shirt size is out of stock. To implement the draft request validation, add the `asset_purchase_request_validation` event type and specify the `draft` status:



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

## Method to auto-approve pending requests

Add an event handler to automatically approve pending purchase requests. Specifically, add the `asset_purchase_request_processing` event type and the `pending` state:


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
    :partying_face: This concludes your `Events Application` creation and your app should be ready for the following tests! :beers:
