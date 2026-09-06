"""HTTP-level tests for the FastAPI adapter using controlled service boundaries."""

from fastapi.testclient import TestClient

from src.api.main import app


client = TestClient(app)


def test_root_points_to_api_resources():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json()["docs"] == "/docs"


def test_health_reports_component_status(monkeypatch):
    from src.api.routes import health

    monkeypatch.setattr(health, "_dependency_status", lambda: {"api": "healthy", "face_service": "available", "search_service": "unavailable", "blockchain": "unavailable"})
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "degraded"
    assert response.json()["components"]["blockchain"] == "unavailable"


def test_pipeline_requires_an_image():
    response = client.post("/pipeline/run")
    assert response.status_code == 400
    assert response.json()["error"]["code"] == "INVALID_REQUEST"


def test_pipeline_route_returns_service_result(monkeypatch):
    from src.api.routes import pipeline

    async def fake_run(_upload, top_k=None, threshold=None, metadata=None):
        return {"pipeline_id": "runtime-id", "status": "completed", "search": {"search_id": "search-id", "timestamp": "now", "provider": "authorized", "candidate_count": 0, "results": []}}

    monkeypatch.setattr(pipeline, "run_uploaded_pipeline", fake_run)
    response = client.post("/pipeline/run", files={"image": ("face.jpg", b"bytes", "image/jpeg")})
    assert response.status_code == 200
    assert response.json()["pipeline_id"] == "runtime-id"
    assert response.headers["x-request-id"]


def test_face_route_returns_service_result(monkeypatch):
    from src.api.routes import face

    async def fake_analyze(_upload):
        return {"face_detected": True, "face_count": 1, "detection_confidence": 0.91, "embedding_dimension": 512}

    monkeypatch.setattr(face, "analyze_uploaded_face", fake_analyze)
    response = client.post("/face/analyze", files={"file": ("face.jpg", b"bytes", "image/jpeg")})
    assert response.status_code == 200
    assert response.json()["face_count"] == 1


def test_verify_route_rejects_non_json(monkeypatch):
    response = client.post("/verify", files={"file": ("evidence.json", b"not-json", "application/json")})
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "INVALID_EVIDENCE"


def test_verify_route_returns_service_result(monkeypatch):
    from src.api.routes import verification

    monkeypatch.setattr(verification, "verify_evidence_object", lambda _payload: {"verified": False, "status": "TAMPER DETECTED", "local_hash": "hash", "on_chain_exists": True})
    response = client.post("/verify", files={"file": ("evidence.json", b"{}", "application/json")})
    assert response.status_code == 200
    assert response.json()["status"] == "TAMPER DETECTED"
