import json
import os
import tempfile

from cnct import ConnectClient

from connect.eaas.core.constants import (
    EGRESS_PROXY_DEFAULT_MAX_RETRIES,
    EGRESS_PROXY_DEFAULT_PATH,
    EGRESS_PROXY_TLS_CA_CERT_ENV_VAR,
    EGRESS_PROXY_TLS_CLIENT_CERT_ENV_VAR,
    EGRESS_PROXY_TLS_CLIENT_KEY_ENV_VAR,
    EGRESS_PROXY_USER_AGENT_HEADER,
    EGRESS_PROXY_X_CONNECT_TARGET_URL_HEADER,
)
from connect.eaas.core.models import EgressProxy, EgressProxyCertificates


class EgressProxyClient(ConnectClient):
    """Client for interacting with the Vendor Proxy API."""

    PROXY_PATH = EGRESS_PROXY_DEFAULT_PATH

    def __init__(
        self,
        proxy: EgressProxy,
        certificates: EgressProxyCertificates,
    ):
        self.proxy = proxy
        self.cert_file = self._create_temp_cert_file(certificates.client_cert)
        self.key_file = self._create_temp_cert_file(certificates.client_key)
        self.ca_file = self._create_temp_cert_file(certificates.ca_cert)

        super().__init__(
            endpoint=self.proxy.url,
            api_key=None,
            max_retries=EGRESS_PROXY_DEFAULT_MAX_RETRIES,
            use_specs=False,
        )

    @staticmethod
    def _create_temp_cert_file(cert_content):
        """Create a temporary file with certificate content."""
        temp_file = tempfile.NamedTemporaryFile(
            mode='w',
            delete=False,
            suffix='.pem',
        )
        temp_file.write(cert_content)
        temp_file.close()
        return temp_file.name

    @classmethod
    def require_proxy(cls, account_id: str):
        """
        Check if a proxy is required for the given account ID.

        Args:
            account_id: The account ID to check (e.g., 'PA-063-101')
        Returns:
            dict | None: Proxy configuration dictionary if it exists
            for the account, None otherwise.
        """
        egress_config = json.loads(os.getenv('EGRESS_PROXIES_CONFIG') or '{}')
        return egress_config.get(account_id)

    @classmethod
    def from_env(cls, account_id: str):
        """
        Create a VendorProxyClient instance from environment variables.

        Args:
            account_id: The account ID to get proxy config for
            (e.g., 'PA-063-101')

        Environment variables:
            EGRESS_PROXIES_CONFIG: JSON string with proxy configurations
            TLS_CLIENT_KEY: PEM-encoded private key
            TLS_CLIENT_CERT: PEM-encoded client certificate
            TLS_CA_CERT: PEM-encoded CA certificate
        """
        # Load proxy configuration
        proxy_config = cls.require_proxy(account_id)

        if not proxy_config:
            raise ValueError(
                f"No proxy configuration found for account {account_id}",
            )

        proxy = EgressProxy(owner_id=account_id, **proxy_config)

        if not all(key in os.environ for key in (
            EGRESS_PROXY_TLS_CLIENT_CERT_ENV_VAR,
            EGRESS_PROXY_TLS_CLIENT_KEY_ENV_VAR,
            EGRESS_PROXY_TLS_CA_CERT_ENV_VAR,
        )):
            raise ValueError("Missing TLS certificate environment variables")

        certificates = EgressProxyCertificates(
            client_cert=os.environ[EGRESS_PROXY_TLS_CLIENT_CERT_ENV_VAR],
            client_key=os.environ[EGRESS_PROXY_TLS_CLIENT_KEY_ENV_VAR],
            ca_cert=os.environ[EGRESS_PROXY_TLS_CA_CERT_ENV_VAR],
        )

        return cls(proxy=proxy, certificates=certificates)

    def send_proxied_request(self, *, target_url, target_method, **kwargs):
        """Send a request to the Vendor Proxy API."""
        kwargs['json'] = kwargs.pop('payload', None) or None
        return self.execute(
            target_method,
            self.PROXY_PATH,
            target_url=target_url,
            **kwargs,
        )

    def _prepare_call_kwargs(self, kwargs):
        target_url = kwargs.pop('target_url')
        kwargs = super()._prepare_call_kwargs(kwargs)
        headers = self._update_headers(target_url, kwargs['headers'])
        self._validate_headers(headers)
        kwargs['headers'] = headers
        kwargs.setdefault('cert', (self.cert_file, self.key_file))
        kwargs.setdefault('verify', self.ca_file)
        return kwargs

    def _update_headers(self, target_url, headers):
        _, rest = headers.get(EGRESS_PROXY_USER_AGENT_HEADER).split('/', 1)
        headers[EGRESS_PROXY_USER_AGENT_HEADER] = (
            f'connect-egress-proxy-{self.proxy.id}/{rest}'
        )
        headers[EGRESS_PROXY_X_CONNECT_TARGET_URL_HEADER] = target_url
        headers.pop('Authorization', None)
        return headers

    def _validate_headers(self, headers):
        for header in self.proxy.headers:
            if header['name'] not in headers and header.get('required', False):
                raise ValueError(
                    f"Missing required header: '{header['name']}'",
                )
