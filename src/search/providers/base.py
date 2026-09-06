"""Interfaces for permitted content search sources."""

from abc import ABC, abstractmethod
from typing import Any

import numpy as np

from src.search.candidate_ranker import CandidatePost


class SearchProvider(ABC):
    """Provider contract for searching authorized or consented content."""

    name: str

    @abstractmethod
    def search(self, embedding: np.ndarray, top_k: int) -> list[CandidatePost]:
        """Return candidates retrieved from the configured authorized source."""

    @abstractmethod
    def fetch_candidates(self) -> list[CandidatePost]:
        """Return all candidates currently available from this source."""

    @abstractmethod
    def fetch_metadata(self, post_id: str) -> dict[str, Any]:
        """Return metadata for a candidate identified by its provider-local ID."""

    @abstractmethod
    def validate_source(self) -> None:
        """Validate that the configured source is available and authorized."""
