import pytest
from app.agent.router import route_request
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
            name=self.name, version="1.0",
            tasks=[self._task], modalities=["OPTICAL", "SAR"],
            input_configurations=[InputConfigType.SINGLE_IMAGE, InputConfigType.BI_TEMPORAL, InputConfigType.OPTICAL_SAR]
        )
    def can_handle(self, request: AnalysisRequest) -> bool: return True
    def analyze(self, request: AnalysisRequest): raise Exception("Should not execute!")
    def health(self) -> SpecialistHealth: return SpecialistHealth(status="OK")

@pytest.fixture(autouse=True)
def setup_integration_registry():
    registry._specialists = []
    registry.register(MockAdapter(TaskType.VQA, "mock-vqa"))
    registry.register(MockAdapter(TaskType.GROUNDING, "mock-grounding"))
    registry.register(MockAdapter(TaskType.CHANGE, "mock-change"))
    registry.register(MockAdapter(TaskType.OPTICAL_SAR, "mock-optical-sar"))

def test_1():
    req = AnalysisRequest(query="Is there water?", inputs=[InputItem(url="1.tif", type="image/tiff")], input_configuration=InputConfiguration(type=InputConfigType.SINGLE_IMAGE))
    res = route_request(req)
    assert res.task == TaskType.VQA and res.status == "PLANNING"

def test_2():
    req = AnalysisRequest(query="Where is the water?", inputs=[InputItem(url="1.tif", type="image/tiff")], input_configuration=InputConfiguration(type=InputConfigType.SINGLE_IMAGE))
    res = route_request(req)
    assert res.task == TaskType.GROUNDING and res.status == "PLANNING"

def test_3():
    req = AnalysisRequest(query="Highlight the water body.", inputs=[InputItem(url="1.tif", type="image/tiff")], input_configuration=InputConfiguration(type=InputConfigType.SINGLE_IMAGE))
    res = route_request(req)
    assert res.task == TaskType.GROUNDING

def test_4():
    req = AnalysisRequest(query="What changed?", inputs=[InputItem(url="1.tif", type="image/tiff"), InputItem(url="2.tif", type="image/tiff")], input_configuration=InputConfiguration(type=InputConfigType.BI_TEMPORAL))
    res = route_request(req)
    assert res.task == TaskType.CHANGE

def test_5():
    req = AnalysisRequest(query="Use optical and SAR together.", inputs=[InputItem(url="1.tif", type="image/tiff", metadata={"modality":"OPTICAL"}), InputItem(url="2.tif", type="image/tiff", metadata={"modality":"SAR"})], input_configuration=InputConfiguration(type=InputConfigType.OPTICAL_SAR))
    res = route_request(req)
    assert res.task == TaskType.OPTICAL_SAR

def test_6():
    req = AnalysisRequest(query="What changed between these images?", inputs=[InputItem(url="1.tif", type="image/tiff")], input_configuration=InputConfiguration(type=InputConfigType.SINGLE_IMAGE))
    res = route_request(req)
    assert res.status == FailureStatus.TEMPORAL_PAIR_REQUIRED

def test_7():
    req = AnalysisRequest(query="test", inputs=[InputItem(url="1.tif", type="image/tiff")], input_configuration=InputConfiguration(type=InputConfigType.BI_TEMPORAL))
    res = route_request(req)
    assert res.status == "INVALID_INPUT_COUNT"

def test_8():
    req = AnalysisRequest(query="Use optical and SAR together.", inputs=[InputItem(url="1.tif", type="image/tiff", metadata={"modality":"OPTICAL"}), InputItem(url="2.tif", type="image/tiff", metadata={"modality":"OPTICAL"})], input_configuration=InputConfiguration(type=InputConfigType.OPTICAL_SAR))
    res = route_request(req)
    assert res.status == "MISSING_MODALITY"

def test_9():
    req = AnalysisRequest(query="", inputs=[InputItem(url="1.tif", type="image/tiff")], input_configuration=InputConfiguration(type=InputConfigType.SINGLE_IMAGE))
    res = route_request(req)
    assert res.status == "EMPTY_QUERY"

def test_10():
    req = AnalysisRequest(query="water?", inputs=[], input_configuration=InputConfiguration(type=InputConfigType.SINGLE_IMAGE))
    res = route_request(req)
    assert res.status == "NO_INPUT"

def test_11():
    registry._specialists = []
    req = AnalysisRequest(query="Is there water?", inputs=[InputItem(url="1.tif", type="image/tiff")], input_configuration=InputConfiguration(type=InputConfigType.SINGLE_IMAGE))
    res = route_request(req)
    assert res.status == FailureStatus.SPECIALIST_UNAVAILABLE

def test_12():
    # router must never execute specialist code
    req = AnalysisRequest(query="Is there water?", inputs=[InputItem(url="1.tif", type="image/tiff")], input_configuration=InputConfiguration(type=InputConfigType.SINGLE_IMAGE))
    res = route_request(req) # if it executed, it would raise Exception("Should not execute!")
    assert res.status == "PLANNING"
