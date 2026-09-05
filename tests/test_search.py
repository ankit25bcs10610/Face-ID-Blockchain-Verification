import json

import cv2
import numpy as np
import pytest

from src.search import index_builder
from src.search.index_builder import DatasetError, build_index, discover_posts
from src.search.candidate_ranker import CandidatePost, rank_candidates
from src.search import orchestrator
from src.search.providers.authorized_dataset import AuthorizedDatasetProvider


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

    @staticmethod
    def read_index(path):
        return FakeSearchIndex()


class FakeSearchIndex:
    d = 512
    ntotal = 3

    def search(self, query, limit):
        return np.array([[0.9, 0.7, 0.4]], dtype=np.float32)[:, :limit], np.array([[1, 0, 2]], dtype=np.int64)[:, :limit]


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


def test_rank_candidates_orders_by_similarity():
    items = [CandidatePost("b", 0.2, "b.jpg", {}), CandidatePost("a", 0.9, "a.jpg", {})]
    assert [item.post_id for item in rank_candidates(items)] == ["a", "b"]


def test_orchestrator_uses_faiss_and_manifest(tmp_path, monkeypatch):
    index_path = tmp_path / "faces.index"
    index_path.write_bytes(b"index")
    manifest_path = tmp_path / "manifest.json"
    manifest_path.write_text(json.dumps([
        {"post_id": "post_001", "image_path": "one.jpg", "metadata": {"caption": "one"}},
        {"post_id": "post_002", "image_path": "two.jpg", "metadata": {"caption": "two"}},
        {"post_id": "post_003", "image_path": "three.jpg", "metadata": {"caption": "three"}},
    ]))
    monkeypatch.setattr(orchestrator, "_faiss_module", lambda: FakeFaiss)
    results = orchestrator.search_candidates(np.eye(512, dtype=np.float32)[0], index_path, manifest_path, top_k=2)
    assert [item.post_id for item in results] == ["post_002", "post_001"]
    assert results[0].similarity_score == pytest.approx(0.9)


def test_detailed_search_generates_dynamic_audit_metadata(monkeypatch):
    class Provider:
        name = "consented_fixture"

        def search(self, embedding, top_k):
            return [CandidatePost("post", 0.8, "post.jpg", {})]

    response = orchestrator.search_detailed(np.ones(512, dtype=np.float32), provider=Provider())
    assert response.provider == "consented_fixture"
    assert response.embedding_dimension == 512
    assert response.candidate_count == 1
    assert response.search_id
    assert response.timestamp.endswith("Z")
