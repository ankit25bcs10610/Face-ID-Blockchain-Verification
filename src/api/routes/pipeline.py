"""Full pipeline execution route."""

from fastapi import APIRouter, File, Form, UploadFile

from src.api.schemas import PipelineResponse
from src.services.pipeline_service import run_uploaded_pipeline

router = APIRouter(prefix="/pipeline", tags=["pipeline"])


@router.post("/run", response_model=PipelineResponse, summary="Run the complete TraceChain pipeline")
async def run(
    image: UploadFile | None = File(None, description="Authorized face image"),
    file: UploadFile | None = File(None, description="Compatibility alias for image"),
    top_k: int | None = Form(None, gt=0),
    threshold: float | None = Form(None, ge=0, le=1),
    metadata: str | None = Form(None, description="Optional query metadata JSON object"),
) -> PipelineResponse:
    upload = image or file
    if upload is None:
        from src.api.errors import ApiFailure
        raise ApiFailure("INVALID_REQUEST", "An image upload is required.", 400)
    return PipelineResponse(**await run_uploaded_pipeline(upload, top_k, threshold, metadata))
