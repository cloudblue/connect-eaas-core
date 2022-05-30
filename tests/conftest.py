import pytest
import responses as sentry_responses


@pytest.fixture
def responses():
    with sentry_responses.RequestsMock() as rsps:
        yield rsps
