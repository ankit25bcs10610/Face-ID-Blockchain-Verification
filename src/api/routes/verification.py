"""Evidence verification route."""

import json

from fastapi import APIRouter, File, UploadFile

from src.api.errors import ApiFailure
from src.api.schemas import VerificationResponse
from src.services.pipeline_service import verify_evidence_object

router = APIRouter(tags=["verification"])


@router.post("/verify", response_model=VerificationResponse, summary="Re-verify evidence against its on-chain record")
async def verify(file: UploadFile = File(..., description="Evidence JSON document")) -> VerificationResponse:
    try:
        content = await file.read()
        from src.config import settings
        if len(content) > settings.API_MAX_UPLOAD_BYTES:
            raise ApiFailure("FILE_TOO_LARGE", "The uploaded evidence exceeds the configured size limit.", 413)
        payload = json.loads(content.decode("utf-8"))
    except ApiFailure:
        raise
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ApiFailure("INVALID_EVIDENCE", "Evidence must be a UTF-8 JSON object.", 422) from exc
    finally:
        await file.close()
    if not isinstance(payload, dict):
        raise ApiFailure("INVALID_EVIDENCE", "Evidence must be a JSON object.", 422)
    return VerificationResponse(**verify_evidence_object(payload))
