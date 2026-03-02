import json
import os

import pytest
import responses

from connect.eaas.core.egress_proxy import EgressProxyClient
from connect.eaas.core.models import EgressProxy, EgressProxyCertificates


@pytest.fixture
def proxy_config():
    """Sample proxy configuration (as stored in EGRESS_PROXIES_CONFIG)."""
    return {
        'id': 'proxy-123',
        'url': 'https://egress-proxy.example.com',
        'headers': [
            {'name': 'X-Required-Header', 'required': True},
            {'name': 'X-Optional-Header', 'required': False},
        ],
    }


@pytest.fixture
def certificates():
    """Sample certificates."""
    return EgressProxyCertificates(
        client_cert=(
            '-----BEGIN CERTIFICATE-----\n'
            'CLIENT_CERT\n'
            '-----END CERTIFICATE-----'
        ),
        client_key=(
            '-----BEGIN PRIVATE KEY-----\n'
            'CLIENT_KEY\n'
            '-----END PRIVATE KEY-----'
        ),
        ca_cert=(
            '-----BEGIN CERTIFICATE-----\n'
            'CA_CERT\n'
            '-----END CERTIFICATE-----'
        ),
    )


@pytest.fixture
def egress_proxy(proxy_config):
    """Sample EgressProxy model."""
    return EgressProxy(owner_id='PA-063-101', **proxy_config)


@pytest.fixture
def cleanup_client():
    """Fixture to cleanup temporary certificate files after test."""
    clients = []

    def _register(client):
        clients.append(client)
        return client

    yield _register

    for client in clients:
        if hasattr(client, 'cert_file') and os.path.exists(client.cert_file):
            os.unlink(client.cert_file)
        if hasattr(client, 'key_file') and os.path.exists(client.key_file):
            os.unlink(client.key_file)
        if hasattr(client, 'ca_file') and os.path.exists(client.ca_file):
            os.unlink(client.ca_file)


@pytest.fixture
def env_vars(proxy_config, certificates):
    """Set up environment variables for testing."""
    old_env = os.environ.copy()
    os.environ['EGRESS_PROXIES_CONFIG'] = json.dumps({
        'PA-063-101': proxy_config,
    })
    os.environ['TLS_CLIENT_CERT'] = certificates.client_cert
    os.environ['TLS_CLIENT_KEY'] = certificates.client_key
    os.environ['TLS_CA_CERT'] = certificates.ca_cert
    yield
    os.environ.clear()
    os.environ.update(old_env)


def test_init_creates_temp_cert_files(
    egress_proxy, certificates, cleanup_client,
):
    """Test that initialization creates temporary certificate files."""
    client = cleanup_client(
        EgressProxyClient(proxy=egress_proxy, certificates=certificates),
    )

    assert os.path.exists(client.cert_file)
    assert os.path.exists(client.key_file)
    assert os.path.exists(client.ca_file)

    with open(client.cert_file, 'r') as f:
        assert f.read() == certificates.client_cert

    with open(client.key_file, 'r') as f:
        assert f.read() == certificates.client_key

    with open(client.ca_file, 'r') as f:
        assert f.read() == certificates.ca_cert


def test_init_sets_proxy_attributes(
    egress_proxy, certificates, cleanup_client,
):
    """Test that initialization sets proxy attributes correctly."""
    client = cleanup_client(
        EgressProxyClient(proxy=egress_proxy, certificates=certificates),
    )

    assert client.proxy == egress_proxy
    assert client.endpoint == egress_proxy.url


def test_require_proxy_returns_config_when_exists(proxy_config):
    """Test require_proxy returns config when account exists."""
    os.environ['EGRESS_PROXIES_CONFIG'] = json.dumps({
        'PA-063-101': proxy_config,
    })

    result = EgressProxyClient.require_proxy('PA-063-101')

    assert result == proxy_config


def test_require_proxy_returns_none_when_not_exists(proxy_config):
    """Test require_proxy returns None when account doesn't exist."""
    os.environ['EGRESS_PROXIES_CONFIG'] = json.dumps({
        'PA-063-101': proxy_config,
    })

    result = EgressProxyClient.require_proxy('PA-999-999')

    assert result is None


def test_require_proxy_returns_none_when_env_var_not_set():
    """Test require_proxy returns None when env var is not set."""
    if 'EGRESS_PROXIES_CONFIG' in os.environ:
        del os.environ['EGRESS_PROXIES_CONFIG']

    result = EgressProxyClient.require_proxy('PA-063-101')

    assert result is None


def test_require_proxy_returns_none_when_env_var_empty():
    """Test require_proxy returns None when env var is empty."""
    os.environ['EGRESS_PROXIES_CONFIG'] = ''

    result = EgressProxyClient.require_proxy('PA-063-101')

    assert result is None


# Tests for from_env class method


def test_from_env_creates_client_successfully(
    env_vars, proxy_config, cleanup_client,
):
    """Test from_env creates client with correct configuration."""
    client = cleanup_client(EgressProxyClient.from_env('PA-063-101'))

    assert client.proxy.id == proxy_config['id']
    assert client.proxy.url == proxy_config['url']
    assert client.proxy.owner_id == 'PA-063-101'
    assert os.path.exists(client.cert_file)
    assert os.path.exists(client.key_file)
    assert os.path.exists(client.ca_file)


def test_from_env_raises_error_when_no_proxy_config(env_vars):
    """Test from_env raises ValueError when proxy config not found."""
    with pytest.raises(ValueError) as exc:
        EgressProxyClient.from_env('PA-999-999')

    assert (
        'No proxy configuration found for account PA-999-999'
        in str(exc.value)
    )


def test_from_env_raises_error_when_missing_client_cert(env_vars):
    """Test from_env raises ValueError when TLS_CLIENT_CERT is missing."""
    del os.environ['TLS_CLIENT_CERT']

    with pytest.raises(ValueError) as exc:
        EgressProxyClient.from_env('PA-063-101')

    assert 'Missing TLS certificate environment variables' in str(exc.value)


def test_from_env_raises_error_when_missing_client_key(env_vars):
    """Test from_env raises ValueError when TLS_CLIENT_KEY is missing."""
    del os.environ['TLS_CLIENT_KEY']

    with pytest.raises(ValueError) as exc:
        EgressProxyClient.from_env('PA-063-101')

    assert 'Missing TLS certificate environment variables' in str(exc.value)


def test_from_env_raises_error_when_missing_ca_cert(env_vars):
    """Test from_env raises ValueError when TLS_CA_CERT is missing."""
    del os.environ['TLS_CA_CERT']

    with pytest.raises(ValueError) as exc:
        EgressProxyClient.from_env('PA-063-101')

    assert 'Missing TLS certificate environment variables' in str(exc.value)


def test_from_env_raises_error_when_all_certs_missing(proxy_config):
    """Test from_env raises ValueError when all cert env vars are missing."""
    os.environ['EGRESS_PROXIES_CONFIG'] = json.dumps({
        'PA-063-101': proxy_config,
    })

    with pytest.raises(ValueError) as exc:
        EgressProxyClient.from_env('PA-063-101')

    assert 'Missing TLS certificate environment variables' in str(exc.value)


@responses.activate
def test_send_proxied_request_success(
    egress_proxy, certificates, cleanup_client,
):
    """Test send_proxied_request successfully sends request."""
    responses.add(
        responses.POST,
        f'{egress_proxy.url}/proxy',
        json={'status': 'success'},
        status=200,
    )

    client = cleanup_client(
        EgressProxyClient(proxy=egress_proxy, certificates=certificates),
    )

    result = client.send_proxied_request(
        target_url='https://api.example.com/data',
        target_method='POST',
        payload={'key': 'value'},
        headers={'X-Required-Header': 'test-value'},
    )

    assert result == {'status': 'success'}


@responses.activate
def test_send_proxied_request_without_payload(
    egress_proxy, certificates, cleanup_client,
):
    """Test send_proxied_request without payload."""
    responses.add(
        responses.GET,
        f'{egress_proxy.url}/proxy',
        json={'data': 'retrieved'},
        status=200,
    )

    client = cleanup_client(
        EgressProxyClient(proxy=egress_proxy, certificates=certificates),
    )

    result = client.send_proxied_request(
        target_url='https://api.example.com/data',
        target_method='GET',
        headers={'X-Required-Header': 'test-value'},
    )

    assert result == {'data': 'retrieved'}


# Tests for _prepare_call_kwargs method


def test_prepare_call_kwargs_adds_target_url_header(
    egress_proxy, certificates, cleanup_client,
):
    """Test _prepare_call_kwargs adds X-Connect-Target-URL header."""
    client = cleanup_client(
        EgressProxyClient(proxy=egress_proxy, certificates=certificates),
    )

    kwargs = {
        'target_url': 'https://api.example.com/data',
        'headers': {
            'User-Agent': 'connect-extension-runner/1.0',
            'X-Required-Header': 'test-value',
        },
    }

    result = client._prepare_call_kwargs(kwargs)

    assert 'X-Connect-Target-URL' in result['headers']
    assert (
        result['headers']['X-Connect-Target-URL']
        == 'https://api.example.com/data'
    )


def test_prepare_call_kwargs_updates_user_agent(
    egress_proxy, certificates, cleanup_client,
):
    """Test _prepare_call_kwargs updates User-Agent header."""
    client = cleanup_client(
        EgressProxyClient(proxy=egress_proxy, certificates=certificates),
    )

    kwargs = {
        'target_url': 'https://api.example.com/data',
        'headers': {
            'User-Agent': 'connect-extension-runner/1.0',
            'X-Required-Header': 'test-value',
        },
    }

    result = client._prepare_call_kwargs(kwargs)

    assert result['headers']['User-Agent'].startswith(
        f'connect-egress-proxy-{egress_proxy.id}/',
    )


def test_prepare_call_kwargs_removes_authorization_header(
    egress_proxy, certificates, cleanup_client,
):
    """Test _prepare_call_kwargs removes Authorization header."""
    client = cleanup_client(
        EgressProxyClient(proxy=egress_proxy, certificates=certificates),
    )

    kwargs = {
        'target_url': 'https://api.example.com/data',
        'headers': {
            'User-Agent': 'connect-extension-runner/1.0',
            'Authorization': 'ApiKey ABC123',
            'X-Required-Header': 'test-value',
        },
    }

    result = client._prepare_call_kwargs(kwargs)

    assert 'Authorization' not in result['headers']


def test_prepare_call_kwargs_sets_cert_files(
    egress_proxy, certificates, cleanup_client,
):
    """Test _prepare_call_kwargs sets cert and verify parameters."""
    client = cleanup_client(
        EgressProxyClient(proxy=egress_proxy, certificates=certificates),
    )

    kwargs = {
        'target_url': 'https://api.example.com/data',
        'headers': {
            'User-Agent': 'connect-extension-runner/1.0',
            'X-Required-Header': 'test-value',
        },
    }

    result = client._prepare_call_kwargs(kwargs)

    assert result['cert'] == (client.cert_file, client.key_file)
    assert result['verify'] == client.ca_file


def test_prepare_call_kwargs_preserves_custom_cert(
    egress_proxy, certificates, cleanup_client,
):
    """Test _prepare_call_kwargs doesn't override custom cert parameter."""
    client = cleanup_client(
        EgressProxyClient(proxy=egress_proxy, certificates=certificates),
    )

    custom_cert = ('/path/to/custom.crt', '/path/to/custom.key')
    kwargs = {
        'target_url': 'https://api.example.com/data',
        'headers': {
            'User-Agent': 'connect-extension-runner/1.0',
            'X-Required-Header': 'test-value',
        },
        'cert': custom_cert,
    }

    result = client._prepare_call_kwargs(kwargs)

    assert result['cert'] == custom_cert


def test_prepare_call_kwargs_preserves_custom_verify(
    egress_proxy, certificates, cleanup_client,
):
    """Test _prepare_call_kwargs doesn't override custom verify parameter."""
    client = cleanup_client(
        EgressProxyClient(proxy=egress_proxy, certificates=certificates),
    )

    custom_ca = '/path/to/custom_ca.pem'
    kwargs = {
        'target_url': 'https://api.example.com/data',
        'headers': {
            'User-Agent': 'connect-extension-runner/1.0',
            'X-Required-Header': 'test-value',
        },
        'verify': custom_ca,
    }

    result = client._prepare_call_kwargs(kwargs)

    assert result['verify'] == custom_ca


# Tests for _update_headers method


def test_update_headers_modifies_user_agent(
    egress_proxy, certificates, cleanup_client,
):
    """Test _update_headers correctly modifies User-Agent."""
    client = cleanup_client(
        EgressProxyClient(proxy=egress_proxy, certificates=certificates),
    )

    headers = {
        'User-Agent': 'connect-extension-runner/1.2.3',
    }

    result = client._update_headers('https://api.example.com', headers)

    assert (
        result['User-Agent']
        == f'connect-egress-proxy-{egress_proxy.id}/1.2.3'
    )


def test_update_headers_adds_target_url(
    egress_proxy, certificates, cleanup_client,
):
    """Test _update_headers adds X-Connect-Target-URL header."""
    client = cleanup_client(
        EgressProxyClient(proxy=egress_proxy, certificates=certificates),
    )

    headers = {
        'User-Agent': 'connect-extension-runner/1.0',
    }

    result = client._update_headers('https://api.example.com/data', headers)

    assert result['X-Connect-Target-URL'] == 'https://api.example.com/data'


def test_update_headers_removes_authorization(
    egress_proxy, certificates, cleanup_client,
):
    """Test _update_headers removes Authorization header."""
    client = cleanup_client(
        EgressProxyClient(proxy=egress_proxy, certificates=certificates),
    )

    headers = {
        'User-Agent': 'connect-extension-runner/1.0',
        'Authorization': 'ApiKey SECRET',
    }

    result = client._update_headers('https://api.example.com', headers)

    assert 'Authorization' not in result


def test_update_headers_preserves_other_headers(
    egress_proxy, certificates, cleanup_client,
):
    """Test _update_headers preserves other headers."""
    client = cleanup_client(
        EgressProxyClient(proxy=egress_proxy, certificates=certificates),
    )

    headers = {
        'User-Agent': 'connect-extension-runner/1.0',
        'X-Custom-Header': 'custom-value',
        'Content-Type': 'application/json',
    }

    result = client._update_headers('https://api.example.com', headers)

    assert result['X-Custom-Header'] == 'custom-value'
    assert result['Content-Type'] == 'application/json'


# Tests for _validate_headers method


def test_validate_headers_success_with_required_headers(
    egress_proxy, certificates, cleanup_client,
):
    """Test _validate_headers passes when all required headers present."""
    client = cleanup_client(
        EgressProxyClient(proxy=egress_proxy, certificates=certificates),
    )

    headers = {
        'X-Required-Header': 'value',
    }

    client._validate_headers(headers)


def test_validate_headers_success_without_optional_headers(
    egress_proxy, certificates, cleanup_client,
):
    """Test _validate_headers passes when optional headers are missing."""
    client = cleanup_client(
        EgressProxyClient(proxy=egress_proxy, certificates=certificates),
    )

    headers = {
        'X-Required-Header': 'value',
    }

    client._validate_headers(headers)


def test_validate_headers_raises_when_required_header_missing(
    egress_proxy, certificates, cleanup_client,
):
    """
    Test _validate_headers raises ValueError when required header is missing.
    """
    client = cleanup_client(
        EgressProxyClient(proxy=egress_proxy, certificates=certificates),
    )

    headers = {
        'X-Optional-Header': 'value',
        # X-Required-Header is missing
    }

    with pytest.raises(ValueError) as exc:
        client._validate_headers(headers)

    assert "Missing required header: 'X-Required-Header'" in str(exc.value)


def test_validate_headers_success_with_no_required_headers(
    certificates, cleanup_client,
):
    """Test _validate_headers passes when proxy has no required headers."""
    proxy = EgressProxy(
        id='proxy-456',
        url='https://proxy.example.com',
        owner_id='PA-063-101',
        headers=[
            {'name': 'X-Optional-1', 'required': False},
            {'name': 'X-Optional-2', 'required': False},
        ],
    )
    client = cleanup_client(
        EgressProxyClient(proxy=proxy, certificates=certificates),
    )

    headers = {}

    # Should not raise
    client._validate_headers(headers)


def test_validate_headers_success_with_empty_headers_list(
    certificates, cleanup_client,
):
    """Test _validate_headers passes when proxy has no headers config."""
    proxy = EgressProxy(
        id='proxy-789',
        url='https://proxy.example.com',
        owner_id='PA-063-101',
        headers=[],
    )
    client = cleanup_client(
        EgressProxyClient(proxy=proxy, certificates=certificates),
    )

    headers = {}

    # Should not raise
    client._validate_headers(headers)


# Tests for _create_cert_file static method


def test_create_cert_file_creates_file():
    """Test _create_cert_file creates a file at a fixed location."""
    cert_content = (
        '-----BEGIN CERTIFICATE-----\n'
        'TEST\n'
        '-----END CERTIFICATE-----'
    )

    filepath = EgressProxyClient._create_cert_file(
        'test_cert.pem', cert_content,
    )

    try:
        assert os.path.exists(filepath)
        assert filepath.endswith('.pem')

        with open(filepath, 'r') as f:
            assert f.read() == cert_content
    finally:
        if os.path.exists(filepath):
            os.unlink(filepath)


def test_create_cert_file_uses_deterministic_path():
    """Test _create_cert_file returns the same path for same filename."""
    cert_content = (
        '-----BEGIN CERTIFICATE-----\n'
        'CERT\n'
        '-----END CERTIFICATE-----'
    )

    filepath1 = EgressProxyClient._create_cert_file(
        'determ_cert.pem', cert_content,
    )
    filepath2 = EgressProxyClient._create_cert_file(
        'determ_cert.pem', cert_content,
    )

    try:
        assert filepath1 == filepath2
    finally:
        if os.path.exists(filepath1):
            os.unlink(filepath1)


def test_create_cert_file_writes_only_once():
    """
    Test _create_cert_file writes the file only on first call.
    Subsequent calls with same content reuse existing file.
    """
    filename = 'write_once_cert.pem'
    cert_content = (
        '-----BEGIN CERTIFICATE-----\n'
        'ONCE\n'
        '-----END CERTIFICATE-----'
    )
    filepath = EgressProxyClient._create_cert_file(
        filename, cert_content,
    )

    try:
        mtime_before = os.path.getmtime(filepath)

        EgressProxyClient._create_cert_file(
            filename, cert_content,
        )

        mtime_after = os.path.getmtime(filepath)
        assert mtime_before == mtime_after
    finally:
        if os.path.exists(filepath):
            os.unlink(filepath)


def test_create_cert_file_rewrites_when_content_changes():
    """
    Test _create_cert_file rewrites the file when content changes.
    """
    filename = 'rewrite_cert.pem'
    old_content = (
        '-----BEGIN CERTIFICATE-----\n'
        'OLD\n'
        '-----END CERTIFICATE-----'
    )
    new_content = (
        '-----BEGIN CERTIFICATE-----\n'
        'NEW\n'
        '-----END CERTIFICATE-----'
    )
    filepath = EgressProxyClient._create_cert_file(
        filename, old_content,
    )

    try:
        EgressProxyClient._create_cert_file(
            filename, new_content,
        )

        with open(filepath, 'r') as f:
            assert f.read() == new_content
    finally:
        if os.path.exists(filepath):
            os.unlink(filepath)


def test_create_cert_file_different_names_create_different_files():
    """Test different filenames create different files."""
    cert1 = (
        '-----BEGIN CERTIFICATE-----\n'
        'CERT1\n'
        '-----END CERTIFICATE-----'
    )
    cert2 = (
        '-----BEGIN CERTIFICATE-----\n'
        'CERT2\n'
        '-----END CERTIFICATE-----'
    )

    filepath1 = EgressProxyClient._create_cert_file(
        'diff_cert1.pem', cert1,
    )
    filepath2 = EgressProxyClient._create_cert_file(
        'diff_cert2.pem', cert2,
    )

    try:
        assert filepath1 != filepath2
        assert os.path.exists(filepath1)
        assert os.path.exists(filepath2)

        with open(filepath1, 'r') as f:
            assert f.read() == cert1

        with open(filepath2, 'r') as f:
            assert f.read() == cert2
    finally:
        if os.path.exists(filepath1):
            os.unlink(filepath1)
        if os.path.exists(filepath2):
            os.unlink(filepath2)


def test_cert_files_created_once_across_multiple_clients(
    egress_proxy, certificates, cleanup_client,
):
    """
    Test that creating multiple clients reuses existing cert files
    without rewriting them.
    """
    client1 = cleanup_client(
        EgressProxyClient(
            proxy=egress_proxy, certificates=certificates,
        ),
    )

    mtime_cert = os.path.getmtime(client1.cert_file)
    mtime_key = os.path.getmtime(client1.key_file)
    mtime_ca = os.path.getmtime(client1.ca_file)

    client2 = cleanup_client(
        EgressProxyClient(
            proxy=egress_proxy, certificates=certificates,
        ),
    )

    assert client1.cert_file == client2.cert_file
    assert client1.key_file == client2.key_file
    assert client1.ca_file == client2.ca_file
    assert os.path.getmtime(client2.cert_file) == mtime_cert
    assert os.path.getmtime(client2.key_file) == mtime_key
    assert os.path.getmtime(client2.ca_file) == mtime_ca


@responses.activate
def test_full_workflow_with_required_headers(
    env_vars, proxy_config, cleanup_client,
):
    """Test complete workflow: create client from env and send request."""
    responses.add(
        responses.POST,
        f'{proxy_config["url"]}/proxy',
        json={'result': 'success'},
        status=200,
    )

    client = cleanup_client(EgressProxyClient.from_env('PA-063-101'))

    result = client.send_proxied_request(
        target_url='https://api.example.com/endpoint',
        target_method='POST',
        payload={'data': 'test'},
        headers={'X-Required-Header': 'value'},
    )

    assert result == {'result': 'success'}

    # Verify request was made with correct headers
    assert len(responses.calls) == 1
    request = responses.calls[0].request
    assert (
        request.headers['X-Connect-Target-URL']
        == 'https://api.example.com/endpoint'
    )
    assert 'connect-egress-proxy-proxy-123' in request.headers['User-Agent']
    assert 'Authorization' not in request.headers


def test_full_workflow_missing_required_header_raises_error(
    env_vars, proxy_config, cleanup_client,
):
    """
    Test that missing required header raises error during request preparation.
    """
    client = cleanup_client(EgressProxyClient.from_env('PA-063-101'))

    with pytest.raises(ValueError) as exc:
        client.send_proxied_request(
            target_url='https://api.example.com/endpoint',
            target_method='GET',
            headers={},
        )

    assert "Missing required header: 'X-Required-Header'" in str(exc.value)
