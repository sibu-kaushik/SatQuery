from typing import Dict
from app.schemas.execution import ExecutionResult

class RunStore:
    def __init__(self):
        self._runs: Dict[str, ExecutionResult] = {}

    def create_run(self, run_id: str, initial_state: ExecutionResult):
        self._runs[run_id] = initial_state

    def update_run(self, run_id: str, result: ExecutionResult):
        self._runs[run_id] = result

    def get_run(self, run_id: str) -> ExecutionResult | None:
        return self._runs.get(run_id)

# In-memory global instance for MVP
run_store = RunStore()
