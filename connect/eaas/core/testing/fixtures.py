import pytest

from connect.eaas.core.testing import WebAppTestClient


@pytest.fixture
def test_client_factory():
    """
    This fixture allows to instantiate a WebAppTestClient
    given a webapp class.
    """

    def _get_client(webapp):
        return WebAppTestClient(webapp)

    return _get_client
