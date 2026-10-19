from pydantic import BaseModel, Field
from typing import List
from app.schemas.common import TaskType, InputConfigType
from app.schemas.evidence import EvidenceType

class SpecialistCapability(BaseModel):
    capability_id: str
    name: str
    version: str
    model_id: str
    model_version: str
    tasks: List[TaskType]
    supported_tasks: List[TaskType]
    modalities: List[str]
    supported_modalities: List[str]
    input_configurations: List[InputConfigType] = Field(default_factory=list)
    supported_input_count: int = 1
    supported_formats: List[str] = Field(default_factory=list)
    evidence_types: List[EvidenceType] = Field(default_factory=list)
    supports_temporal: bool = False
    supports_optical_sar: bool = False
    requires_rs_adaptation: bool = False
    rs_adaptation_status: str = "NOT_AVAILABLE"
    adaptation_dataset: str = "TEST_ONLY"
    checkpoint_reference: str = "TEST_ONLY"
    status: str = "AVAILABLE"
    supports_confidence: bool = False
    supports_uncertainty: bool = False
