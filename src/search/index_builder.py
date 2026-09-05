"""Build a FAISS index from an authorized, consented post dataset."""

import json
from datetime import datetime, timezone
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Callable

import numpy as np

from src.config import settings
from src.face.encoder import extract_embedding


class DatasetError(ValueError):
    """Raised when an authorized post cannot be loaded or indexed."""


class IndexBuildError(RuntimeError):
    """Raised when an index cannot be created or persisted."""


@dataclass(frozen=True)
class IndexedPost:
    post_id: str
    image_path: str
    metadata: dict


@dataclass(frozen=True)
class IndexBuildResult:
    indexed_count: int
    skipped_count: int
    index_path: str
    embeddings_path: str
    manifest_path: str
    errors: list[str]


def _read_metadata(post_dir: Path) -> dict:
    metadata_path = post_dir / "metadata.json"
    if not metadata_path.is_file():
        raise DatasetError(f"Missing metadata.json: {metadata_path}")
    try:
        metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise DatasetError(f"Invalid metadata.json: {metadata_path}") from exc
    if not isinstance(metadata, dict):
        raise DatasetError(f"Metadata must be a JSON object: {metadata_path}")
    post_id = metadata.get("post_id")
    if not isinstance(post_id, str) or not post_id.strip():
        raise DatasetError(f"Metadata requires a non-empty post_id: {metadata_path}")
    return metadata


def _find_image(post_dir: Path) -> Path:
    images = sorted(
        path for path in post_dir.iterdir()
        if path.is_file() and path.suffix.lower() in settings.IMAGE_EXTENSIONS
    )
    if not images:
        raise DatasetError(f"No supported image found in {post_dir}")
    return images[0]


def discover_posts(posts_dir: str | Path) -> list[tuple[Path, dict, Path]]:
    root = Path(posts_dir)
    if not root.is_dir():
        raise DatasetError(f"Posts directory does not exist: {root}")
    discovered = []
    for post_dir in sorted(path for path in root.iterdir() if path.is_dir()):
        try:
            metadata = _read_metadata(post_dir)
            discovered.append((post_dir, metadata, _find_image(post_dir)))
        except DatasetError:
            continue
    return discovered


def _faiss_module():
    try:
        import faiss
        return faiss
    except ImportError as exc:
        raise IndexBuildError("FAISS is required to build the face index") from exc


def build_index(
    posts_dir: str | Path = settings.POSTS_DIR,
    embeddings_dir: str | Path = settings.EMBEDDINGS_DIR,
    faiss_dir: str | Path = settings.FAISS_DIR,
    embedding_fn: Callable[[str | Path], np.ndarray] = extract_embedding,
) -> IndexBuildResult:
    posts = discover_posts(posts_dir)
    total_post_dirs = sum(1 for path in Path(posts_dir).iterdir() if path.is_dir())
    vectors: list[np.ndarray] = []
    records: list[IndexedPost] = []
    errors: list[str] = []
    for _, metadata, image_path in posts:
        try:
            vector = np.asarray(embedding_fn(image_path), dtype=np.float32).reshape(-1)
            if vector.size != 512 or not np.all(np.isfinite(vector)):
                raise DatasetError(f"Embedding must be a finite 512-dimensional vector: {image_path}")
            norm = np.linalg.norm(vector)
            if norm == 0:
                raise DatasetError(f"Embedding cannot be zero length: {image_path}")
            vectors.append(vector / norm)
            records.append(IndexedPost(metadata["post_id"], str(image_path), metadata))
        except Exception as exc:
            errors.append(f"{image_path}: {exc}")

    if not vectors:
        raise IndexBuildError("No valid posts were available to build the FAISS index")

    matrix = np.ascontiguousarray(np.vstack(vectors), dtype=np.float32)
    faiss = _faiss_module()
    index = faiss.IndexFlatIP(matrix.shape[1])
    index.add(matrix)
    embeddings_path = Path(embeddings_dir) / settings.EMBEDDINGS_NAME
    index_path = Path(faiss_dir) / settings.INDEX_NAME
    manifest_path = Path(faiss_dir) / settings.MANIFEST_NAME
    metadata_path = Path(faiss_dir) / settings.INDEX_METADATA_NAME
    embeddings_path.parent.mkdir(parents=True, exist_ok=True)
    index_path.parent.mkdir(parents=True, exist_ok=True)
    np.save(embeddings_path, matrix)
    faiss.write_index(index, str(index_path))
    manifest_path.write_text(
        json.dumps([asdict(record) for record in records], indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    metadata_path.write_text(json.dumps({
        "schema_version": "1.0",
        "embedding_dimension": int(matrix.shape[1]),
        "index_type": "IndexFlatIP",
        "record_count": int(matrix.shape[0]),
        "created_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
    }, indent=2), encoding="utf-8")
    return IndexBuildResult(
        len(records), total_post_dirs - len(records), str(index_path),
        str(embeddings_path), str(manifest_path), errors,
    )
