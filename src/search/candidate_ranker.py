"""Ranking and validation for FAISS candidate results."""

from dataclasses import dataclass


class RankingError(ValueError):
    """Raised when candidate results cannot be ranked."""


@dataclass(frozen=True)
class CandidatePost:
    post_id: str
    similarity_score: float
    image_path: str
    metadata: dict


def rank_candidates(candidates: list[CandidatePost]) -> list[CandidatePost]:
    """Return candidates in descending similarity order, deterministically."""
    if any(not isinstance(candidate, CandidatePost) for candidate in candidates):
        raise RankingError("All candidates must be CandidatePost instances")
    return sorted(candidates, key=lambda item: item.similarity_score, reverse=True)
