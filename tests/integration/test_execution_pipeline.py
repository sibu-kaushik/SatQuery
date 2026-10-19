import pytest
from app.schemas.request import AnalysisRequest, InputConfiguration, InputItem
from app.schemas.common import InputConfigType, TaskType, RunStatus
from app.agent.router import route_request
from app.agent.executor import execute_specialist
from app.agent.registry import registry
from app.specialists.test_doubles.vqa import TestVQASpecialist
from app.specialists.test_doubles.grounding import TestGroundingSpecialist
from app.specialists.test_doubles.change import TestChangeSpecialist
from app.specialists.test_doubles.optical_sar import TestOpticalSARSpecialist

@pytest.fixture(autouse=True)
def setup_integration_registry():
    registry._specialists = []
    registry.register(TestVQASpecialist())
    registry.register(TestGroundingSpecialist())
    registry.register(TestChangeSpecialist())
    registry.register(TestOpticalSARSpecialist())

def test_full_pipeline_vqa():
    req = AnalysisRequest(
        query="Is there water?",
        inputs=[InputItem(url="1.tif", type="image/tiff")],
        input_configuration=InputConfiguration(type=InputConfigType.SINGLE_IMAGE)
    )
    
    # Router
    route_res = route_request(req)
    assert route_res.status == "PLANNING"
    assert route_res.task == TaskType.VQA
    assert len(route_res.candidates) > 0
    
    candidate = route_res.candidates[0]
    
    # Executor
    exec_res = execute_specialist(req, route_res.task, candidate)
    
    assert exec_res.status == RunStatus.COMPLETED
    assert exec_res.response.task == TaskType.VQA
    assert exec_res.response.answer == "TEST_ONLY_RESULT"
    assert exec_res.response.model.name == "test-vqa"
    assert exec_res.response.provenance.synthetic is True
    
    # Check trace
    actions = [s.action for s in exec_res.trace.steps]
    assert "INPUT_VALIDATION" in actions
    assert "SPECIALIST_EXECUTION_COMPLETED" in actions

def test_full_pipeline_change():
    req = AnalysisRequest(
        query="What changed?",
        inputs=[
            InputItem(url="1.tif", type="image/tiff"),
            InputItem(url="2.tif", type="image/tiff")
        ],
        input_configuration=InputConfiguration(type=InputConfigType.BI_TEMPORAL)
    )
    
    route_res = route_request(req)
    assert route_res.task == TaskType.CHANGE
    
    exec_res = execute_specialist(req, route_res.task, route_res.candidates[0])
    
    assert exec_res.status == RunStatus.COMPLETED
    assert exec_res.response.task == TaskType.CHANGE
    assert exec_res.response.model.name == "test-change"
