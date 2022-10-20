from connect.eaas.core.testing import WebAppTestClient


def test_test_client_factory(test_client_factory, webapp_mock):
    client = test_client_factory(webapp_mock)
    assert isinstance(client, WebAppTestClient)
    assert client._webapp_class == webapp_mock
