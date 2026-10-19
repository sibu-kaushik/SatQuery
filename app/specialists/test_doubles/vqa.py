from app.specialists.base import BaseSpecialist, SpecialistHealth
from app.agent.capabilities import SpecialistCapability
from app.schemas.request import AnalysisRequest
from app.schemas.response import SpecialistResult, ModelInfo
from app.schemas.common import TaskType, InputConfigType
from app.schemas.provenance import Provenance

class TestVQASpecialist(BaseSpecialist):
    @property
    def name(self) -> str:
        return "test-vqa"

    @property
    def version(self) -> str:
        return "test"

    @property
    def capabilities(self) -> SpecialistCapability:
        return SpecialistCapability(
            capability_id="satquery.vqa",
            name=self.name,
            version=self.version,
            model_id="mock-vqa-model",
            model_version="1.0",
            tasks=[TaskType.VQA],
            supported_tasks=[TaskType.VQA],
            modalities=["OPTICAL"],
            supported_modalities=["OPTICAL"],
            input_configurations=[InputConfigType.SINGLE_IMAGE],
            supported_input_count=1,
            requires_rs_adaptation=False,
            status="AVAILABLE"
        )

    def can_handle(self, request: AnalysisRequest) -> bool:
        return request.input_configuration.type == InputConfigType.SINGLE_IMAGE

    def analyze(self, request: AnalysisRequest) -> SpecialistResult:
        return SpecialistResult(
            status="SUCCESS",
            task=TaskType.VQA,
            answer="TEST_ONLY_RESULT",
            model=ModelInfo(name=self.name, version=self.version),
            confidence=None,
            evidence=[],
            provenance=Provenance(synthetic=True, is_real_data=False)
        )

    def health(self) -> SpecialistHealth:
        return SpecialistHealth(status="OK")
