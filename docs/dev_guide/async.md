Connect EaaS Core supports the use of asynchronous I/O to develop events and web applications
through the [python asyncio module](https://docs.python.org/3/library/asyncio.html).

## Events application

If your event handler is declared as `async def` the [Connect Extension Runner](https://github.com/cloudblue/connect-extension-runner)
will instantiate your application class injecting the [AyncConnectClient](https://connect-openapi-client.readthedocs.io/en/latest/async_client/) client allowing you to make API calls to Connect using asyncio.

For example, the t-shirt application developed in the [Events Application tutorial](../tutorials/eventsapp/develop.md) can be rewritten
as in the following example:

```python hl_lines="27 29 49 56 58 63"
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
    async def update_stock(self, schedule):
        current_oos_size = random.choice(TSHIRT_SIZES)
        await self.client.ns(
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
    async def validate_tshirt_size(self, request):
        if request['asset']['params'][0]['value'] == self.config['OUT_OF_STOCK_SIZE']:
            request['asset']['params'][0]['value_error'] = f"Sorry, the size {self.config['OUT_OF_STOCK_SIZE']} is out of stock"
        
        return InteractiveResponse.done(body=request)
    
    @event('asset_purchase_request_processing', statuses=['pending'])
    async def approve_purchase_request(self, request):
        product_id = request['asset']['product']['id']
        template = await self.client.products[product_id].templates.filter(
            scope='asset',
            type='fulfillment',
        ).first()

        await self.client.requests[request['id']]('approve').post(
            {'template_id': template['id']},
        )
        return BackgroundResponse.done()
```


## Web application

Web applications are based on the [FastAPI](https://fastapi.tiangolo.com/async/) web framework that support writing web application both in a synchronous and asynchronous way.

`Connect Eaas Core` have the corresponding asynchronous injection function to inject in a asynchronous endpoint both the [AyncConnectClient](https://connect-openapi-client.readthedocs.io/en/latest/async_client/), and the [installation](../reference/injection.md/#asynchronous-web-application) object.

So the chart REST API developed in the [Web Application tutorial](../tutorials/webapp/api.md) can be rewritten
as in the following example:

```python  hl_lines="1 4 20 31 37 47 53 64 71"
from connect.client import AsyncConnectClient
from connect.eaas.core.decorators import router, web_app
from connect.eaas.core.extension import WebApplicationBase
from connect.eaas.core.inject.asynchronous import get_installation, get_installation_client
from connect.eaas.core.inject.common import get_call_context
from connect.eaas.core.inject.models import Context
from fastapi import Depends

from chart_extension.schemas import Settings


@web_app(router)
class ChartWebApplication(WebApplicationBase):

    @router.get(
        '/settings',
        summary='Retrive extension settings',
        response_model=Settings,
    )
    async def retrieve_settings(
        self,
        installation: dict = Depends(get_installation),
    ):
        return Settings(marketplaces=installation['settings'].get('marketplaces', []))

    @router.get(
        '/marketplaces',
        summary='List all available marketplaces',
        response_model=List[Marketplace],
    )
    async def list_marketplaces(
        self,
        client: AsyncConnectClient = Depends(get_installation_client),
    ):
        return [
            Marketplace(**marketplace)
            async for marketplace in client.marketplaces.all().values_list(
                'id', 'name', 'description', 'icon',
            )
        ]

    @router.post(
        '/settings',
        summary='Save charts settings',
        response_model=Settings,
    )
    async def save_settings(
        self,
        settings: Settings,
        context: Context = Depends(get_call_context),
        client: AsyncConnectClient = Depends(get_installation_client),
    ):
        await client('devops').installations[context.installation_id].update(
            payload={
                'settings': settings.dict(),
            },
        )
        return settings

@router.get(
        '/chart',
        summary='Generate chart data',
    )
    async def generate_chart_data(
        self,
        installation: dict = Depends(get_installation),
        client: AsyncConnectClient = Depends(get_installation_client),
    ):
        data = {}
        for mp in installation['settings'].get('marketplaces', []):
            active_assets = await client('subscriptions').assets.filter(
                R().marketplace.id.eq(mp['id']) & R().status.eq('active'),
            ).count()
            data[mp['id']] = active_assets

        return {
            'type': 'bar',
            'data': {
                'labels': list(data.keys()),
                'datasets': [
                    {
                        'label': 'Subscriptions',
                        'data': list(data.values()),
                    },
                ],
            },
        }
```