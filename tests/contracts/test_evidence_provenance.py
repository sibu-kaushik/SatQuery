from app.schemas.response import SpecialistResult, ModelInfo, Provenance, EvidenceItem
from app.schemas.common import TaskType
from app.schemas.request import AnalysisRequest, InputConfiguration, InputItem
from app.agent.executor import execute_specialist
from app.specialists.base import BaseSpecialist, SpecialistCapability

def test_evidence_compatibility():
    """
    Test that different types of evidence flow through the same generic schema seamlessly.
    """
    # 1. Grounding Evidence
    bbox_evidence = EvidenceItem(
        type="BOUNDING_BOX",
        coordinate_space="PIXEL",
        coordinates=[10, 10, 50, 50],
        label="water body"
    )
    
    # 2. Change Evidence
    change_evidence = EvidenceItem(
        type="CHANGE_MAP",
        mask_url="s3://satquery/masks/123.tif"
    )
    
    # 3. Optical-SAR Evidence
    modality_evidence = EvidenceItem(
        type="TEXT",
        label="SAR reflection high"
    )
    
    # Prove they can all coexist in the same list and pass validation
    result = SpecialistResult(
        status="COMPLETED",
        task=TaskType.OPTICAL_SAR,
        answer="Found evidence.",
        model=ModelInfo(name="Test", version="1.0"),
        confidence=0.8,
        evidence=[bbox_evidence, change_evidence, modality_evidence],
        provenance=Provenance(synthetic=True, is_real_data=False)
    )
    
    assert len(result.evidence) == 3
    assert result.evidence[0].type == "BOUNDING_BOX"
    assert result.evidence[1].type == "CHANGE_MAP"
    assert result.evidence[2].type == "TEXT"

def test_provenance_immutability():
    """
    Verify the executor does not overwrite or confuse provenance values.
    """
    class ProvenanceSpecialist(BaseSpecialist):
        @property
        def name(self) -> str: return "ProvSpec"
        @property
        def version(self) -> str: return "1.0"
        @property
        def capabilities(self) -> SpecialistCapability:
            return SpecialistCapability(
                capability_id="provspec", name=self.name, version=self.version,
                model_id="prov", model_version="1.0",
                tasks=[TaskType.VQA], supported_tasks=[TaskType.VQA], modalities=["OPTICAL"], supported_modalities=["OPTICAL"]
            )
        def can_handle(self, request): return True
        def analyze(self, request) -> SpecialistResult:
            return SpecialistResult(
                status="COMPLETED",
                task=TaskType.VQA,
                answer="Answer",
                model=ModelInfo(name="ProvSpec", version="1.0"),
                confidence=0.9,
                evidence=[],
                provenance=Provenance(synthetic=False, is_real_data=True, dataset="S2-TEST", file_hash="abc")
            )
        def health(self) -> bool: return True

    req = AnalysisRequest(
        query="Test",
        input_configuration=InputConfiguration(type="SINGLE_IMAGE"),
        inputs=[InputItem(url="t.tif", type="image/tiff")]
    )
    
    from app.agent.registry import registry
    from app.agent.router import SpecialistCandidateInfo
    spec = ProvenanceSpecialist()
    registry.register(spec)
    try:
        exec_res = execute_specialist(req, TaskType.VQA, SpecialistCandidateInfo(name=spec.name, version=spec.version), "run-prov")
        assert exec_res.status == "COMPLETED"
    finally:
        registry._specialists.remove(spec)
    
    assert exec_res.response.provenance.is_real_data is True
    assert exec_res.response.provenance.synthetic is False
    assert exec_res.response.provenance.dataset == "S2-TEST"
    assert exec_res.response.provenance.file_hash == "abc"
