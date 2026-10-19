from pydantic import BaseModel, Field
from typing import List, Optional, Any
from .common import InputConfigType

class InputItem(BaseModel):
    url: str
    type: str
    metadata: Optional[dict[str, Any]] = Field(default_factory=dict)

class InputConfiguration(BaseModel):
    type: InputConfigType
    metadata: Optional[dict[str, Any]] = Field(default_factory=dict)

class AnalysisRequest(BaseModel):
    query: str
    inputs: List[InputItem]
    input_configuration: InputConfiguration
