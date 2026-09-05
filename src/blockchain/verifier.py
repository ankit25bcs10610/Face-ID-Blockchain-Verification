"""Re-verify local evidence against its immutable on-chain fingerprint."""

from copy import deepcopy
from typing import Any

from src.verification.hasher import generate_hash


class ReverificationError(ValueError):
    """Raised when evidence cannot be re-verified."""


def _normal_hash(value: str) -> str:
    return value.removeprefix("0x").lower()


def reverify_evidence(evidence: dict, web3=None, contract=None, evidence_reader=None) -> dict:
    """Recreate the evidence hash and compare it with the registry record."""
    if not isinstance(evidence, dict):
        raise ReverificationError("Evidence must be a JSON object")
    if evidence_reader is None:
        try:
            from src.blockchain.registry import get_evidence
        except ImportError as exc:
            raise ReverificationError("Web3.py is required for blockchain re-verification") from exc
        evidence_reader = get_evidence
    local_hash = generate_hash(evidence)
    try:
        record = evidence_reader(local_hash, web3=web3, contract=contract)
        blockchain_hash = record["evidence_hash"]
        on_chain_exists = bool(record["exists"])
    except (KeyError, TypeError, ValueError) as exc:
        raise ReverificationError(f"Invalid blockchain evidence record: {exc}") from exc
    if not isinstance(blockchain_hash, str):
        raise ReverificationError("Blockchain evidence hash must be text")
    verified = on_chain_exists and _normal_hash(local_hash) == _normal_hash(blockchain_hash)
    return {
        "verified": verified,
        "status": "VERIFIED" if verified else "TAMPER DETECTED",
        "local_hash": local_hash,
        "blockchain_hash": blockchain_hash,
        "on_chain_exists": on_chain_exists,
        "timestamp": record["timestamp"],
        "verifier": record["verifier"],
        "contract_address": record["contract_address"],
        "reason": "Evidence matches the on-chain record" if verified else (
            "No on-chain record exists" if not on_chain_exists else "Evidence does not match the on-chain record"
        ),
        "message": "Evidence matches the on-chain record" if verified else "Evidence does not match the on-chain record",
    }


def tamper_evidence(evidence: dict, field: str, value: Any) -> dict:
    """Return a modified copy for the tamper-detection demonstration."""
    if not isinstance(evidence, dict):
        raise ReverificationError("Evidence must be a JSON object")
    if field not in evidence:
        raise ReverificationError(f"Evidence field does not exist: {field}")
    modified = deepcopy(evidence)
    modified[field] = value
    return modified


def demonstrate_tampering(evidence: dict, field: str, value: Any, web3=None, contract=None, evidence_reader=None) -> dict:
    """Return original and tampered verification results without mutating evidence."""
    tampered = tamper_evidence(evidence, field, value)
    return {
        "original": reverify_evidence(evidence, web3=web3, contract=contract, evidence_reader=evidence_reader),
        "tampered": {
            "field": field,
            "value": value,
            "result": reverify_evidence(tampered, web3=web3, contract=contract, evidence_reader=evidence_reader),
        },
    }
