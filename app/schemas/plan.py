from pydantic import BaseModel, Field
from typing import List, Optional, Any
from app.schemas.common import TaskType

class PlanStep(BaseModel):
    step_id: str
    capability_id: str
    action: str
    input_refs: List[str] = Field(default_factory=list)
    output_ref: str
    execution_order: int
    required: bool = True
    rationale: str
    status: str = "PENDING"
    selected_specialist_name: Optional[str] = None
    selected_specialist_version: Optional[str] = None

class ExecutionPlan(BaseModel):
    plan_id: str
    plan_version: str = "1.0"
    intent: str
    steps: List[PlanStep] = Field(default_factory=list)
    final_output_step: str
    status: str = "PENDING"
