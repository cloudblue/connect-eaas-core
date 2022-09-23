from typing import List, Literal, Optional

from pydantic import BaseModel


class ValidationItem(BaseModel):
    level: Literal['WARNING', 'ERROR'] = 'WARNING'
    message: str
    file: Optional[str]
    start_line: Optional[int]
    lineno: Optional[int]
    code: Optional[str]


class ValidationResult(BaseModel):
    items: List[ValidationItem] = []
    must_exit: bool = False
    context: Optional[dict]
