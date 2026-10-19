from app.specialists.base import BaseSpecialist, SpecialistHealth
from app.agent.capabilities import SpecialistCapability
from app.schemas.request import AnalysisRequest
from app.schemas.response import SpecialistResult, ModelInfo
from app.schemas.common import TaskType, InputConfigType
from app.schemas.provenance import Provenance

class TestChangeSpecialist(BaseSpecialist):
    @property
    def name(self) -> str:
        return "test-change"

    @property
    def version(self) -> str:
        return "test"

    @property
    def capabilities(self) -> SpecialistCapability:
        return SpecialistCapability(
            capability_id="satquery.change",
            name=self.name,
            version=self.version,
            model_id="mock-change-model",
            model_version="1.0",
            tasks=[TaskType.CHANGE],
            supported_tasks=[TaskType.CHANGE],
            modalities=["OPTICAL"],
            supported_modalities=["OPTICAL"],
            input_configurations=[InputConfigType.BI_TEMPORAL],
            supported_input_count=2,
            supports_temporal=True,
            requires_rs_adaptation=False,
            status="AVAILABLE"
        )

    def can_handle(self, request: AnalysisRequest) -> bool:
        return request.input_configuration.type == InputConfigType.BI_TEMPORAL

    def analyze(self, request: AnalysisRequest) -> SpecialistResult:
        return SpecialistResult(
            status="SUCCESS",
            task=TaskType.CHANGE,
            answer="TEST_ONLY_RESULT",
            model=ModelInfo(name=self.name, version=self.version),
            confidence=None,
            evidence=[],
            provenance=Provenance(synthetic=True, is_real_data=False)
        )

    def health(self) -> SpecialistHealth:
        return SpecialistHealth(status="OK")
