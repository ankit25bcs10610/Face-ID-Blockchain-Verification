"""Interfaces for permitted content search sources."""

from abc import ABC, abstractmethod

import numpy as np

from src.search.candidate_ranker import CandidatePost


class SearchProvider(ABC):
    """Provider contract for searching authorized or consented content."""

    name: str

    @abstractmethod
    def search(self, embedding: np.ndarray, top_k: int) -> list[CandidatePost]:
        """Return candidates retrieved from the configured authorized source."""
