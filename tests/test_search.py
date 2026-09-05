import json

import cv2
import numpy as np
import pytest

from src.search import index_builder
from src.search.index_builder import DatasetError, build_index, discover_posts


def make_post(root, name, post_id, image=True):
    directory = root / name
    directory.mkdir()
    (directory / "metadata.json").write_text(json.dumps({"post_id": post_id, "caption": name}), encoding="utf-8")
    if image:
        cv2.imwrite(str(directory / "image.jpg"), np.zeros((20, 20, 3), dtype=np.uint8))


def embedding_fn(path):
    vector = np.zeros(512, dtype=np.float32)
    vector[0] = 1 if "001" in str(path) else 2
    return vector


class FakeFaissIndex:
    def __init__(self, dimensions):
        self.dimensions = dimensions
        self.vectors = None

    def add(self, matrix):
        self.vectors = matrix.copy()


class FakeFaiss:
    IndexFlatIP = FakeFaissIndex

    @staticmethod
    def write_index(index, path):
        open(path, "wb").write(index.vectors.tobytes())


def test_discover_posts_reads_metadata_and_images(tmp_path):
    posts = tmp_path / "posts"
    posts.mkdir()
    make_post(posts, "post_001", "post_001")
    found = discover_posts(posts)
    assert len(found) == 1
    assert found[0][1]["post_id"] == "post_001"
    assert found[0][2].name == "image.jpg"


def test_build_index_writes_faiss_embeddings_and_manifest(tmp_path, monkeypatch):
    posts = tmp_path / "posts"
    posts.mkdir()
    make_post(posts, "post_001", "post_001")
    make_post(posts, "post_002", "post_002")
    monkeypatch.setattr(index_builder, "_faiss_module", lambda: FakeFaiss)
    result = build_index(posts, tmp_path / "embeddings", tmp_path / "faiss", embedding_fn)
    assert result.indexed_count == 2
    assert result.skipped_count == 0
    assert (tmp_path / "embeddings" / "embeddings.npy").is_file()
    assert (tmp_path / "faiss" / "faces.index").is_file()
    manifest = json.loads((tmp_path / "faiss" / "manifest.json").read_text())
    assert [record["post_id"] for record in manifest] == ["post_001", "post_002"]
    assert np.load(tmp_path / "embeddings" / "embeddings.npy").shape == (2, 512)


def test_invalid_post_is_skipped(tmp_path, monkeypatch):
    posts = tmp_path / "posts"
    posts.mkdir()
    make_post(posts, "post_001", "post_001")
    make_post(posts, "post_002", "post_002", image=False)
    monkeypatch.setattr(index_builder, "_faiss_module", lambda: FakeFaiss)
    result = build_index(posts, tmp_path / "embeddings", tmp_path / "faiss", embedding_fn)
    assert result.indexed_count == 1
    assert result.skipped_count == 1


def test_missing_posts_directory_fails(tmp_path):
    with pytest.raises(DatasetError):
        discover_posts(tmp_path / "missing")
