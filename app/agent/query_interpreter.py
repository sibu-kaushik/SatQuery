from pydantic import BaseModel
from typing import Optional
from app.schemas.common import TaskType

class QueryInterpretation(BaseModel):
    task_hint: TaskType
    target: Optional[str] = None

def interpret_query(query: str) -> QueryInterpretation:
    query_lower = query.lower()
    
    # 4. Deterministic interpretation logic (no LLMs)
    
    # Check for Change
    if "change" in query_lower or "increase" in query_lower or "decrease" in query_lower:
        return QueryInterpretation(task_hint=TaskType.CHANGE, target=None)
        
    # Check for Optical-SAR explicitly requested together
    if "optical" in query_lower and "sar" in query_lower:
        # Simplistic extraction of target
        target = None
        if "identify" in query_lower:
            parts = query_lower.split("identify")
            if len(parts) > 1:
                target = parts[1].split("using")[0].strip().strip(".")
        return QueryInterpretation(task_hint=TaskType.OPTICAL_SAR, target=target if target else "built-up areas")
        
    # Check for Grounding / localization
    spatial_keywords = ["where", "locate", "highlight", "show me where", "which region", "identify"]
    for keyword in spatial_keywords:
        if keyword in query_lower:
            # Attempt to extract target if possible, fallback to None
            target = query_lower.replace(keyword, "").replace("is the", "").replace("is", "").strip().strip("?")
            if not target:
                target = None
            return QueryInterpretation(task_hint=TaskType.GROUNDING, target=target)
            
    # Check for VQA (fallback for single image queries basically)
    # Check "is there", "does this", etc.
    return QueryInterpretation(task_hint=TaskType.VQA, target=None)
