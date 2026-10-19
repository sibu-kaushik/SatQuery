from pydantic import BaseModel, Field
from typing import List, Optional, Any
from datetime import datetime

class TraceStep(BaseModel):
    step: str
    action: str
    component: str
    status: str
    details: Optional[dict[str, Any]] = Field(default_factory=dict)
    
class TraceConstants:
    PLAN_CREATED = "PLAN_CREATED"
    PLAN_VALIDATION_STARTED = "PLAN_VALIDATION_STARTED"
    PLAN_VALIDATION_COMPLETED = "PLAN_VALIDATION_COMPLETED"
    SPECIALIST_SELECTED = "SPECIALIST_SELECTED"
    STEP_STARTED = "STEP_STARTED"
    STEP_COMPLETED = "STEP_COMPLETED"
    STEP_FAILED = "STEP_FAILED"
    PLAN_COMPLETED = "PLAN_COMPLETED"
    PLAN_FAILED = "PLAN_FAILED"

class ExecutionTrace(BaseModel):
    run_id: str
    steps: List[TraceStep] = Field(default_factory=list)
    total_time_ms: Optional[int] = None
