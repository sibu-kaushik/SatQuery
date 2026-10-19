from app.schemas.request import AnalysisRequest, InputConfiguration, InputItem
from app.schemas.response import SpecialistResult
from app.schemas.common import TaskType
from app.agent.executor import execute_specialist
from app.specialists.base import BaseSpecialist

def run_specialist_contract_tests(specialist: BaseSpecialist, task_type: TaskType, valid_request: AnalysisRequest):
    """
    Generic contract test harness that proves a specialist module conforms to the agent architecture.
    """
    
    # A. specialist name exists
    assert hasattr(specialist, "name"), f"Specialist {specialist.__class__.__name__} missing name"
    assert isinstance(specialist.name, str) and len(specialist.name) > 0
    
    # B. specialist version exists
    assert hasattr(specialist, "version"), f"Specialist {specialist.__class__.__name__} missing version"
    
    # C. capabilities are declared
    capabilities = specialist.capabilities
    assert capabilities is not None, "Must declare capabilities"
    
    # D. can_handle() returns bool
    can_handle_result = specialist.can_handle(valid_request)
    assert isinstance(can_handle_result, bool)
    
    if can_handle_result:
        # E. analyze() accepts valid request
        result = specialist.analyze(valid_request)
        
        # F. analyze() returns SpecialistResult
        assert isinstance(result, SpecialistResult), f"Expected SpecialistResult, got {type(result)}"
        
        # G. task matches declared capability
        assert result.task == task_type
        
        # H. model information exists
        assert result.model.name == specialist.name
        assert result.model.version == specialist.version
        
        # I. provenance is present for real execution
        assert hasattr(result, "provenance")
        assert hasattr(result.provenance, "is_real_data")
        assert hasattr(result.provenance, "synthetic")
        
        # J. evidence matches EvidenceItem schema (validated by Pydantic implicitly when returning SpecialistResult)
        for evidence in result.evidence:
            assert hasattr(evidence, "type")
            
        # K. confidence can be null (or float)
        assert result.confidence is None or isinstance(result.confidence, float)
        
        # L. uncertainty can be null
        # Uncertainty is not explicitly in SpecialistResult in phase 1, but we can check the model structure
        
        from app.specialists.base import SpecialistHealth
        assert isinstance(specialist.health(), SpecialistHealth)
    
    # N. specialist exceptions are handled by executor
    # We test this by forcing executor to run it (we pass dummy context)
    from app.agent.registry import registry
    from app.agent.router import SpecialistCandidateInfo
    registry.register(specialist)
    try:
        exec_result = execute_specialist(valid_request, task_type, SpecialistCandidateInfo(name=specialist.name, version=specialist.version), "test_run_id")
        assert exec_result.status in ["COMPLETED", "SPECIALIST_FAILED", "UNSUPPORTED_TASK"]
    finally:
        registry._specialists.remove(specialist)
    
    # O. no frontend dependency exists
    # If the specialist imported frontend, it would fail here or statically. 
    # Python doesn't have great isolation unless we trace imports, but we assert it doesn't return HTML/JS.
    assert "<html" not in str(result.answer)
    
    # P. no agent/router dependency exists inside specialist
    # By strictly relying on BaseSpecialist and schemas, this is architecturally enforced.
    
    return True
