from typing import Literal, Optional

from pydantic import BaseModel


class Context(BaseModel):
    """
    Represent the context of the current web call.

    **Attributes:**

    * **installation_id** - id of the installation object owned by the current caller.
    * **user_id** - id of the user or service user that is doing the call.
    * **account_id** - id of the account that is doing the call.
    * **account_role** - role of the account that is doing the call.
    * **call_source** - it can be `ui` if the call came from the user interface or `api`
        if it is an API call.
    * **call_type** - it can be `admin` if the call came from the same account
        that own the extension otherwise `user`.
    """

    installation_id: Optional[str] = None
    user_id: str
    account_id: str
    account_role: str
    call_source: Literal['ui', 'api']
    call_type: Literal['admin', 'user']
