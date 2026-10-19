from pydantic import BaseModel
from typing import List, Optional
from app.schemas.request import AnalysisRequest
from app.schemas.common import TaskType, FailureStatus
from app.schemas.plan import ExecutionPlan
from app.agent.agent import AgentV2

class SpecialistCandidateInfo(BaseModel):
    name: str
    version: str

class RoutingResult(BaseModel):
    status: str
    task: TaskType | str
    reason: str
    candidates: List[SpecialistCandidateInfo]
    plan: Optional[ExecutionPlan] = None

# Singleton agent
_agent = AgentV2()

def route_request(request: AnalysisRequest) -> RoutingResult:
    # Delegate to AgentV2
    plan_or_status = _agent.build_plan(request)
    
    if isinstance(plan_or_status, FailureStatus):
        return RoutingResult(
            status=plan_or_status.value,
            task=TaskType.UNKNOWN,
            reason=f"Agent routing failed with status: {plan_or_status.value}",
            candidates=[],
            plan=None
        )
        
    plan = plan_or_status
    
    # Preserve existing API behavior by mapping plan back to RoutingResult fields
    # Just take the first step for compatibility
    first_step = plan.steps[0] if plan.steps else None
    task = TaskType.UNKNOWN
    candidates = []
    
    if first_step:
        # Hack to get task from action string, or just use UNKNOWN for compat since executor doesn't strictly need it if it uses plan
        # Actually in AgentV2 we put the task in the action string "Execute {task.value}"
        # Let's extract it or default
        task_str = first_step.action.replace("Execute ", "")
        try:
            task = TaskType(task_str)
        except ValueError:
            pass
            
        if first_step.selected_specialist_name:
            candidates.append(SpecialistCandidateInfo(
                name=first_step.selected_specialist_name,
                version=first_step.selected_specialist_version
            ))
            
    return RoutingResult(
        status="PLANNING",
        task=task,
        reason=plan.intent,
        candidates=candidates,
        plan=plan
    )
