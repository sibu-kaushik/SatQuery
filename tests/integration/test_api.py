from fastapi.testclient import TestClient
from app.main import app
import json

client = TestClient(app)

def test_health_check():
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "service": "satquery-api", "version": "v1"}

def test_analyze_no_image():
    # File is required by FastAPI but if sent as empty list or not sent
    response = client.post("/api/v1/analyze", data={
        "query": "Is there water?",
        "input_configuration": json.dumps({"type": "SINGLE_IMAGE"})
    })
    # Our internal validator should catch NO_INPUT
    assert response.status_code == 200
    assert response.json()["status"] == "NO_INPUT"

def test_analyze_valid():
    response = client.post(
        "/api/v1/analyze",
        data={
            "query": "Is there water?",
            "input_configuration": json.dumps({"type": "SINGLE_IMAGE"})
        },
        files=[("files", ("test.tif", b"dummy content", "image/tiff"))]
    )
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "COMPLETED"
    assert data["response"]["task"] == "VQA"
    assert "run_id" in data
    
    # Check that GET /api/v1/runs/{run_id} works
    run_id = data["run_id"]
    run_response = client.get(f"/api/v1/runs/{run_id}")
    assert run_response.status_code == 200
    assert run_response.json()["status"] == "COMPLETED"

def test_analyze_validation_failure():
    # Empty query should fail validation layer
    response = client.post(
        "/api/v1/analyze",
        data={
            "query": "",
            "input_configuration": json.dumps({"type": "SINGLE_IMAGE"})
        },
        files=[("files", ("test.tif", b"dummy content", "image/tiff"))]
    )
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "EMPTY_QUERY"
    assert "run_id" in data
