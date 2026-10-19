from app.schemas.request import AnalysisRequest, InputConfiguration, InputItem
from app.schemas.common import TaskType, InputConfigType
from app.agent.executor import execute_specialist
from app.specialists.base import BaseSpecialist, SpecialistCapability

class ExplodingSpecialist(BaseSpecialist):
    @property
    def name(self) -> str: return "Exploder"
    @property
    def version(self) -> str: return "1.0"
    @property
    def capabilities(self) -> SpecialistCapability:
        return SpecialistCapability(
            capability_id="exploder", name=self.name, version=self.version,
            model_id="exp", model_version="1.0", tasks=[TaskType.VQA], supported_tasks=[TaskType.VQA], modalities=["OPTICAL"], supported_modalities=["OPTICAL"]
        )
    def can_handle(self, request): return getattr(request, 'task', None) == TaskType.VQA or request.input_configuration.type == InputConfigType.SINGLE_IMAGE
    def analyze(self, request):
        raise ValueError("Internal CUDA out of memory")
    def health(self):
        from app.specialists.base import SpecialistHealth
        return SpecialistHealth(status="OK")

class UnavailableSpecialist(BaseSpecialist):
    @property
    def name(self) -> str: return "Unavailable"
    @property
    def version(self) -> str: return "1.0"
    @property
    def capabilities(self) -> SpecialistCapability:
        return SpecialistCapability(
            capability_id="unavail", name=self.name, version=self.version,
            model_id="un", model_version="1.0", tasks=[TaskType.VQA], supported_tasks=[TaskType.VQA], modalities=["OPTICAL"], supported_modalities=["OPTICAL"]
        )
    def can_handle(self, request): return getattr(request, 'task', None) == TaskType.VQA or request.input_configuration.type == InputConfigType.SINGLE_IMAGE
    def analyze(self, request):
        pass # Won't be called if health is False or we mock it
    def health(self):
        from app.specialists.base import SpecialistHealth
        return SpecialistHealth(status="UNAVAILABLE")

from app.agent.registry import registry
from app.agent.router import SpecialistCandidateInfo

def test_specialist_exception():
    req = AnalysisRequest(
        query="Test",
        input_configuration=InputConfiguration(type="SINGLE_IMAGE"),
        inputs=[InputItem(url="t.tif", type="image/tiff")]
    )
    spec = ExplodingSpecialist()
    registry.register(spec)
    try:
        res = execute_specialist(req, TaskType.VQA, SpecialistCandidateInfo(name=spec.name, version=spec.version), "run-err")
        assert res.status == "SPECIALIST_FAILED"
    finally:
        registry._specialists.remove(spec)

class RejectingSpecialist(BaseSpecialist):
    @property
    def name(self) -> str: return "Rejecter"
    @property
    def version(self) -> str: return "1.0"
    @property
    def capabilities(self) -> SpecialistCapability:
        return SpecialistCapability(
            capability_id="rej", name=self.name, version=self.version,
            model_id="rej", model_version="1.0", tasks=[TaskType.VQA], supported_tasks=[TaskType.VQA], modalities=["OPTICAL"], supported_modalities=["OPTICAL"]
        )
    def can_handle(self, request): return False
    def analyze(self, request): pass
    def health(self):
        from app.specialists.base import SpecialistHealth
        return SpecialistHealth(status="OK")

def test_unsupported_task():
    req = AnalysisRequest(
        query="Test",
        input_configuration=InputConfiguration(type="SINGLE_IMAGE"),
        inputs=[InputItem(url="t.tif", type="image/tiff")]
    )
    spec = RejectingSpecialist()
    registry.register(spec)
    try:
        res = execute_specialist(req, TaskType.CHANGE, SpecialistCandidateInfo(name=spec.name, version=spec.version), "run-err2")
        assert res.status == "UNSUPPORTED_TASK"
    finally:
        registry._specialists.remove(spec)
