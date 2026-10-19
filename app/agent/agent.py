import uuid
from app.schemas.request import AnalysisRequest
from app.schemas.common import TaskType, InputConfigType, FailureStatus
from app.schemas.plan import ExecutionPlan, PlanStep
from app.agent.query_interpreter import interpret_query
from app.validation.compatibility import validate_request_full
from app.agent.registry import registry
from app.agent.plan_validator import PlanValidator

class AgentV2:
    def __init__(self):
        self.validator = PlanValidator()

    def build_plan(self, request: AnalysisRequest) -> ExecutionPlan | FailureStatus:
        # 1. Validate
        validation_res = validate_request_full(request)
        if not validation_res.valid:
            # We return FailureStatus for the router to handle compat
            code = validation_res.errors[0].code
            try:
                return FailureStatus(code)
            except ValueError:
                return FailureStatus.UNSUPPORTED_TASK
            
        config_type = request.input_configuration.type
        query_interp = interpret_query(request.query)
        
        # Determine steps based on intent
        tasks_needed = []
        
        if config_type == InputConfigType.BI_TEMPORAL:
            tasks_needed.append(TaskType.CHANGE)
            if query_interp.task_hint == TaskType.GROUNDING:
                tasks_needed.append(TaskType.GROUNDING)
        elif config_type == InputConfigType.OPTICAL_SAR:
            tasks_needed.append(TaskType.OPTICAL_SAR)
            if query_interp.task_hint == TaskType.GROUNDING:
                tasks_needed.append(TaskType.GROUNDING)
        elif query_interp.task_hint == TaskType.GROUNDING:
            tasks_needed.append(TaskType.GROUNDING)
        else:
            tasks_needed.append(TaskType.VQA)

        if not tasks_needed:
            return FailureStatus.UNSUPPORTED_TASK

        # Match capabilities
        plan_steps = []
        current_input_refs = ["request_input"]
        order = 1
        
        for task in tasks_needed:
            candidates = registry.find_candidates(request, task)
            if not candidates:
                return FailureStatus.SPECIALIST_UNAVAILABLE
                
            # Filter by adaptation status (must be available if it requires adaptation)
            eligible_candidates = []
            for c in candidates:
                if c.capabilities.requires_rs_adaptation and c.capabilities.rs_adaptation_status != "COMPLETED":
                    continue
                # Phase 7 constraint: RS adaptation is eligibility metadata
                eligible_candidates.append(c)
                
            if not eligible_candidates:
                return FailureStatus.SPECIALIST_UNAVAILABLE
                
            best_candidate = eligible_candidates[0]
            
            output_ref = f"output_step_{order}"
            
            step = PlanStep(
                step_id=str(uuid.uuid4()),
                capability_id=best_candidate.capabilities.capability_id,
                action=f"Execute {task.value}",
                input_refs=current_input_refs.copy(),
                output_ref=output_ref,
                execution_order=order,
                rationale=f"Selected {best_candidate.name} for {task.value}",
                selected_specialist_name=best_candidate.name,
                selected_specialist_version=best_candidate.version
            )
            
            plan_steps.append(step)
            current_input_refs = [output_ref] # Next step consumes this step's output
            order += 1
            
        plan = ExecutionPlan(
            plan_id=str(uuid.uuid4()),
            intent=request.query,
            steps=plan_steps,
            final_output_step=plan_steps[-1].output_ref if plan_steps else ""
        )
        
        try:
            self.validator.validate(plan)
        except ValueError:
            return FailureStatus.SPECIALIST_FAILED
            
        return plan
