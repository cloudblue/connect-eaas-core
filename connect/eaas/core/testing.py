from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from starlette.testclient import TestClient


class WebAppTestClient(TestClient):

    def __init__(self, webapp, default_headers=None):
        self._webapp_class = webapp
        self.app = self.get_application()

        super().__init__(app=self.app)

        if default_headers:
            self.headers = default_headers

    def get_application(self):
        app = FastAPI()

        auth_router, no_auth_router = self._webapp_class.get_routers()
        app.include_router(auth_router, prefix='/api')
        app.include_router(no_auth_router, prefix='/guest')

        static_root = self._webapp_class.get_static_root()
        if static_root:
            app.mount('/static', StaticFiles(directory=static_root), name='static')

        return app
