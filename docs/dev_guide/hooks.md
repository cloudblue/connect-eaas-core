The following functions could be used to execute some logic before it starts and after it is stopped in any Application type (EventsApp, WebApp, AnvilApp or TransformationsApp).
For instance it could be used to:

- Apply some schema migrations.
- Retrieve some data from other services.
- Make an API call to send the extension status to other services.

### Startup hook

In order to add the logic to be executed before the app starts, we have to declare a class method function called `on_startup` in the Application class that we are using.
It can be synchronous function or asynchronous coroutine. For the asynchronous version you just need to add the `async` declaration and execute the logic asynchronously.

The signature has to be the one that you could see in the example:

- `cls`: the class.
- `logger`: a logger instance to be used.
- `config`: all the extension variables dictionary.

The following synchronous example:

```py3
from connect.eaas.core.decorators import (
    router,
    web_app,
)
from connect.eaas.core.extension import WebApplicationBase


@web_app(router)
class MyWebApplication(WebApplicationBase):
    @classmethod
    def on_startup(cls, logger, config):
        logger.info('Executing WebApp startup hook')
        # startup logic
        logger.info('WebApp startup hook execution done')
```

### Shutdown hook

In order to add logic to be executed after the extension shutdown, we have to declare a class method function called `on_shutdown` in the Application class that we are using.
Like in the startup callback, it can be a synchronous function or asynchronous coroutine.

The following synchronous example:

```py3

from connect.eaas.core.decorators import (
    router,
    web_app,
)
from connect.eaas.core.extension import WebApplicationBase


@web_app(router)
class MyWebApplication(WebApplicationBase):
    @classmethod
    def on_shutdown(cls, logger, config):
        logger.info('Executing WebApp shutdown hook')
        # shutdown logic
        logger.info('WebApp shutdown hook execution done')
```