"""Full pipeline execution routes."""

import asyncio
import json

from fastapi import APIRouter, File, Form, UploadFile
from fastapi.responses import StreamingResponse

from src.api.schemas import PipelineResponse
from src.services.pipeline_service import run_uploaded_pipeline, stream_uploaded_pipeline

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


@router.post("/stream", summary="Run the pipeline and stream each stage as it completes")
async def stream(
    image: UploadFile | None = File(None, description="Authorized face image"),
    file: UploadFile | None = File(None, description="Compatibility alias for image"),
    top_k: int | None = Form(None, gt=0),
    threshold: float | None = Form(None, ge=0, le=1),
    metadata: str | None = Form(None, description="Optional query metadata JSON object"),
) -> StreamingResponse:
    upload = image or file
    if upload is None:
        from src.api.errors import ApiFailure
        raise ApiFailure("INVALID_REQUEST", "An image upload is required.", 400)

    events = stream_uploaded_pipeline(upload, top_k, threshold, metadata)

    async def body():
        async for event in events:
            yield f"data: {json.dumps(event)}\n\n"
            # Flush promptly so the browser paints each stage as it lands.
            await asyncio.sleep(0)

    return StreamingResponse(
        body(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )
