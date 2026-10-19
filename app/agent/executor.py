from datetime import datetime, timezone
import time
from app.schemas.request import AnalysisRequest
from app.schemas.common import TaskType, RunStatus, FailureStatus
from app.schemas.response import SpecialistResult
from app.schemas.execution import ExecutionResult
from app.schemas.trace import ExecutionTrace, TraceStep, TraceConstants
from app.schemas.plan import ExecutionPlan, PlanStep
from app.agent.router import SpecialistCandidateInfo
from app.agent.registry import registry
from pydantic import ValidationError

def create_trace_step(step: str, action: str, component: str, status: str, details: dict = None) -> TraceStep:
    return TraceStep(
        step=step,
        action=action,
        component=component,
        status=status,
        details=details or {}
    )

def execute_plan(request: AnalysisRequest, plan: ExecutionPlan, run_id: str = "test-run") -> ExecutionResult:
    trace_steps = []
    start_ms = int(time.time() * 1000)
    
    trace_steps.append(create_trace_step("1", "INPUT_VALIDATION", "executor", RunStatus.COMPLETED))
    trace_steps.append(create_trace_step("2", "QUERY_INTERPRETATION", "executor", RunStatus.COMPLETED))
    trace_steps.append(create_trace_step("3", TraceConstants.PLAN_CREATED, "agent", RunStatus.COMPLETED, details={"intent": plan.intent}))
    trace_steps.append(create_trace_step("4", TraceConstants.PLAN_VALIDATION_COMPLETED, "agent", RunStatus.COMPLETED))
    
    final_result = None
    
    for step in plan.steps:
        trace_steps.append(create_trace_step(str(5 + step.execution_order), TraceConstants.STEP_STARTED, "executor", RunStatus.RUNNING_SPECIALIST, details={
            "capability_id": step.capability_id,
            "specialist": f"{step.selected_specialist_name}@{step.selected_specialist_version}",
            "rationale": step.rationale
        }))
        
        specialist = registry.get(step.selected_specialist_name, step.selected_specialist_version)
        if not specialist:
            trace_steps.append(create_trace_step(str(5 + step.execution_order), TraceConstants.STEP_FAILED, "executor", FailureStatus.SPECIALIST_UNAVAILABLE))
            return ExecutionResult(run_id=run_id, status=FailureStatus.SPECIALIST_UNAVAILABLE, trace=ExecutionTrace(run_id=run_id, steps=trace_steps, total_time_ms=int(time.time() * 1000) - start_ms), errors=["Specialist not found"])
            
        try:
            # We assume single-step plans for now, so we pass original request. 
            # In true multi-step, we would pass outputs from previous steps.
            raw_result = specialist.analyze(request)
        except Exception as e:
            trace_steps.append(create_trace_step(str(5 + step.execution_order), TraceConstants.STEP_FAILED, "specialist", FailureStatus.SPECIALIST_FAILED))
            return ExecutionResult(run_id=run_id, status=FailureStatus.SPECIALIST_FAILED, trace=ExecutionTrace(run_id=run_id, steps=trace_steps, total_time_ms=int(time.time() * 1000) - start_ms), errors=[str(e)])
            
        if not isinstance(raw_result, SpecialistResult):
            trace_steps.append(create_trace_step(str(5 + step.execution_order), TraceConstants.STEP_FAILED, "executor", FailureStatus.SPECIALIST_FAILED))
            return ExecutionResult(run_id=run_id, status=FailureStatus.SPECIALIST_FAILED, trace=ExecutionTrace(run_id=run_id, steps=trace_steps, total_time_ms=int(time.time() * 1000) - start_ms), errors=["INVALID_SPECIALIST_RESULT"])
            
        try:
            SpecialistResult.model_validate(raw_result.model_dump())
        except ValidationError:
            trace_steps.append(create_trace_step(str(5 + step.execution_order), TraceConstants.STEP_FAILED, "executor", FailureStatus.SPECIALIST_FAILED))
            return ExecutionResult(run_id=run_id, status=FailureStatus.SPECIALIST_FAILED, trace=ExecutionTrace(run_id=run_id, steps=trace_steps, total_time_ms=int(time.time() * 1000) - start_ms), errors=["INVALID_SPECIALIST_RESULT"])
            
        trace_steps.append(create_trace_step(str(5 + step.execution_order), TraceConstants.STEP_COMPLETED, "specialist", RunStatus.COMPLETED))
        final_result = raw_result

    trace_steps.append(create_trace_step("99", TraceConstants.PLAN_COMPLETED, "executor", RunStatus.COMPLETED))

    return ExecutionResult(
        run_id=run_id,
        status=RunStatus.COMPLETED,
        response=final_result,
        trace=ExecutionTrace(run_id=run_id, steps=trace_steps, total_time_ms=int(time.time() * 1000) - start_ms),
        errors=[]
    )

def execute_specialist(request: AnalysisRequest, task: TaskType, candidate: SpecialistCandidateInfo, run_id: str = "test-run") -> ExecutionResult:
    # Wrapper for contract tests
    dummy_plan = ExecutionPlan(
        plan_id="dummy", intent="test", final_output_step="out",
        steps=[PlanStep(
            step_id="1", capability_id="dummy", action="test", output_ref="out", execution_order=1, rationale="test",
            selected_specialist_name=candidate.name, selected_specialist_version=candidate.version
        )]
    )
    return execute_plan(request, dummy_plan, run_id)
