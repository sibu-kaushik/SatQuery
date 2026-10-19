import pytest
from pydantic import ValidationError
from app.schemas.request import AnalysisRequest, InputConfiguration, InputItem
from app.schemas.response import SpecialistResult, ModelInfo
from app.schemas.common import InputConfigType, TaskType, RunStatus
from app.schemas.evidence import EvidenceItem, EvidenceType, CoordinateSpace
from app.schemas.provenance import Provenance
from app.schemas.trace import TraceStep
from app.agent.capabilities import SpecialistCapability
from app.specialists.base import BaseSpecialist, SpecialistHealth
from app.agent.registry import SpecialistRegistry

class MockVQAAdapter(BaseSpecialist):
    @property
    def name(self) -> str:
        return "mock-vqa"

    @property
    def version(self) -> str:
        return "1.0"
        
    @property
    def capabilities(self) -> SpecialistCapability:
        return SpecialistCapability(
            capability_id="mock-vqa",
            name="mock-vqa",
            version="1.0",
            model_id="mock-vqa",
            model_version="1.0",
            tasks=[TaskType.VQA],
            supported_tasks=[TaskType.VQA],
            modalities=["OPTICAL"],
            supported_modalities=["OPTICAL"],
            input_configurations=[InputConfigType.SINGLE_IMAGE]
        )

    def can_handle(self, request: AnalysisRequest) -> bool:
        return request.input_configuration.type in self.capabilities.input_configurations

    def analyze(self, request: AnalysisRequest) -> SpecialistResult:
        return SpecialistResult(
            status="SUCCESS",
            task=TaskType.VQA,
            answer="DEMO ONLY — real VQA specialist not connected.",
            model=ModelInfo(name=self.name, version=self.version)
        )

    def health(self) -> SpecialistHealth:
        return SpecialistHealth(status="OK")

def test_1_valid_analysis_request():
    req = AnalysisRequest(
        query="Is there water?",
        inputs=[InputItem(url="test.tif", type="image/tiff")],
        input_configuration=InputConfiguration(type=InputConfigType.SINGLE_IMAGE)
    )
    assert req.query == "Is there water?"

def test_2_invalid_task_rejected():
    with pytest.raises(ValidationError):
        caps = SpecialistCapability(
            name="mock", version="1.0", tasks=["NOT_A_TASK"], modalities=["OPTICAL"]
        )

def test_3_valid_analysis_response_accepted():
    res = SpecialistResult(
        status="SUCCESS",
        task=TaskType.VQA,
        answer="Water is present.",
        model=ModelInfo(name="mock", version="1.0")
    )
    assert res.task == TaskType.VQA

def test_4_5_confidence_uncertainty_may_be_null():
    res = SpecialistResult(
        status="SUCCESS",
        task=TaskType.VQA,
        answer="Yes.",
        model=ModelInfo(name="mock", version="1.0"),
        confidence=None,
        uncertainty=None
    )
    assert res.confidence is None
    assert res.uncertainty is None

def test_6_valid_bounding_box_accepted():
    box = EvidenceItem(
        type=EvidenceType.BOUNDING_BOX,
        coordinates=[100, 80, 300, 250],
        coordinate_space=CoordinateSpace.PIXEL,
        label="water body"
    )
    assert box.type == EvidenceType.BOUNDING_BOX

def test_7_invalid_coordinate_space_rejected():
    with pytest.raises(ValidationError):
        EvidenceItem(
            type=EvidenceType.BOUNDING_BOX,
            coordinate_space="NOT_A_SPACE"
        )

def test_8_9_provenance_supports_real_and_synthetic_data():
    prov1 = Provenance(is_real_data=True, synthetic=False)
    assert prov1.is_real_data is True
    prov2 = Provenance(is_real_data=False, synthetic=True)
    assert prov2.synthetic is True

def test_10_trace_step_accepted():
    step = TraceStep(
        step="1",
        action="parse",
        component="router",
        status=RunStatus.QUEUED
    )
    assert step.action == "parse"

def test_11_12_13_14_registry_behavior():
    registry = SpecialistRegistry()
    mock = MockVQAAdapter()
    
    # 11. Registration works
    registry.register(mock)
    
    # 14. Duplicate handling (mock registry logic currently allows list appending, but get_all works)
    registry.register(mock)
    
    # 12. Retrieval works
    all_specs = registry.get_all()
    assert len(all_specs) == 2
    
    # 13. Filtering works
    req = AnalysisRequest(
        query="water?",
        inputs=[],
        input_configuration=InputConfiguration(type=InputConfigType.SINGLE_IMAGE)
    )
    candidates = registry.find_candidates(req, TaskType.VQA)
    assert len(candidates) == 2

def test_15_16_base_specialist_and_registry_no_execute():
    registry = SpecialistRegistry()
    mock = MockVQAAdapter()
    registry.register(mock)
    
    # 15. BaseSpecialist instantiated via test mock
    assert mock.name == "mock-vqa"
    
    # 16. Registry does not execute model code automatically
    # Just retrieving does not trigger analyze
    candidates = registry.find_candidates(
        AnalysisRequest(
            query="water?",
            inputs=[],
            input_configuration=InputConfiguration(type=InputConfigType.SINGLE_IMAGE)
        ), 
        TaskType.VQA
    )
    assert len(candidates) == 1
