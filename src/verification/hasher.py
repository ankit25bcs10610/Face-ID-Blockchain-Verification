"""SHA-256 hashing of canonical evidence JSON."""

import hashlib

from src.verification.evidence import canonicalize_evidence


def generate_hash(evidence: dict) -> str:
    """Hash canonical UTF-8 evidence bytes and return lowercase hexadecimal SHA-256."""
    canonical_json = canonicalize_evidence(evidence)
    return hashlib.sha256(canonical_json.encode("utf-8")).hexdigest()
