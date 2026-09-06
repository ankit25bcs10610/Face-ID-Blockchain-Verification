"""FAISS-backed provider for the authorized local post dataset."""

from pathlib import Path
import json
from typing import Any

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

        self.validate_source()
        return search_candidates(embedding, self.index_path, self.manifest_path, top_k)

    def fetch_candidates(self) -> list[CandidatePost]:
        self.validate_source()
        try:
            records = json.loads(Path(self.manifest_path).read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            raise ValueError(f"Unable to read authorized dataset manifest: {self.manifest_path}") from exc
        if not isinstance(records, list):
            raise ValueError("Authorized dataset manifest must be a JSON array")
        candidates = []
        for record in records:
            if not isinstance(record, dict) or not isinstance(record.get("post_id"), str):
                raise ValueError("Authorized dataset manifest contains an invalid record")
            candidates.append(CandidatePost(
                record["post_id"],
                0.0,
                record.get("image_path", ""),
                record.get("metadata", {}),
            ))
        return candidates

    def fetch_metadata(self, post_id: str) -> dict[str, Any]:
        for candidate in self.fetch_candidates():
            if candidate.post_id == post_id:
                return candidate.metadata
        raise KeyError(f"Authorized post does not exist: {post_id}")

    def validate_source(self) -> None:
        if not Path(self.index_path).is_file():
            raise ValueError(f"Authorized dataset index does not exist: {self.index_path}")
        if not Path(self.manifest_path).is_file():
            raise ValueError(f"Authorized dataset manifest does not exist: {self.manifest_path}")
