## Create the web application class

Now it's time to create our python module that will contain our web application class with our API endpoints:

```
$ touch chart_extension/webapp.py
```

Open the `chart_extension/webapp.py` with your favorite editor and put the following content inside it:

```python
from connect.eaas.core.decorators import router, web_app
from connect.eaas.core.extension import WebApplicationBase


@web_app(router)
class ChartWebApplication(WebApplicationBase):
    pass
```

A web application class must inherit from `connect.eaas.core.extension.WebApplicationBase` and must be decorated with the `web_app` decorator that accept the `router` instance as an argument.

The `router` will be used later to declare your API endpoints.


## Declare the web application class in your pyproject.toml file

Your extension will be executed by the EaaS runtime called [Connect Extension Runner](https://github.com/cloudblue/connect-extension-runner).

The runner uses setuptools entrypoints to discover the features that your extensions implements, so we have to modify our **pyproject.toml** add an entrypoint for our web application:


```toml hl_lines="13 14"
[tool.poetry]
name = "chart-extension"
version = "0.1.0"
description = "Chart extension"
authors = ["Globex corporation"]
readme = "README.md"
packages = [{include = "chart_extension"}]

[tool.poetry.dependencies]
python = ">=3.8,<3.11"
connect-eaas-core = ">=26.12,<27"

[tool.poetry.plugins."connect.eaas.ext"]
"webapp" = "chart_extension.webapp:ChartWebApplication"

[build-system]
requires = ["poetry-core"]
build-backend = "poetry.core.masonry.api"
```

## Implements the `retrieve settings` API endpoint

The FastAPI web framework use the [pydantic](https://pydantic-docs.helpmanual.io/) library to define input/output models for an API and perform json serialization/deserialization and validation of messages. Pydantic models are also used by FastAPI to generates schemas for your request/response payloads.

So first of all let's create a module for our models:

```
$ touch chart_extension/schemas.py
```

Now add the `Marketplace` and `Settings` models to the `schemas.py` module:

```python
from typing import List

from pydantic import BaseModel


class Marketplace(BaseModel):
    id: str
    name: str
    description: str
    icon: str = (
        'https://unpkg.com/@cloudblueconnect'
        '/material-svg@latest/icons/google/language/baseline.svg'
    )


class Settings(BaseModel):
    marketplaces: List[Marketplace] = []
```

Now that models are defined you can add an endpoint to your web application to retrieve the settings for a specific account.
Connect allows you to store the settings of an extension for a specific account within the installation object owner by such account.

Go to the `ChartWebApplication` class and add the following endpoint:

```python  hl_lines="3 12-21"
from connect.eaas.core.decorators import router, web_app
from connect.eaas.core.extension import WebApplicationBase
from connect.eaas.core.inject.synchronous import get_installation
from fastapi import Depends

from chart_extension.schemas import Settings


@web_app(router)
class ChartWebApplication(WebApplicationBase):

    @router.get(
        '/settings',
        summary='Retrive extension settings',
        response_model=Settings,
    )
    def retrieve_settings(
        self,
        installation: dict = Depends(get_installation),
    ):
        return Settings(marketplaces=installation['settings'].get('marketplaces', []))
```

Using the `router` as a decorator we can define an `GET` operation, specifying the path (/settings), a summary for the OpenAPI specifications and a response model for such operation.

To obtain the installation object owned by the account that is calling your settings endpoint we use the dependency injection technique of FastAPI.
It means that FastAPI will inject an `installation` object as the argument of method that handles this endpoint using the `get_installation` injection function provided by `connect-eaas-core`.

The Runner will be responsible to retrieve the Installation object owned by the current caller for you.

Finally this method return a Settings model getting the marketplaces from the settings attribute of the installation object.


!!! info
    If you want to know more about the FastAPI dependency injection system read the [FastAPI Dependencies chapter](https://fastapi.tiangolo.com/tutorial/dependencies/) of the FastAPI documentation.


!!! note
    Please note that your endpoints will be prefixed with the `/api` path fragment, so your retrieve settings endpoint will be available as
    `/api/settings`.


!!! warning
    The **settings** attribute of an **Installation** object is intended to store arbitrary JSON and is aimed at extensions that require a small number of values (at most 1-2 Kb). If your extension needs to keep more settings for a given account then you will need to use an external storage system such as a database as a service.


## Implements the `list marketplaces` API endpoint

Now you need to add an endpoint to retrieve the list of available marketplace querying the Connect API to allow your extension settings page to create a list of checkboxes so the user can select the marketplaces which is interested in:

```python  hl_lines="1 4 24-40"
from connect.client import ConnectClient
from connect.eaas.core.decorators import router, web_app
from connect.eaas.core.extension import WebApplicationBase
from connect.eaas.core.inject.synchronous import get_installation, get_installation_client
from fastapi import Depends

from chart_extension.schemas import Settings


@web_app(router)
class ChartWebApplication(WebApplicationBase):

    @router.get(
        '/settings',
        summary='Retrive extension settings',
        response_model=Settings,
    )
    def retrieve_settings(
        self,
        installation: dict = Depends(get_installation),
    ):
        return Settings(marketplaces=installation['settings'].get('marketplaces', []))

    @router.get(
        '/marketplaces',
        summary='List all available marketplaces',
        response_model=List[Marketplace],
    )
    def list_marketplaces(
        self,
        client: ConnectClient = Depends(get_installation_client),
    ):
        return [
            Marketplace(**marketplace)
            for marketplace in client.marketplaces.all().values_list(
                'id', 'name', 'description', 'icon',
            )
        ]
```

As for the installation object, using the FastAPI dependency injection you can receive a already instantiated `ConnectClient` that will work in the scope of the account that are consuming this endpoint using the `get_installation_client` injection function.


## Implements the `save settings` API endpoint

Let's add the save settings endpoint:

```python  hl_lines="4-5 42-60"
from connect.client import ConnectClient
from connect.eaas.core.decorators import router, web_app
from connect.eaas.core.extension import WebApplicationBase
from connect.eaas.core.inject.common import get_call_context
from connect.eaas.core.inject.models import Context
from connect.eaas.core.inject.synchronous import get_installation, get_installation_client
from fastapi import Depends

from chart_extension.schemas import Settings


@web_app(router)
class ChartWebApplication(WebApplicationBase):

    @router.get(
        '/settings',
        summary='Retrive extension settings',
        response_model=Settings,
    )
    def retrieve_settings(
        self,
        installation: dict = Depends(get_installation),
    ):
        return Settings(marketplaces=installation['settings'].get('marketplaces', []))

    @router.get(
        '/marketplaces',
        summary='List all available marketplaces',
        response_model=List[Marketplace],
    )
    def list_marketplaces(
        self,
        client: ConnectClient = Depends(get_installation_client),
    ):
        return [
            Marketplace(**marketplace)
            for marketplace in client.marketplaces.all().values_list(
                'id', 'name', 'description', 'icon',
            )
        ]

    @router.post(
        '/settings',
        summary='Save charts settings',
        response_model=Settings,
    )
    def save_settings(
        self,
        settings: Settings,
        context: Context = Depends(get_call_context),
        client: ConnectClient = Depends(get_installation_client),
    ):
        client('devops').installations[context.installation_id].update(
            payload={
                'settings': settings.dict(),
            },
        )
        return settings
```

Please note that here you don't need to retrieve the installation object but just update it.
To know the id of the installation that you have to update you can ask FastAPI to inject the call context in your method.

Also note that, this method expect a settings argument of type `Settings` so the request payload will be deserialized to
the `Settings` pydantic model.


!!! info
    The **Context** object is a pydantic model that have the following attributes:

    * **installation_id**: identifier of the installation object from which the call is originated
    * **user_id**: current UI user id or service user id for API calls
    * **account_role**: can be `vendor`, `distributor` or `reseller`
    * **call_source**: if its value is `ui` it means that the call is originated from the Connect user interface, if `api` it is a direct API call
    * **call_type**: if `admin` it means that the call is originated from the same account that own the extension.


## Implements the `generate chart data` API endpoint

The chart is rendered using the [quickchart.io](https://quickchart.io) that returns an image.
So this endpoint must generate chart configuration json that will be send to quickchart.io as a querystring parameter.

Let's add the endpoint:

```python  hl_lines="60-87"
from connect.client import ConnectClient
from connect.eaas.core.decorators import router, web_app
from connect.eaas.core.extension import WebApplicationBase
from connect.eaas.core.inject.common import get_call_context
from connect.eaas.core.inject.models import Context
from connect.eaas.core.inject.synchronous import get_installation, get_installation_client
from fastapi import Depends

from chart_extension.schemas import Settings


@web_app(router)
class ChartWebApplication(WebApplicationBase):

    @router.get(
        '/settings',
        summary='Retrive extension settings',
        response_model=Settings,
    )
    def retrieve_settings(
        self,
        installation: dict = Depends(get_installation),
    ):
        return Settings(marketplaces=installation['settings'].get('marketplaces', []))

    @router.get(
        '/marketplaces',
        summary='List all available marketplaces',
        response_model=List[Marketplace],
    )
    def list_marketplaces(
        self,
        client: ConnectClient = Depends(get_installation_client),
    ):
        return [
            Marketplace(**marketplace)
            for marketplace in client.marketplaces.all().values_list(
                'id', 'name', 'description', 'icon',
            )
        ]

    @router.post(
        '/settings',
        summary='Save charts settings',
        response_model=Settings,
    )
    def save_settings(
        self,
        settings: Settings,
        context: Context = Depends(get_call_context),
        client: ConnectClient = Depends(get_installation_client),
    ):
        client('devops').installations[context.installation_id].update(
            payload={
                'settings': settings.dict(),
            },
        )
        return settings

@router.get(
        '/chart',
        summary='Generate chart data',
    )
    def generate_chart_data(
        self,
        installation: dict = Depends(get_installation),
        client: ConnectClient = Depends(get_installation_client),
    ):
        data = {}
        for mp in installation['settings'].get('marketplaces', []):
            active_assets = client('subscriptions').assets.filter(
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