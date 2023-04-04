Sometimes you need to implement a middleware that has to be executed on every call. For instance if
 you want to authenticate in different ways depending on the path or log the HTTPS call performance. For this
 reason you could use middlewares that follows the 
  [ASGI](https://asgi.readthedocs.io/en/latest/specs/main.html) protocol standards.
  [FastAPI](https://fastapi.tiangolo.com/advanced/middleware/) and
   [Starlette](https://www.starlette.io/middleware/) have already implemented some of them.

In order to configure the middlewares you have to overwrite the class method `get_middlewares` in
 the Application class. This function must return a list of middlewares. Such middlewares could be
 specified in three ways:

 - As a **function**.
 - As a **class**.
 - As a **class with init parameters**, which will be a **tupple** where the first element is the class and
    the second one a dict with the parameters.

In the following example you could see how this could be done:

```py3
import logging

from connect.eaas.core.decorators import (
    router,
    web_app,
)
from connect.eaas.core.extension import WebApplicationBase


logger = logging.getLogger('example')


async def middleware_timing(request, call_next):
    """"
    Middleware that logs all the call timings in seconds.
    """"
    start_time = time.time():
    request = await call_next(request)
    elapsed = time.time() - start_time
    logger.info(f'Request processed. Elapsed time {elapsed}s')
    return request


class MiddlewareTimingClass:
    """"
    Middleware that logs all the call timings in seconds.
    """"
    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        start_time = time.time()
        await self.app(scope, receive, send)
        elapsed = time.time() - start_time
        logger.info(f'Request processed. Elapsed time {elapsed}s')


class MiddlewareTimingClassWithParams:
    """"
    Middleware that logs the calls that are longer than the specified
     threshold in seconds. Also the logging level could be configured.
    """"
    
    _log_fn = {
        logging.CRITICAL: logger.critical,
        logging.ERROR: logger.error,
        logging.WARNING: logger.warning,
        logging.INFO: logger.info,
        logging.DEBUG: logger.debug
    }

    def __init__(self, app, log_level=logging.INFO, threshold=60.0):
        self.app = app
        self.log_level = log_level
        self.threshold = threshold

    async def __call__(self, scope, receive, send):
        start_time = time.time()
        await self.app(scope, receive, send)
        elapsed = time.time() - start_time
        if elapsed >= self.threshold:
            self._log_fn[self.log_level](
                f'Request processed. Elapsed time {elapsed}s',
            )


@web_app(router)
class MyWebApplication(WebApplicationBase):
    @classmethod
    def get_middlewares(cls):
        return [
            middleware_timing,
            MiddlewareTimingClass,
            (
                MiddlewareTimingClassWithParams,
                {
                    'log_level': logging.ERROR,
                    'threshold': 40.0,
                },
            ),
        ]
```
