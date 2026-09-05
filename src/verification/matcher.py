"""Multi-signal verification of a candidate post."""

from dataclasses import dataclass
from pathlib import Path

import imagehash
from PIL import Image

from src.config import settings
from src.search.candidate_ranker import CandidatePost


class MatchVerificationError(ValueError):
    """Raised when verification inputs or configuration are invalid."""


@dataclass(frozen=True)
class MatchResult:
    match: bool
    confidence: float
    face_similarity: float
    image_similarity: float | None
    metadata_consistency: float | None
    candidate: CandidatePost

    def as_dict(self) -> dict:
        return {
            "match": self.match,
            "confidence": self.confidence,
            "face_similarity": self.face_similarity,
            "image_similarity": self.image_similarity,
            "metadata_consistency": self.metadata_consistency,
            "candidate": {
                "post_id": self.candidate.post_id,
                "similarity_score": self.candidate.similarity_score,
                "image_path": self.candidate.image_path,
                "metadata": self.candidate.metadata,
            },
        }


def _score(value: float) -> float:
    if not isinstance(value, (int, float)) or value != value:
        raise MatchVerificationError("Similarity scores must be finite numbers")
    return max(0.0, min(1.0, float(value)))


def perceptual_image_similarity(query_path: str | Path, candidate_path: str | Path) -> float | None:
    """Return a normalized pHash similarity, or None when an image is unavailable."""
    query, candidate = Path(query_path), Path(candidate_path)
    if not query.is_file() or not candidate.is_file():
        return None
    try:
        query_hash = imagehash.phash(Image.open(query))
        candidate_hash = imagehash.phash(Image.open(candidate))
        distance = query_hash - candidate_hash
        return 1.0 - (distance / len(query_hash.hash) ** 2)
    except (OSError, ValueError) as exc:
        raise MatchVerificationError(f"Unable to calculate perceptual image similarity: {exc}") from exc


def metadata_consistency(query_metadata: dict | None, candidate_metadata: dict) -> float | None:
    if query_metadata is None:
        return None
    if not isinstance(query_metadata, dict) or not isinstance(candidate_metadata, dict):
        raise MatchVerificationError("Metadata inputs must be JSON objects")
    fields = settings.METADATA_FIELDS
    if not fields:
        return None
    compared = [field for field in fields if field in query_metadata and field in candidate_metadata]
    if not compared:
        return None
    return sum(query_metadata[field] == candidate_metadata[field] for field in compared) / len(compared)


def verify_match(
    candidate: CandidatePost,
    query_image_path: str | Path | None = None,
    query_metadata: dict | None = None,
    threshold: float = settings.MATCH_THRESHOLD,
    face_weight: float = settings.FACE_SIMILARITY_WEIGHT,
    image_weight: float = settings.IMAGE_SIMILARITY_WEIGHT,
    metadata_weight: float = settings.METADATA_CONSISTENCY_WEIGHT,
) -> MatchResult:
    if not isinstance(candidate, CandidatePost):
        raise MatchVerificationError("candidate must be a CandidatePost")
    if not 0 <= threshold <= 1:
        raise MatchVerificationError("threshold must be between zero and one")
    weights = (face_weight, image_weight, metadata_weight)
    if any(weight < 0 for weight in weights) or sum(weights) <= 0:
        raise MatchVerificationError("verification weights must be non-negative and non-zero")

    face_similarity = _score(candidate.similarity_score)
    image_similarity = None
    if query_image_path is not None:
        image_similarity = perceptual_image_similarity(query_image_path, candidate.image_path)
    metadata_score = metadata_consistency(query_metadata, candidate.metadata)
    signals = [(face_similarity, face_weight), (image_similarity, image_weight), (metadata_score, metadata_weight)]
    available = [(value, weight) for value, weight in signals if value is not None]
    confidence = sum(value * weight for value, weight in available) / sum(weight for _, weight in available)
    return MatchResult(confidence >= threshold, confidence, face_similarity, image_similarity, metadata_score, candidate)
