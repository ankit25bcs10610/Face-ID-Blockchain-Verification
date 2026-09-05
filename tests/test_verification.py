import numpy as np
from PIL import Image
import pytest

from src.search.candidate_ranker import CandidatePost
from src.verification.matcher import MatchVerificationError, metadata_consistency, verify_match
from src.verification.evidence import EvidenceError, canonicalize_evidence, create_evidence, save_evidence
from src.verification.hasher import generate_hash


def candidate(score=0.9, image_path=""):
    return CandidatePost("post_001", score, image_path, {"platform": "demo", "caption": "same"})


def test_weighted_match_uses_configured_signals(monkeypatch, tmp_path):
    query = tmp_path / "query.png"
    Image.fromarray(np.full((32, 32, 3), 100, dtype=np.uint8)).save(query)
    monkeypatch.setattr("src.verification.matcher.perceptual_image_similarity", lambda *_: 0.5)
    result = verify_match(candidate(image_path="candidate.png"), query, {"platform": "demo", "caption": "same"}, threshold=0.8, face_weight=0.7, image_weight=0.2, metadata_weight=0.1)
    assert result.match is True
    assert result.confidence == pytest.approx(0.83)


def test_tampered_metadata_fails_threshold():
    result = verify_match(candidate(0.7), query_metadata={"platform": "other", "caption": "changed"}, threshold=0.8, face_weight=0.7, image_weight=0, metadata_weight=0.3)
    assert result.match is False
    assert result.metadata_consistency == 0


def test_metadata_without_comparable_fields_is_optional():
    assert metadata_consistency({"unknown": "x"}, {"caption": "y"}) is None


def test_invalid_configuration_is_rejected():
    with pytest.raises(MatchVerificationError):
        verify_match(candidate(), threshold=1.5)


def verified_result():
    return verify_match(candidate(0.95), query_metadata={"platform": "demo", "caption": "same"}, threshold=0.8, image_weight=0, metadata_weight=0.1)


def test_canonicalization_is_sorted_and_stable():
    first = {"z": "é", "a": 1}
    second = {"a": 1, "z": "é"}
    assert canonicalize_evidence(first) == '{"a":1,"z":"é"}'
    assert generate_hash(first) == generate_hash(second)


def test_evidence_is_saved_as_utf8_canonical_json(tmp_path):
    evidence = create_evidence(verified_result(), image_hash="abc123")
    path = save_evidence(evidence, tmp_path / "evidence.json")
    assert path.read_text(encoding="utf-8") == canonicalize_evidence(evidence)
    assert path.is_file()


def test_tampering_changes_hash():
    evidence = create_evidence(verified_result())
    original_hash = generate_hash(evidence)
    evidence["caption"] = "modified"
    assert generate_hash(evidence) != original_hash


def test_unverified_match_cannot_create_evidence():
    result = verify_match(candidate(0.2), threshold=0.8, image_weight=0, metadata_weight=0.1)
    with pytest.raises(EvidenceError):
        create_evidence(result)
