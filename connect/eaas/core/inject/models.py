from typing import Literal

from pydantic import BaseModel


class Context(BaseModel):
    installation_id: str
    user_id: str
    account_id: str
    account_role: str
    call_source: Literal['ui', 'api']
    call_type: Literal['admin', 'user']
