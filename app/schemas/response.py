from pydantic import BaseModel, Field
from typing import List, Optional, Any
from .common import TaskType
from .evidence import EvidenceItem
from .provenance import Provenance
from .trace import ExecutionTrace

class ModelInfo(BaseModel):
    name: str
    version: str
    checkpoint: Optional[str] = None
    adapter: Optional[str] = None
    provider: Optional[str] = None
    metadata: Optional[dict[str, Any]] = Field(default_factory=dict)

class SpecialistResult(BaseModel):
    status: str
    task: TaskType
    answer: str
    model: ModelInfo
    confidence: Optional[float] = None
    uncertainty: Optional[float] = None
    evidence: List[EvidenceItem] = Field(default_factory=list)
    provenance: Optional[Provenance] = None
    execution_trace: Optional[ExecutionTrace] = None
    warnings: List[str] = Field(default_factory=list)
    timing: dict[str, Any] = Field(default_factory=dict)
