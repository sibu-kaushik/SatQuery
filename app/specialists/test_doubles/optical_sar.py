from app.specialists.base import BaseSpecialist, SpecialistHealth
from app.agent.capabilities import SpecialistCapability
from app.schemas.request import AnalysisRequest
from app.schemas.response import SpecialistResult, ModelInfo
from app.schemas.common import TaskType, InputConfigType
from app.schemas.provenance import Provenance

class TestOpticalSARSpecialist(BaseSpecialist):
    @property
    def name(self) -> str:
        return "test-optical-sar"

    @property
    def version(self) -> str:
        return "test"

    @property
    def capabilities(self) -> SpecialistCapability:
        return SpecialistCapability(
            capability_id="satquery.optical_sar",
            name=self.name,
            version=self.version,
            model_id="mock-optical-sar-model",
            model_version="1.0",
            tasks=[TaskType.OPTICAL_SAR],
            supported_tasks=[TaskType.OPTICAL_SAR],
            modalities=["OPTICAL", "SAR"],
            supported_modalities=["OPTICAL", "SAR"],
            input_configurations=[InputConfigType.OPTICAL_SAR],
            supported_input_count=2,
            supports_optical_sar=True,
            requires_rs_adaptation=False,
            status="AVAILABLE"
        )

    def can_handle(self, request: AnalysisRequest) -> bool:
        return request.input_configuration.type == InputConfigType.OPTICAL_SAR

    def analyze(self, request: AnalysisRequest) -> SpecialistResult:
        return SpecialistResult(
            status="SUCCESS",
            task=TaskType.OPTICAL_SAR,
            answer="TEST_ONLY_RESULT",
            model=ModelInfo(name=self.name, version=self.version),
            confidence=None,
            evidence=[],
            provenance=Provenance(synthetic=True, is_real_data=False)
        )

    def health(self) -> SpecialistHealth:
        return SpecialistHealth(status="OK")
