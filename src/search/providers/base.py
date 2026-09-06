"""Interfaces for permitted content search sources."""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any

import numpy as np

from src.search.candidate_ranker import CandidatePost


class SearchProvider(ABC):
    """Provider contract for searching authorized or consented content."""

    name: str

    @abstractmethod
    def search(
        self, embedding: np.ndarray, top_k: int, image_path: str | Path | None = None
    ) -> list[CandidatePost]:
        """Return candidates retrieved from the configured source.

        ``image_path`` is optional context for providers (such as a live web
        search) that need the original image bytes in addition to the
        embedding; providers that only need the embedding may ignore it.
        """

    @abstractmethod
    def fetch_candidates(self) -> list[CandidatePost]:
        """Return all candidates currently available from this source."""

    @abstractmethod
    def fetch_metadata(self, post_id: str) -> dict[str, Any]:
        """Return metadata for a candidate identified by its provider-local ID."""

    @abstractmethod
    def validate_source(self) -> None:
        """Validate that the configured source is available and authorized."""
