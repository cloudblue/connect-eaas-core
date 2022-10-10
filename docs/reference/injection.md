## Common

<code>connect.eaas.core.inject.common.<strong>get_config</strong></code>

> Function to inject the environment variables dictionary in a
> Web Application endpoint method.
>
> Usage:
> ``` python
> from connect.eaas.core.decorators import router, web_app
> from connect.eaas.core.extension import WebApplicationBase
> from connect.eaas.core.inject.common import get_config
> from fastapi import Depends
>
>
> @web_app(router)
> class MyWebApp(WebApplicationBase):
>
>   @router.get('/my_endpoint')
>   def my_endpoint(self, config: dict = Depends(get_config)):
>       my_variable = config['MY_VARIABLE']
>       ...
> ```


<code>connect.eaas.core.inject.common.<strong>get_logger</strong></code>

> Function to inject a preconfigured logger that, when run in cloud mode,
> it will send log messages to `logz.io`.
>
> Usage:
> ``` python
> from logging import LoggerAdapter
>
> from connect.eaas.core.decorators import router, web_app
> from connect.eaas.core.extension import WebApplicationBase
> from connect.eaas.core.inject.common import get_logger
> from fastapi import Depends
>
>
> @web_app(router)
> class MyWebApp(WebApplicationBase):
>
>   @router.get('/my_endpoint')
>   def my_endpoint(self, logger: LoggerAdapter = Depends(get_logger)):
>       logger.info('This is a log message at level INFO!')
>       ...
> ```


<code>connect.eaas.core.inject.common.<strong>get_call_context</strong></code>

> Function to inject a `Context` object with information about the call.
>
> Usage:
> ``` python
> from connect.eaas.core.decorators import router, web_app
> from connect.eaas.core.extension import WebApplicationBase
> from connect.eaas.core.inject.common import get_call_context
> from connect.eaas.core.inject.models import Context
> from fastapi import Depends
>
>
> @web_app(router)
> class MyWebApp(WebApplicationBase):
>
>   @router.get('/my_endpoint')
>   def my_endpoint(self, context: Context = Depends(get_call_context)):
>       installation_id = context.installation_id
>       ...
> ```


## Synchronous Web Application

<code>connect.eaas.core.inject.synchronous.<strong>get_extension_client</strong></code>

> Function to inject a pre-instantiated `ConnectClient` with an API key that will
> authenticate as the same account that owns the extension.
>
> Usage:
> ``` python
> from connect.client import ConnectClient
> from connect.eaas.core.decorators import router, web_app
> from connect.eaas.core.extension import WebApplicationBase
> from connect.eaas.core.inject.synchronous import get_extension_client
> from fastapi import Depends
>
>
> @web_app(router)
> class MyWebApp(WebApplicationBase):
>
>   @router.get('/my_endpoint')
>   def my_endpoint(self, client: ConnectClient = Depends(get_extension_client)):
>       pass
> ```


<code>connect.eaas.core.inject.synchronous.<strong>get_installation_client</strong></code>

> Function to inject a pre-instantiated `ConnectClient` with an API key that will
> authenticate as the same account as the one that is invoking the endpoint, i.e.
> the owner of the installation.
>
> Usage:
> ``` python
> from connect.client import ConnectClient
> from connect.eaas.core.decorators import router, web_app
> from connect.eaas.core.extension import WebApplicationBase
> from connect.eaas.core.inject.synchronous import get_installation_client
> from fastapi import Depends
>
>
> @web_app(router)
> class MyWebApp(WebApplicationBase):
>
>   @router.get('/my_endpoint')
>   def my_endpoint(self, client: ConnectClient = Depends(get_installation_client)):
>       pass
> ```

<code>connect.eaas.core.inject.synchronous.<strong>get_installation</strong></code>

> Function to inject the installation object owner by the current caller.
>
> Usage:
> ``` python
> from connect.eaas.core.decorators import router, web_app
> from connect.eaas.core.extension import WebApplicationBase
> from connect.eaas.core.inject.synchronous import get_installation
> from fastapi import Depends
>
>
> @web_app(router)
> class MyWebApp(WebApplicationBase):
>
>   @router.get('/my_endpoint')
>   def my_endpoint(self, installation: dict = Depends(get_installation)):
>       pass
> ```


## Asynchronous Web Application

<code>connect.eaas.core.inject.asynchronous.<strong>get_extension_client</strong></code>

> Function to inject a pre-instantiated `AsyncConnectClient` with an API key that will
> authenticate as the same account that owns the extension.
>
> Usage:
> ``` python
> from connect.client import AsyncConnectClient
> from connect.eaas.core.decorators import router, web_app
> from connect.eaas.core.extension import WebApplicationBase
> from connect.eaas.core.inject.asynchronous import get_extension_client
> from fastapi import Depends
>
>
> @web_app(router)
> class MyWebApp(WebApplicationBase):
>
>   @router.get('/my_endpoint')
>   async def my_endpoint(self, client: AsyncConnectClient = Depends(get_extension_client)):
>       pass
> ```


<code>connect.eaas.core.inject.asynchronous.<strong>get_installation_client</strong></code>

> Function to inject a pre-instantiated `AsyncConnectClient` with an API key that will
> authenticate as the same account as the one that is invoking the endpoint, i.e.
> the owner of the installation.
>
> Usage:
> ``` python
> from connect.client import AsyncConnectClient
> from connect.eaas.core.decorators import router, web_app
> from connect.eaas.core.extension import WebApplicationBase
> from connect.eaas.core.inject.asynchronous import get_installation_client
> from fastapi import Depends
>
>
> @web_app(router)
> class MyWebApp(WebApplicationBase):
>
>   @router.get('/my_endpoint')
>   async def my_endpoint(self, client: AsyncConnectClient = Depends(get_installation_client)):
>       pass
> ```

<code>connect.eaas.core.inject.asynchronous.<strong>get_installation</strong></code>

> Function to inject the installation object owner by the current caller.
>
> Usage:
> ``` python
> from connect.eaas.core.decorators import router, web_app
> from connect.eaas.core.extension import WebApplicationBase
> from connect.eaas.core.inject.asynchronous import get_installation
> from fastapi import Depends
>
>
> @web_app(router)
> class MyWebApp(WebApplicationBase):
>
>   @router.get('/my_endpoint')
>   async def my_endpoint(self, installation: dict = Depends(get_installation)):
>       pass
> ```


## Call `Context` model

::: connect.eaas.core.inject.models.Context
    :docstring: