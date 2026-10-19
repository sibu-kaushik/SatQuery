import pytest
from app.agent.router import route_request, RoutingResult
from app.schemas.request import AnalysisRequest, InputConfiguration, InputItem
from app.schemas.common import InputConfigType, TaskType, FailureStatus
from app.agent.registry import registry
from app.specialists.base import BaseSpecialist, SpecialistHealth
from app.agent.capabilities import SpecialistCapability

class MockAdapter(BaseSpecialist):
    def __init__(self, task: TaskType, name: str = "mock"):
        self._task = task
        self._name = name
        
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
            input_configurations=[InputConfigType.SINGLE_IMAGE, InputConfigType.BI_TEMPORAL, InputConfigType.OPTICAL_SAR]
        )
    def can_handle(self, request: AnalysisRequest) -> bool: return True
    def analyze(self, request: AnalysisRequest): pass
    def health(self) -> SpecialistHealth: return SpecialistHealth(status="OK")

@pytest.fixture(autouse=True)
def setup_registry():
    # Clear registry for each test
    registry._specialists = []
    registry.register(MockAdapter(TaskType.VQA, "mock-vqa"))
    registry.register(MockAdapter(TaskType.GROUNDING, "mock-grounding"))
    registry.register(MockAdapter(TaskType.CHANGE, "mock-change"))
    registry.register(MockAdapter(TaskType.OPTICAL_SAR, "mock-optical-sar"))

def test_routing_vqa():
    req = AnalysisRequest(
        query="Is there water?",
        inputs=[InputItem(url="1.tif", type="image/tiff")],
        input_configuration=InputConfiguration(type=InputConfigType.SINGLE_IMAGE)
    )
    res = route_request(req)
    assert res.task == TaskType.VQA
    assert res.status == "PLANNING"
    assert len(res.candidates) == 1

def test_routing_grounding():
    req = AnalysisRequest(
        query="Where is the water?",
        inputs=[InputItem(url="1.tif", type="image/tiff")],
        input_configuration=InputConfiguration(type=InputConfigType.SINGLE_IMAGE)
    )
    res = route_request(req)
    assert res.task == TaskType.GROUNDING

def test_routing_change():
    req = AnalysisRequest(
        query="What changed?",
        inputs=[
            InputItem(url="1.tif", type="image/tiff"),
            InputItem(url="2.tif", type="image/tiff")
        ],
        input_configuration=InputConfiguration(type=InputConfigType.BI_TEMPORAL)
    )
    res = route_request(req)
    assert res.task == TaskType.CHANGE

def test_routing_change_validation_failure():
    req = AnalysisRequest(
        query="What changed between these images?",
        inputs=[InputItem(url="1.tif", type="image/tiff")],
        input_configuration=InputConfiguration(type=InputConfigType.SINGLE_IMAGE)
    )
    res = route_request(req)
    assert res.status == FailureStatus.TEMPORAL_PAIR_REQUIRED

def test_missing_specialist():
    registry._specialists = [] # Empty it out
    req = AnalysisRequest(
        query="Is there water?",
        inputs=[InputItem(url="1.tif", type="image/tiff")],
        input_configuration=InputConfiguration(type=InputConfigType.SINGLE_IMAGE)
    )
    res = route_request(req)
    assert res.status == FailureStatus.SPECIALIST_UNAVAILABLE
