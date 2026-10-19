from app.vlm_service import get_vlm_engine
from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Optional
import uuid
import json
import time

from app.schemas.request import AnalysisRequest, InputConfiguration, InputItem
from app.schemas.common import RunStatus, TaskType, InputConfigType, FailureStatus
from app.schemas.execution import ExecutionResult
from app.schemas.trace import ExecutionTrace, TraceStep
from app.store import run_store
from app.agent.router import route_request
from app.agent.executor import execute_specialist
from app.agent.registry import registry
from app.specialists.test_doubles.vqa import TestVQASpecialist
from app.specialists.test_doubles.grounding import TestGroundingSpecialist
from app.specialists.test_doubles.change import TestChangeSpecialist
from app.specialists.test_doubles.optical_sar import TestOpticalSARSpecialist

# Register test doubles for Phase 4 MVP
registry.register(TestVQASpecialist())
registry.register(TestGroundingSpecialist())
registry.register(TestChangeSpecialist())
registry.register(TestOpticalSARSpecialist())

app = FastAPI(title="SatQuery AI API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # In production, restrict this
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/api/v1/health")
async def health_check():
    return {
        "status": "ok",
        "service": "satquery-api",
        "version": "v1"
    }

@app.post("/api/v1/analyze", response_model=ExecutionResult)
async def analyze(
    query: str = Form(default=""),
    input_configuration: str = Form(...),
    files: List[UploadFile] = File(default=[])
):
    run_id = str(uuid.uuid4())
    start_time = int(time.time() * 1000)
    
    # Create initial run state
    initial_trace = ExecutionTrace(run_id=run_id, steps=[TraceStep(step="0", action="QUEUED", component="api", status=RunStatus.QUEUED)], total_time_ms=0)
    initial_state = ExecutionResult(run_id=run_id, status=RunStatus.QUEUED, trace=initial_trace)
    run_store.create_run(run_id, initial_state)
    
    # Parse input config
    try:
        config_dict = json.loads(input_configuration)
        config = InputConfiguration(**config_dict)
    except Exception as e:
        err_res = ExecutionResult(
            run_id=run_id, status=FailureStatus.INTERNAL_ERROR,
            trace=initial_trace, errors=[f"Invalid input_configuration JSON: {str(e)}"]
        )
        run_store.update_run(run_id, err_res)
        return err_res

    # Construct request
    # For MVP, we use the filename as URL, because we are not doing deep raster parsing or real processing yet
    inputs = []
    for f in files:
        # In a real app we'd save to disk/S3 here
        inputs.append(InputItem(url=f.filename, type=f.content_type or "image/tiff"))

    request = AnalysisRequest(
        query=query,
        input_configuration=config,
        inputs=inputs
    )

    # 3. Route
    route_res = route_request(request)
    
    if route_res.status not in ["PLANNING"]:
        # Means routing failed (e.g. VALIDATION_FAILED, SPECIALIST_UNAVAILABLE, etc)
        err_res = ExecutionResult(
            run_id=run_id, status=route_res.status,
            trace=ExecutionTrace(run_id=run_id, steps=[
                TraceStep(step="1", action="ROUTING_FAILED", component="router", status=route_res.status, details={"reason": route_res.reason})
            ], total_time_ms=int(time.time() * 1000) - start_time),
            errors=[route_res.reason]
        )
        run_store.update_run(run_id, err_res)
        return err_res

    from app.agent.executor import execute_plan
    
    # 4. Execute
    exec_res = execute_plan(request, route_res.plan, run_id=run_id)
    
    run_store.update_run(run_id, exec_res)
    return exec_res

@app.get("/api/v1/runs/{run_id}", response_model=ExecutionResult)
async def get_run(run_id: str):
    run = run_store.get_run(run_id)
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")
    return run


# --- SatQuery VLM Inference Route ---
@app.post("/api/analyze")
async def analyze_satellite_tile(
    file: UploadFile = File(...),
    query: str = Form(...),
    mode: str = Form("grounding")
):
    if not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="File must be an image.")

    image_bytes = await file.read()

    try:
        engine = get_vlm_engine()
        result = engine.run_inference(
            image_bytes=image_bytes,
            user_query=query,
            mode=mode
        )
        return {"status": "success", "data": result}
    except Exception as e:                                                                                                                              
        raise HTTPException(status_code=500, detail=str(e))     