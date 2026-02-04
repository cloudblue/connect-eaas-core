from dataclasses import dataclass, field


@dataclass
class Context:
    extension_id: str
    environment_id: str
    environment_type: str


@dataclass
class EgressProxy:
    id: str
    url: str
    owner_id: str
    headers: list[dict] = field(default_factory=list)


@dataclass
class EgressProxyCertificates:
    client_cert: str
    client_key: str
    ca_cert: str
