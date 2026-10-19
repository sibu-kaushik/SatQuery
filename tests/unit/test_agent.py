import pytest
from app.schemas.request import AnalysisRequest, InputConfiguration, InputItem
from app.schemas.common import InputConfigType, TaskType, FailureStatus
from app.schemas.plan import ExecutionPlan
from app.agent.agent import AgentV2
from app.agent.registry import registry
from app.specialists.base import BaseSpecialist, SpecialistHealth
from app.agent.capabilities import SpecialistCapability

class MockAdapter(BaseSpecialist):
    def __init__(self, task: TaskType, name: str = "mock", rs_status: str = "COMPLETED", requires_rs: bool = False):
        self._task = task
        self._name = name
        self._rs_status = rs_status
        self._requires_rs = requires_rs
        
    @property
    def name(self) -> str: return self._name
    @property
    def version(self) -> str: return "1.0"
    @property
    def capabilities(self) -> SpecialistCapability:
        return SpecialistCapability(
            capability_id=self.name,
            name=self.name, version="1.0",
            model_id=self.name, model_version="1.0",
            tasks=[self._task], supported_tasks=[self._task],
            modalities=["OPTICAL", "SAR"], supported_modalities=["OPTICAL", "SAR"],
            input_configurations=[InputConfigType.SINGLE_IMAGE, InputConfigType.BI_TEMPORAL, InputConfigType.OPTICAL_SAR],
            requires_rs_adaptation=self._requires_rs,
            rs_adaptation_status=self._rs_status
        )
    def can_handle(self, request: AnalysisRequest) -> bool: return True
    def analyze(self, request: AnalysisRequest): pass
    def health(self) -> SpecialistHealth: return SpecialistHealth(status="OK")

@pytest.fixture(autouse=True)
def setup_registry():
    registry._specialists = []
    registry.register(MockAdapter(TaskType.VQA, "mock-vqa"))
    registry.register(MockAdapter(TaskType.GROUNDING, "mock-grounding"))
    registry.register(MockAdapter(TaskType.CHANGE, "mock-change"))
    registry.register(MockAdapter(TaskType.OPTICAL_SAR, "mock-optical-sar"))

def test_agent_vqa_single_step():
    agent = AgentV2()
    req = AnalysisRequest(
        query="Is there water?",
        inputs=[InputItem(url="1.tif", type="image/tiff")],
        input_configuration=InputConfiguration(type=InputConfigType.SINGLE_IMAGE)
    )
    plan = agent.build_plan(req)
    assert isinstance(plan, ExecutionPlan)
    assert len(plan.steps) == 1
    assert plan.steps[0].action == "Execute VQA"
    assert plan.steps[0].selected_specialist_name == "mock-vqa"

def test_agent_change_multi_step():
    agent = AgentV2()
    req = AnalysisRequest(
        query="Where are the new buildings?",
        inputs=[
            InputItem(url="1.tif", type="image/tiff"),
            InputItem(url="2.tif", type="image/tiff")
        ],
        input_configuration=InputConfiguration(type=InputConfigType.BI_TEMPORAL)
    )
    plan = agent.build_plan(req)
    assert isinstance(plan, ExecutionPlan)
    # The query interpreter detects spatial language, so it triggers GROUNDING after CHANGE
    assert len(plan.steps) == 2
    assert plan.steps[0].action == "Execute CHANGE"
    assert plan.steps[1].action == "Execute GROUNDING"
    assert plan.steps[0].output_ref == plan.steps[1].input_refs[0]
    assert plan.final_output_step == plan.steps[1].output_ref

def test_agent_filters_incomplete_adaptation():
    agent = AgentV2()
    registry._specialists = []
    registry.register(MockAdapter(TaskType.VQA, "mock-vqa-unadapted", rs_status="PENDING", requires_rs=True))
    
    req = AnalysisRequest(
        query="Is there water?",
        inputs=[InputItem(url="1.tif", type="image/tiff")],
        input_configuration=InputConfiguration(type=InputConfigType.SINGLE_IMAGE)
    )
    res = agent.build_plan(req)
    # Should fail because the only specialist requires RS adaptation which is pending
    assert res == FailureStatus.SPECIALIST_UNAVAILABLE
