import pytest

from connect.eaas.core.testing import WebAppTestClient


@pytest.fixture
def test_client_factory():
    """
    This fixture allows to instantiate a WebAppTestClient
    given a webapp class.
    """

    def _get_client(webapp, base_url='https://example.org/public/v1'):
        return WebAppTestClient(webapp, base_url=base_url)

    return _get_client
