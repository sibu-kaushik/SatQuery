from typing import List, Optional
from app.specialists.base import BaseSpecialist
from app.schemas.request import AnalysisRequest
from app.schemas.common import TaskType

class SpecialistRegistry:
    def __init__(self):
        self._specialists: List[BaseSpecialist] = []

    def register(self, specialist: BaseSpecialist):
        self._specialists.append(specialist)

    def get_all(self) -> List[BaseSpecialist]:
        return self._specialists

    def get(self, name: str, version: str) -> Optional[BaseSpecialist]:
        for s in self._specialists:
            if s.name == name and s.version == version:
                return s
        return None
        
    def find_candidates(self, request: AnalysisRequest, task: TaskType) -> List[BaseSpecialist]:
        """
        Finds specialists capable of handling the request for a given task.
        """
        candidates = []
        for specialist in self._specialists:
            if task in specialist.capabilities.tasks and specialist.can_handle(request):
                candidates.append(specialist)
        return candidates

# Global registry instance
registry = SpecialistRegistry()
