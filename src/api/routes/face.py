"""Independent face analysis route."""

from fastapi import APIRouter, File, UploadFile

from src.api.schemas import FaceAnalysisResponse
from src.services.pipeline_service import analyze_uploaded_face

router = APIRouter(prefix="/face", tags=["face"])


@router.post("/analyze", response_model=FaceAnalysisResponse, summary="Analyze a face image")
async def analyze(file: UploadFile = File(..., description="Authorized JPG, JPEG, or PNG face image")) -> FaceAnalysisResponse:
    return FaceAnalysisResponse(**await analyze_uploaded_face(file))
