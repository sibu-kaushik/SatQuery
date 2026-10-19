from app.schemas.plan import ExecutionPlan
from app.agent.registry import registry

class PlanValidator:
    @staticmethod
    def validate(plan: ExecutionPlan) -> bool:
        if not plan.steps:
            raise ValueError("Execution plan has no steps.")
            
        produced_outputs = set(["request_input"])
        
        for step in plan.steps:
            # Check inputs
            for ref in step.input_refs:
                if ref not in produced_outputs:
                    raise ValueError(f"Step {step.step_id} requires missing input reference: {ref}")
                    
            # Add output
            produced_outputs.add(step.output_ref)
            
            # Check capability availability
            if step.selected_specialist_name:
                specialist = registry.get(step.selected_specialist_name, step.selected_specialist_version)
                if not specialist:
                    raise ValueError(f"Step {step.step_id} requires unregistered specialist: {step.selected_specialist_name}")
                if not specialist.health().status == "OK":
                    raise ValueError(f"Step {step.step_id} selected specialist {step.selected_specialist_name} which is unhealthy.")
            else:
                raise ValueError(f"Step {step.step_id} has no specialist selected.")
                
        if plan.final_output_step not in produced_outputs:
            raise ValueError(f"Final output reference {plan.final_output_step} is never produced.")
            
        return True
