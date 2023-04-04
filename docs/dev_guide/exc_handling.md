Common Web Applications may produce various generic Exceptions, like unexpected DB errors, Runtime Errors, etc.
Our Web Application framework provides a generic way to configure catching and handling of these errors in the global application scope.
This way is based on the [FastAPI error handling](https://fastapi.tiangolo.com/tutorial/handling-errors/). Please, refer to the FastAPI documentation for more details.

In order to configure global exception handling, @classmethod `get_exception_handlers` shall be implemented in the Application class.
This method must accept `exception_handlers` arg and return a dictionary with Exception Classes as keys and handling functions as values.
Argument `exception_handlers` provides a default error handling configuration, which can be reused or ignored. 

Examples:

```py3
from connect.eaas.core.decorators import (
    router,
    web_app,
)
from connect.eaas.core.extension import WebApplicationBase
from fastapi.exception_handlers import http_exception_handler


async def custom_http_exception_handler(request, exc):
    print(f"OMG! An HTTP error!")
    return await http_exception_handler(request, exc)


@web_app(router)
class WAExtendsExceptionHandling(WebApplicationBase):
    @classmethod
    def get_exception_handlers(cls, exception_handlers):
        exception_handlers[ValueError] = custom_http_exception_handler
        return exception_handlers
        

@web_app(router)
class WAOverridesExceptionHandling(WebApplicationBase):
    @classmethod
    def get_exception_handlers(cls, exception_handlers):
        return {
            RuntimeError: custom_http_exception_handler,
        }
```
