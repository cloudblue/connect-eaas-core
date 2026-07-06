from typing import List, Literal, Optional

from pydantic import BaseModel


class ValidationItem(BaseModel):
    level: Literal['WARNING', 'ERROR'] = 'WARNING'
    message: str
    file: Optional[str] = None
    start_line: Optional[int] = None
    lineno: Optional[int] = None
    code: Optional[str] = None


class ValidationResult(BaseModel):
    items: List[ValidationItem] = []
    must_exit: bool = False
    context: Optional[dict] = None
