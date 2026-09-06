"""Secure request handling around the existing TraceChain pipeline."""

import json
import tempfile
from pathlib import Path
from typing import Any

from fastapi import UploadFile
from fastapi.encoders import jsonable_encoder

from src.api.errors import ApiFailure
from src.config import settings
from src.face.detector import detect_face, detect_faces, get_face_app
from src.face.encoder import extract_embedding
from src.face.quality import validate_image
from src.main import run_pipeline
from src.search.orchestrator import SearchError


def _suffix(upload: UploadFile) -> str:
    suffix = Path(upload.filename or "").suffix.lower()
    if suffix not in settings.IMAGE_EXTENSIONS:
        raise ApiFailure("INVALID_IMAGE_TYPE", "Only configured image formats are accepted.", 400)
    return suffix


async def save_upload(upload: UploadFile) -> Path:
    """Write an upload to a unique temporary file after enforcing its size."""
    suffix = _suffix(upload)
    total = 0
    temporary = tempfile.NamedTemporaryFile(prefix="tracechain-", suffix=suffix, delete=False)
    path = Path(temporary.name)
    try:
        with temporary:
            while chunk := await upload.read(1024 * 1024):
                total += len(chunk)
                if total > settings.API_MAX_UPLOAD_BYTES:
                    raise ApiFailure("FILE_TOO_LARGE", "The uploaded image exceeds the configured size limit.", 413)
                temporary.write(chunk)
    except Exception:
        path.unlink(missing_ok=True)
        raise
    finally:
        await upload.close()
    return path


def _json_object(value: Any) -> dict[str, Any] | None:
    if value is None:
        return None
    if isinstance(value, str):
        try:
            value = json.loads(value)
        except json.JSONDecodeError as exc:
            raise ApiFailure("INVALID_METADATA", "Metadata must be a JSON object.", 422) from exc
    if not isinstance(value, dict):
        raise ApiFailure("INVALID_METADATA", "Metadata must be a JSON object.", 422)
    return value


def analyze_face(image_path: Path) -> dict[str, Any]:
    try:
        image, quality = validate_image(image_path)
        faces = detect_faces(image)
        if not faces:
            raise ApiFailure("FACE_NOT_DETECTED", "No face could be detected in the uploaded image.", 422)
        selected = detect_face(image_path)
        embedding = extract_embedding(image_path)
    except ApiFailure:
        raise
    except Exception as exc:
        message = str(exc)
        code = "FACE_NOT_DETECTED" if "No face" in message else "FACE_PROCESSING_FAILED"
        raise ApiFailure(code, message, 422 if code == "FACE_NOT_DETECTED" else 503) from exc
    return {
        "face_detected": True,
        "face_count": len(faces),
        "detection_confidence": selected.detection_confidence,
        "embedding_dimension": int(embedding.size),
        "image_quality": {
            "width": quality.width,
            "height": quality.height,
            "brightness": quality.brightness,
            "sharpness": quality.sharpness,
            "quality_score": quality.quality_score,
        },
    }


def _pipeline_result(result: dict[str, Any]) -> dict[str, Any]:
    encoded = jsonable_encoder(result)
    encoded["status"] = "completed"
    return encoded


async def run_uploaded_pipeline(upload: UploadFile, top_k: int | None = None, threshold: float | None = None, metadata: str | None = None) -> dict[str, Any]:
    path = await save_upload(upload)
    try:
        query_metadata = _json_object(metadata)
        from src.config import settings as runtime
        return _pipeline_result(run_pipeline(path, top_k or runtime.TOP_K, threshold if threshold is not None else runtime.MATCH_THRESHOLD, query_metadata))
    except ApiFailure:
        raise
    except (FileNotFoundError, SearchError) as exc:
        raise ApiFailure("SEARCH_UNAVAILABLE", str(exc), 503) from exc
    except Exception as exc:
        message = str(exc)
        if "No candidate posts" in message or "No match" in message:
            raise ApiFailure("NO_MATCH_FOUND", message, 422) from exc
        if "blockchain" in message.lower() or "RPC" in message:
            raise ApiFailure("BLOCKCHAIN_UNAVAILABLE", "Blockchain registration could not be completed.", 503) from exc
        raise ApiFailure("PIPELINE_FAILED", message, 422) from exc
    finally:
        path.unlink(missing_ok=True)


async def analyze_uploaded_face(upload: UploadFile) -> dict[str, Any]:
    path = await save_upload(upload)
    try:
        return analyze_face(path)
    finally:
        path.unlink(missing_ok=True)


def verify_evidence_object(evidence: dict[str, Any]) -> dict[str, Any]:
    from src.blockchain.verifier import reverify_evidence

    try:
        return reverify_evidence(evidence)
    except Exception as exc:
        raise ApiFailure("VERIFICATION_FAILED", str(exc), 503) from exc
