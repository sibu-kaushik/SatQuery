from enum import Enum
from typing import List, Optional, Any
from pydantic import BaseModel, Field

class EvidenceType(str, Enum):
    TEXT = "TEXT"
    BOUNDING_BOX = "BOUNDING_BOX"
    POLYGON = "POLYGON"
    MASK = "MASK"
    POINT = "POINT"
    CHANGE_REGION = "CHANGE_REGION"
    CHANGE_MAP = "CHANGE_MAP"
    HEATMAP = "HEATMAP"
    MODALITY_EVIDENCE = "MODALITY_EVIDENCE"
    IMAGE_REGION = "IMAGE_REGION"

class CoordinateSpace(str, Enum):
    PIXEL = "PIXEL"
    NORMALIZED = "NORMALIZED"
    GEO = "GEO"

class EvidenceItem(BaseModel):
    type: EvidenceType
    coordinates: Optional[List[float]] = None
    coordinate_space: Optional[CoordinateSpace] = None
    label: Optional[str] = None
    score: Optional[float] = None
    metadata: Optional[dict[str, Any]] = Field(default_factory=dict)
