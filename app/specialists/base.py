from abc import ABC, abstractmethod
from pydantic import BaseModel
from app.schemas.request import AnalysisRequest
from app.schemas.response import SpecialistResult
from app.agent.capabilities import SpecialistCapability

class SpecialistHealth(BaseModel):
    status: str
    details: str = ""

class BaseSpecialist(ABC):
    
    @property
    @abstractmethod
    def name(self) -> str:
        """Name of the specialist."""
        pass

    @property
    @abstractmethod
    def version(self) -> str:
        """Version of the specialist."""
        pass
        
    @property
    @abstractmethod
    def capabilities(self) -> SpecialistCapability:
        """The capabilities this specialist supports."""
        pass

    @abstractmethod
    def can_handle(self, request: AnalysisRequest) -> bool:
        """Determine if this specialist can handle the given request."""
        pass

    @abstractmethod
    def analyze(self, request: AnalysisRequest) -> SpecialistResult:
        """Execute the analysis."""
        pass

    @abstractmethod
    def health(self) -> SpecialistHealth:
        """Check the health status of the specialist."""
        pass
