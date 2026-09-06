"""Health and dependency status endpoint."""

import importlib.util
from pathlib import Path

from fastapi import APIRouter

from src.blockchain.client import connect_to_blockchain
from src.config import settings
from src.api.schemas import HealthResponse

router = APIRouter(tags=["health"])


def _dependency_status() -> dict[str, str]:
    face_status = "available" if importlib.util.find_spec("insightface") else "unavailable"
    search_index = Path(settings.FAISS_DIR) / settings.INDEX_NAME
    search_status = "available" if search_index.is_file() else "unavailable"
    blockchain_status = "unavailable"
    if settings.BLOCKCHAIN_RPC_URL:
        try:
            connect_to_blockchain()
            blockchain_status = "available"
        except Exception:
            blockchain_status = "unavailable"
    return {"api": "healthy", "face_service": face_status, "search_service": search_status, "blockchain": blockchain_status}


@router.get("/health", response_model=HealthResponse, summary="Check API and dependency health")
def health() -> HealthResponse:
    components = _dependency_status()
    status = "healthy" if all(value in {"healthy", "available"} for value in components.values()) else "degraded"
    return HealthResponse(status=status, service="TraceChain AI API", components=components)
