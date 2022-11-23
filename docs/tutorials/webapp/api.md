## Create a web application class

Define a python module that includes a web application class and your required API endpoints:

```
$ touch chart_extension/webapp.py
```

Open  `chart_extension/webapp.py` with your code editor and provide the following data:

```python
from connect.eaas.core.decorators import router, web_app
from connect.eaas.core.extension import WebApplicationBase


@web_app(router)
class ChartWebApplication(WebApplicationBase):
    pass
```

A web application class must import the structure from `connect.eaas.core.extension.WebApplicationBase` and must be decorated with the `web_app` decorator that accepts the `router` instance as an argument.

The `router` instance will be used later to declare your API endpoints.


## Declare web application class in `pyproject.toml`

Your extension will be executed by the EaaS runtime called [Connect Extension Runner](https://github.com/cloudblue/connect-extension-runner).

This runner uses setuptools entrypoints to discover all features that are implemented by your extensions. Therefore, it is required to modify **pyproject.toml** and add an entrypoint for your web application as follows:


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

## Implement `retrieve settings` API endpoint

The backend of this web application is based on the FastAPI web framework. The FastAPI framework uses the [pydantic](https://pydantic-docs.helpmanual.io/) library to define input/output models for an API and perform JSON serialization/deserialization and validation of messages. Pydantic models are also used by FastAPI to generates schemas for your request/response payloads.

The following demonstrates how to implement a web application for working with multiple modules (`models`) on the Connect platform. Add a new module by using the following command:

```
$ touch chart_extension/schemas.py
```

Next, add the `Marketplace` and `Settings` modules to the `schemas.py` module:

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

Once your required models are defined, add an endpoint to your web application to retrieve settings of a specific account.
Connect enables you to store the settings of an extension for a specific account within the installation objects. 

Locate the `ChartWebApplication` class and add the following endpoint:

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

By using the `router` instance as a decorator, you can define an `GET` operation, specify the path (`/settings`), a summary for the OpenAPI specifications, and a response model for such operation.

To obtain the installation object owned by the account that is calling your settings endpoint, use the dependency injection technique of the FastAPI framework.
Specifically, FastAPI injects an `installation` object as an argument for the method that handles this endpoint by using the `get_installation` injection function provided by `connect-eaas-core`.

The extension runner is used to retrieve an installation object that is owned by a certain caller.

Futhermore, this method returns a *Settings* model with selected marketplaces. These marketplaces are received from the `settings` attribute of the installation object.

!!! note
    Your endpoints will be prefixed with the `/api` path fragment, so your retrieve settings endpoint will be available at
    `/api/settings`.

!!! warning
    The **settings** attribute of an **installation** object can store arbitrary JSON and are supported by extensions that include a small number of values (1-2 Kb at most). If your extension requires to keep more settings for a given account, you will need to use an external storage system such as a database as a service.
    

In case more information on the FastAPI dependency injection system is required, refer to the [FastAPI Dependencies docs](https://fastapi.tiangolo.com/tutorial/dependencies/).




## Implements `list marketplaces` API endpoint

The demo web application should include an endpoint to retrieve a list of available marketplaces. Thus, this application will query the Connect API to create a list of checkboxes and users will be able to select required matketplaces.

Implement this functionality by using the following code:

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
Note that installation objects in this case will also work with the FastAPI dependecy injection. Therefore, you can receive instantiated `ConnectClient` that works in the scope of a specific account. Such accounts will consume your specified endpoint by using the `get_installation_client` injection function.


## Implement `save settings` API endpoint

It is also required to add the functionality to save provided settings. Use the following code to add the corresponding endpoint:

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
Note that this code does not retrieves installation objects. However, it is used to update such objects.  
In order to locate and update required installation identifiers, use FastAPI to inject the call context in your method.  
In addition, note that this method requires a settings argument of the `Settings` type. Thus, the request payload will be deserialized to the `Settings` pydantic model.


!!! info
    The **Context** object is a pydantic model that contains the following attributes:

    * **installation_id**: identifier of the installation object from which a call is originated
    * **user_id**: current UI user id or service user id for API calls
    * **account_role**: can be either `vendor`, `distributor` or `reseller`
    * **call_source**: use the `ui` value that calls will originated from the Connect user interface, use `api` to use direct API calls
    * **call_type**: in case your value is set to `admin`, all calls will be originated from the same account that own the extension.


## Implement `generate chart data` API endpoint

The demo web app renders charts by using [quickchart.io](https://quickchart.io) that allows working with diagrams.
Thus, the provided endpoint generates chart configuration json that will be send to quickchart.io as a query-string parameter.

Implement this functionality as follows:

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

!!! info
    The provided demo web application includes the same structure and functionality of eaas-e2e-ma-mock extension. Refer to the [github.com/cloudblue/eaas-e2e-ma-mock](https://github.com/cloudblue/eaas-e2e-ma-mock) repository for more details.
