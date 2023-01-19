from dataclasses import dataclass


@dataclass
class Context:
    extension_id: str
    environment_id: str
    environment_type: str
