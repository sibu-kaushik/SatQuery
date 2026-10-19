from pydantic import BaseModel
from typing import List, Optional
from app.schemas.common import FailureStatus

class ValidationErrorDetail(BaseModel):
    code: FailureStatus | str
    message: str

class ValidationResult(BaseModel):
    valid: bool
    errors: List[ValidationErrorDetail]
    warnings: List[str]

    @classmethod
    def success(cls):
        return cls(valid=True, errors=[], warnings=[])

    @classmethod
    def failure(cls, errors: List[ValidationErrorDetail]):
        return cls(valid=False, errors=errors, warnings=[])
