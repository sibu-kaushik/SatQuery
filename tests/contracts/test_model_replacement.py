from app.schemas.request import AnalysisRequest, InputConfiguration, InputItem
from app.schemas.response import SpecialistResult, ModelInfo, Provenance
from app.schemas.common import TaskType, InputConfigType
from app.agent.registry import registry
from app.agent.router import route_request
from app.agent.executor import execute_specialist
from app.specialists.base import BaseSpecialist, SpecialistCapability

class DummyVQAAdapterV1(BaseSpecialist):
    @property
    def name(self) -> str:
        return "DummyVQA"
    @property
    def version(self) -> str:
        return "1.0"
    @property
    def capabilities(self) -> SpecialistCapability:
        return SpecialistCapability(
            capability_id="v1", name=self.name, version=self.version,
            model_id="mock", model_version="1.0", tasks=[TaskType.VQA], supported_tasks=[TaskType.VQA], modalities=["OPTICAL"], supported_modalities=["OPTICAL"]
        )
    def can_handle(self, request): return True
    def analyze(self, request: AnalysisRequest) -> SpecialistResult:
        return SpecialistResult(
            status="COMPLETED",
            task=TaskType.VQA,
            answer="V1 Answer",
            model=ModelInfo(name=self.name, version=self.version),
            confidence=0.9,
            evidence=[],
            provenance=Provenance(synthetic=True, is_real_data=False)
        )
    def health(self) -> bool:
        return True

class DummyVQAAdapterV2(BaseSpecialist):
    @property
    def name(self) -> str:
        return "DummyVQA"
    @property
    def version(self) -> str:
        return "2.0"
    @property
    def capabilities(self) -> SpecialistCapability:
        return SpecialistCapability(
            capability_id="v2", name=self.name, version=self.version,
            model_id="mock", model_version="2.0", tasks=[TaskType.VQA], supported_tasks=[TaskType.VQA], modalities=["OPTICAL"], supported_modalities=["OPTICAL"]
        )
    def can_handle(self, request): return True
    def analyze(self, request: AnalysisRequest) -> SpecialistResult:
        return SpecialistResult(
            status="COMPLETED",
            task=TaskType.VQA,
            answer="V2 Answer",
            model=ModelInfo(name=self.name, version=self.version),
            confidence=0.95,
            evidence=[],
            provenance=Provenance(synthetic=True, is_real_data=False)
        )
    def health(self) -> bool:
        return True

def test_model_replacement():
    """
    Proves that upgrading a model does not require changing the agent router or executor.
    """
    req = AnalysisRequest(
        query="Is there water?",
        input_configuration=InputConfiguration(type=InputConfigType.SINGLE_IMAGE),
        inputs=[InputItem(url="test.tif", type="image/tiff")]
    )
    
    # 1. Register V1
    v1 = DummyVQAAdapterV1()
    registry.register(v1)
    
    route_res_v1 = route_request(req)
    assert route_res_v1.candidates[0].name == "DummyVQA"
    
    exec_v1 = execute_specialist(req, route_res_v1.task, route_res_v1.candidates[0], "run-v1")
    assert exec_v1.response.answer == "V1 Answer"
    assert exec_v1.response.model.version == "1.0"
    
    # 2. Replace with V2 (Simulate deploying a new model version)
    # Clear registry manually for test isolation
    registry._specialists = [s for s in registry._specialists if s.name != "DummyVQA"]
    
    v2 = DummyVQAAdapterV2()
    registry.register(v2)
    
    route_res_v2 = route_request(req)
    exec_v2 = execute_specialist(req, route_res_v2.task, route_res_v2.candidates[0], "run-v2")
    assert exec_v2.response.answer == "V2 Answer"
    assert exec_v2.response.model.version == "2.0"
    
    # Prove that the agent architecture required ZERO changes to handle the V2 upgrade
    assert exec_v1.status == "COMPLETED"
    assert exec_v2.status == "COMPLETED"

    # Cleanup registry
    registry._specialists = [s for s in registry._specialists if s.name != "DummyVQA"]
