import pytest
from app.schemas.request import AnalysisRequest, InputConfiguration, InputItem
from app.schemas.common import InputConfigType, TaskType, FailureStatus, RunStatus
from app.schemas.response import SpecialistResult
from app.schemas.plan import ExecutionPlan, PlanStep
from app.schemas.trace import TraceConstants
from app.agent.executor import execute_plan
from app.agent.registry import registry
from app.specialists.test_doubles.vqa import TestVQASpecialist
from app.specialists.base import BaseSpecialist, SpecialistHealth
from app.agent.capabilities import SpecialistCapability

class BadSpecialist(BaseSpecialist):
    @property
    def name(self) -> str: return "bad"
    @property
    def version(self) -> str: return "1.0"
    @property
    def capabilities(self) -> SpecialistCapability:
        return SpecialistCapability(capability_id="bad", name="bad", version="1.0", model_id="b", model_version="1", tasks=[TaskType.VQA], supported_tasks=[TaskType.VQA], modalities=["OPTICAL"], supported_modalities=["OPTICAL"])
    def can_handle(self, request: AnalysisRequest) -> bool: return True
    def analyze(self, request: AnalysisRequest) -> SpecialistResult:
        raise ValueError("Simulated crash")
    def health(self) -> SpecialistHealth: return SpecialistHealth(status="OK")

class MalformedSpecialist(BaseSpecialist):
    @property
    def name(self) -> str: return "malformed"
    @property
    def version(self) -> str: return "1.0"
    @property
    def capabilities(self) -> SpecialistCapability:
        return SpecialistCapability(capability_id="m", name="malformed", version="1.0", model_id="m", model_version="1", tasks=[TaskType.VQA], supported_tasks=[TaskType.VQA], modalities=["OPTICAL"], supported_modalities=["OPTICAL"])
    def can_handle(self, request: AnalysisRequest) -> bool: return True
    def analyze(self, request: AnalysisRequest) -> SpecialistResult:
        return {"not": "a SpecialistResult object"} # type: ignore
    def health(self) -> SpecialistHealth: return SpecialistHealth(status="OK")

@pytest.fixture(autouse=True)
def setup_registry():
    registry._specialists = []
    registry.register(TestVQASpecialist())
    registry.register(BadSpecialist())
    registry.register(MalformedSpecialist())

def get_base_request():
    return AnalysisRequest(
        query="Is there water?",
        inputs=[InputItem(url="1.tif", type="image/tiff")],
        input_configuration=InputConfiguration(type=InputConfigType.SINGLE_IMAGE)
    )

def create_plan(spec_name: str, spec_version: str) -> ExecutionPlan:
    return ExecutionPlan(
        plan_id="p1", intent="test", final_output_step="out",
        steps=[PlanStep(step_id="1", capability_id="test", action="test", output_ref="out", execution_order=1, rationale="test", selected_specialist_name=spec_name, selected_specialist_version=spec_version)]
    )

def test_missing_specialist():
    req = get_base_request()
    res = execute_plan(req, create_plan("non-existent", "1.0"))
    assert res.status == FailureStatus.SPECIALIST_UNAVAILABLE
    assert "not found" in res.errors[0]

def test_specialist_exception():
    req = get_base_request()
    res = execute_plan(req, create_plan("bad", "1.0"))
    assert res.status == FailureStatus.SPECIALIST_FAILED
    assert "Simulated crash" in res.errors[0]
    assert res.trace.steps[-1].status == FailureStatus.SPECIALIST_FAILED

def test_malformed_result():
    req = get_base_request()
    res = execute_plan(req, create_plan("malformed", "1.0"))
    assert res.status == FailureStatus.SPECIALIST_FAILED
    assert "INVALID_SPECIALIST_RESULT" in res.errors[0]

def test_successful_execution():
    req = get_base_request()
    res = execute_plan(req, create_plan("test-vqa", "test"))
    assert res.status == RunStatus.COMPLETED
    assert res.response.task == TaskType.VQA
    assert res.response.answer == "TEST_ONLY_RESULT"
    assert res.response.confidence is None
    assert res.response.evidence == []
    assert res.response.provenance.synthetic is True
    steps = [s.action for s in res.trace.steps]
    assert TraceConstants.STEP_STARTED in steps
    assert TraceConstants.STEP_COMPLETED in steps
    assert TraceConstants.PLAN_COMPLETED in steps
