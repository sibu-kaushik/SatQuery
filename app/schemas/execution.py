from pydantic import BaseModel, Field
from typing import List, Optional, Any
from .response import SpecialistResult
from .trace import ExecutionTrace
from .common import RunStatus, FailureStatus

class ExecutionResult(BaseModel):
    run_id: str
    status: RunStatus | FailureStatus | str
    response: Optional[SpecialistResult] = None
    trace: ExecutionTrace
    errors: List[str] = Field(default_factory=list)
    timings: dict[str, Any] = Field(default_factory=dict)
