"""FAISS-backed provider for the authorized local post dataset."""

from pathlib import Path

import numpy as np

from src.config import settings
from src.search.candidate_ranker import CandidatePost
from src.search.providers.base import SearchProvider


class AuthorizedDatasetProvider(SearchProvider):
    """Search the configured consented dataset and never an unrestricted source."""

    name = "authorized_dataset"

    def __init__(self, index_path: str | Path | None = None, manifest_path: str | Path | None = None):
        self.index_path = index_path or Path(settings.FAISS_DIR) / settings.INDEX_NAME
        self.manifest_path = manifest_path or Path(settings.FAISS_DIR) / settings.MANIFEST_NAME

    def search(self, embedding: np.ndarray, top_k: int) -> list[CandidatePost]:
        from src.search.orchestrator import search_candidates

        return search_candidates(embedding, self.index_path, self.manifest_path, top_k)
