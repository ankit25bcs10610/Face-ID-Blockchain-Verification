"""Nearest-neighbor search over the persisted authorized-content index."""

import json
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

from src.config import settings
from src.search.candidate_ranker import CandidatePost, rank_candidates


class SearchError(RuntimeError):
    """Raised when the FAISS search cannot be completed."""


@dataclass(frozen=True)
class SearchResponse:
    search_id: str
    timestamp: str
    provider: str
    embedding_dimension: int
    candidate_count: int
    results: list[CandidatePost]

    def as_dict(self) -> dict:
        return {
            "search_id": self.search_id,
            "timestamp": self.timestamp,
            "provider": self.provider,
            "query": {"embedding_dimension": self.embedding_dimension},
            "candidate_count": self.candidate_count,
            "results": [
                {
                    "post_id": result.post_id,
                    "similarity_score": result.similarity_score,
                    "image_path": result.image_path,
                    "metadata": result.metadata,
                }
                for result in self.results
            ],
        }


def _faiss_module():
    try:
        import faiss
        return faiss
    except ImportError as exc:
        raise SearchError("FAISS is required to search the face index") from exc


def _load_manifest(path: Path) -> list[dict]:
    if not path.is_file():
        raise SearchError(f"FAISS manifest does not exist: {path}")
    try:
        manifest = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise SearchError(f"Unable to read FAISS manifest: {path}") from exc
    if not isinstance(manifest, list):
        raise SearchError("FAISS manifest must contain a JSON array")
    return manifest


def search_candidates(
    face_embedding: np.ndarray,
    index_path: str | Path = Path(settings.FAISS_DIR) / settings.INDEX_NAME,
    manifest_path: str | Path = Path(settings.FAISS_DIR) / settings.MANIFEST_NAME,
    top_k: int = settings.TOP_K,
) -> list[CandidatePost]:
    """Search the actual persisted FAISS index and return ranked post records."""
    if top_k <= 0:
        raise SearchError("top_k must be greater than zero")
    query = np.asarray(face_embedding, dtype=np.float32).reshape(1, -1)
    if query.shape[1] != 512 or not np.all(np.isfinite(query)):
        raise SearchError("Face embedding must be a finite 512-dimensional vector")
    norm = np.linalg.norm(query)
    if norm == 0:
        raise SearchError("Face embedding cannot be zero length")
    query /= norm
    index_file = Path(index_path)
    if not index_file.is_file():
        raise SearchError(f"FAISS index does not exist: {index_file}")
    manifest = _load_manifest(Path(manifest_path))
    try:
        index = _faiss_module().read_index(str(index_file))
        if index.d != query.shape[1]:
            raise SearchError("FAISS index dimensions do not match the face embedding")
        limit = min(top_k, index.ntotal, len(manifest))
        if limit == 0:
            return []
        scores, indices = index.search(query, limit)
    except SearchError:
        raise
    except Exception as exc:
        raise SearchError(f"FAISS nearest-neighbor search failed: {exc}") from exc

    candidates = []
    for score, row_id in zip(scores[0], indices[0]):
        if row_id < 0 or row_id >= len(manifest):
            raise SearchError(f"FAISS returned an invalid manifest row: {row_id}")
        record = manifest[int(row_id)]
        if not isinstance(record, dict) or not isinstance(record.get("post_id"), str):
            raise SearchError(f"Invalid manifest record at row {row_id}")
        candidates.append(CandidatePost(record["post_id"], float(score), record.get("image_path", ""), record.get("metadata", {})))
    return rank_candidates(candidates)


def search(face_embedding: np.ndarray, top_k: int = settings.TOP_K) -> list[CandidatePost]:
    return search_candidates(face_embedding, top_k=top_k)


def _default_provider():
    if settings.SEARCH_PROVIDER == "web_reverse_image":
        from src.search.providers.web_reverse_image import WebReverseImageProvider

        return WebReverseImageProvider()
    from src.search.providers.authorized_dataset import AuthorizedDatasetProvider

    return AuthorizedDatasetProvider()


def search_detailed(
    face_embedding: np.ndarray,
    top_k: int = settings.TOP_K,
    provider=None,
    image_path: str | Path | None = None,
) -> SearchResponse:
    """Execute a configured authorized provider search with dynamic audit metadata."""
    if provider is None:
        provider = _default_provider()
    if top_k <= 0:
        raise SearchError("top_k must be greater than zero")
    query = np.asarray(face_embedding).reshape(-1)
    if query.size != 512:
        raise SearchError("Face embedding must be 512-dimensional")
    try:
        results = provider.search(face_embedding, top_k, image_path=image_path)
    except SearchError:
        raise
    except Exception as exc:
        raise SearchError(str(exc)) from exc
    return SearchResponse(
        search_id=str(uuid.uuid4()),
        timestamp=datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        provider=getattr(provider, "name", provider.__class__.__name__),
        embedding_dimension=int(query.size),
        candidate_count=len(results),
        results=results,
    )
