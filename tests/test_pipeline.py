from pathlib import Path

import numpy as np

from src import main as pipeline
from src.search.candidate_ranker import CandidatePost
from src.verification.hasher import generate_hash
from src.verification.matcher import MatchResult


def test_run_pipeline_connects_all_stages(monkeypatch, tmp_path):
    input_image = tmp_path / "input.jpg"
    input_image.write_bytes(b"input")
    post_image = tmp_path / "post.jpg"
    post_image.write_bytes(b"post")
    quality = type("Quality", (), {"width": 240, "height": 240, "quality_score": 0.9})()
    face = type("Face", (), {"detection_confidence": 0.99})()
    candidate = CandidatePost("post_001", 0.95, str(post_image), {"platform": "demo", "caption": "same"})
    match = MatchResult(True, 0.95, 0.95, None, None, candidate)
    blockchain = {
        "transaction_hash": "0xtx",
        "block_number": 1,
        "timestamp": "2026-01-01T00:00:00Z",
        "contract_address": "0xcontract",
    }

    monkeypatch.setattr(pipeline, "validate_image", lambda _: (object(), quality))
    monkeypatch.setattr(pipeline, "detect_face", lambda _: face)
    monkeypatch.setattr(pipeline, "extract_embedding", lambda _: np.ones(512, dtype=np.float32))
    monkeypatch.setattr(pipeline, "search_candidates", lambda *_args, **_kwargs: [candidate])
    monkeypatch.setattr(pipeline, "verify_match", lambda *_args, **_kwargs: match)
    monkeypatch.setattr(pipeline, "_image_hash", lambda _: "phash")
    monkeypatch.setattr(pipeline, "save_evidence", lambda evidence: tmp_path / "evidence.json")
    monkeypatch.setattr(pipeline, "generate_hash", lambda evidence: "a" * 64)
    monkeypatch.setattr(pipeline, "reverify_evidence", lambda *_args, **_kwargs: {
        "status": "VERIFIED", "verified": True, "local_hash": "a" * 64,
        "blockchain_hash": "0x" + "a" * 64, "timestamp": 1,
        "verifier": "0xverifier", "contract_address": "0xcontract",
    })

    result = pipeline.run_pipeline(input_image, top_k=5, threshold=0.8, blockchain_register=lambda _: blockchain)
    assert result["candidate"].post_id == "post_001"
    assert result["evidence_hash"] == "a" * 64
    assert result["reverification"]["status"] == "VERIFIED"
