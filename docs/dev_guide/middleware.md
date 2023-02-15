Sometimes you need to implement a middleware that has to be executed on every call. For instance if
 you want to authenticate in differents ways depending on the path or log the HTTPS call performance. For this
 reason you could use middlewares that follows the 
  [ASGI](https://asgi.readthedocs.io/en/latest/specs/main.html) protocol standards.
  [FastAPI](https://fastapi.tiangolo.com/advanced/middleware/) and
   [Starlette](https://www.starlette.io/middleware/) have already implemented some of them.

Basically you could write your own middleware in a two different ways:

- As a **function**: an asynchronous function that needs two parameters; `request` and `call_next`.
    You must return the result of `await call_next(request)` always in order to keep the 
    regular flow. The logic might be before or after this call.
- As a **class**:
    - **Without parameters**: you should override the async `__call__` method that has `scope`, `receive`
        and `send` parameters as input. Inside you should also call 
        `await self.app(scope, receive, send)` to process the request. The logic might be before or
        after this call.
    - **With init parameters**: additionaly to override the `__call__` method, you should override the
        `__init__` method. The signature additionally to the `app` parameter, add the ones you need.

In order to configure the middlewares you have to overwrite the class method `get_middlewares` in
 the Application class. This function must return a list of middlewares. Such middlewares could be
 specified in three ways:

 - As a **function**.
 - As a **class**.
 - As a **class with init parameters**, which will be a **tupple** where the first element is the class and
    the second one a dict with the parameters.

In the following example you could see how this could be done:

```py3
from starlette.requests import Request

from connect.eaas.core.decorators import (
    router,
    web_app,
)
from connect.eaas.core.extension import WebApplicationBase

async def middleware_fn(request, call_next):
    request = await call_next(request)
    # Do something
    return request

class MiddlewareClass:

    async def __call__(self, scope, receive, send):
        if scope["type"] == "http":
            request = Request(scope)
            # Do something with the request
        await self.app(scope, receive, send)

class MiddlewareClassWithParams:
    def __init__(self, app, debug=False):
        self.app = app
        self.debug = debug

    async def __call__(self, scope, receive, send):
        if self.debug:
            # Log the call
        await self.app(scope, receive, send)

@web_app(router)
class MyWebApplication(WebApplicationBase):
    @classmethod
    def get_middlewares(cls):
        return [
            middleware_fn,
            MiddleWareClass,
            (MiddleWareClassWithParams, {'debug': True}),
        ]
```
