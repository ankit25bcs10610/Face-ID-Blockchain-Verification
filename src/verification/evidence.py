"""Structured, deterministic evidence records for verified matches."""

import json
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from src.config import settings
from src.search.candidate_ranker import CandidatePost
from src.verification.matcher import MatchResult


class EvidenceError(ValueError):
    """Raised when evidence cannot be created or serialized."""


def _json_safe(value: Any) -> Any:
    try:
        json.dumps(value)
    except (TypeError, ValueError) as exc:
        raise EvidenceError(f"Evidence contains a non-JSON value: {exc}") from exc
    return value


def create_evidence(result: MatchResult, image_hash: str | None = None, search=None, threshold: float | None = None) -> dict:
    if not isinstance(result, MatchResult):
        raise EvidenceError("result must be a MatchResult")
    if not result.match:
        raise EvidenceError("Evidence can only be generated for a verified match")
    metadata = result.candidate.metadata
    evidence = {
        "version": settings.EVIDENCE_VERSION,
        "evidence_id": str(uuid.uuid4()),
        "search": {
            "search_id": getattr(search, "search_id", None),
            "provider": getattr(search, "provider", None),
        },
        "post_id": result.candidate.post_id,
        "platform": metadata.get("platform"),
        "post_url": metadata.get("post_url"),
        "caption": metadata.get("caption"),
        "timestamp": metadata.get("timestamp"),
        "image_hash": image_hash,
        "face_similarity": result.face_similarity,
        "image_similarity": result.image_similarity,
        "metadata_consistency": result.metadata_consistency,
        "final_confidence": result.confidence,
        "match_threshold": threshold if threshold is not None else settings.MATCH_THRESHOLD,
        "verification_timestamp": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
    }
    return _json_safe(evidence)


def canonicalize_evidence(evidence: dict) -> str:
    if not isinstance(evidence, dict):
        raise EvidenceError("Evidence must be a JSON object")
    try:
        return json.dumps(evidence, sort_keys=True, ensure_ascii=False, separators=(",", ":"), allow_nan=False)
    except (TypeError, ValueError) as exc:
        raise EvidenceError(f"Unable to canonicalize evidence: {exc}") from exc


def save_evidence(evidence: dict, evidence_path: str | Path | None = None) -> Path:
    path = Path(evidence_path) if evidence_path else Path(settings.EVIDENCE_DIR) / f"{evidence['evidence_id']}.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(canonicalize_evidence(evidence), encoding="utf-8")
    return path
