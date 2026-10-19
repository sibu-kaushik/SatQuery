from pydantic import BaseModel, Field
from typing import Optional, List, Any

class Provenance(BaseModel):
    source_type: Optional[str] = None
    dataset: Optional[str] = None
    sample_id: Optional[str] = None
    file_name: Optional[str] = None
    file_hash: Optional[str] = None
    modality: Optional[str] = None
    bands: Optional[List[str]] = None
    preprocessing_version: Optional[str] = None
    model: Optional[str] = None
    checkpoint: Optional[str] = None
    is_real_data: bool = False
    synthetic: bool = False
    metadata: Optional[dict[str, Any]] = Field(default_factory=dict)
