"""Operations against the deployed EvidenceRegistry contract."""

from datetime import datetime, timezone

from src.blockchain.client import BlockchainError, connect_to_blockchain, load_registry
from src.config import settings


def _hash_bytes32(evidence_hash: str | bytes) -> bytes:
    try:
        value = bytes.fromhex(evidence_hash.removeprefix("0x")) if isinstance(evidence_hash, str) else bytes(evidence_hash)
    except ValueError as exc:
        raise BlockchainError("Evidence hash must be hexadecimal or bytes") from exc
    if len(value) != 32:
        raise BlockchainError("Evidence hash must contain exactly 32 bytes")
    return value


def register_evidence(
    evidence_hash: str | bytes,
    web3=None,
    contract=None,
    private_key: str | None = None,
    wallet_address: str | None = None,
) -> dict:
    web3 = web3 or connect_to_blockchain()
    contract = contract or load_registry(web3)
    key = private_key or settings.PRIVATE_KEY
    sender = wallet_address or settings.WALLET_ADDRESS
    if not key or not sender:
        raise BlockchainError("PRIVATE_KEY and WALLET_ADDRESS are required")
    sender = web3.to_checksum_address(sender)
    try:
        nonce = web3.eth.get_transaction_count(sender)
        transaction = contract.functions.registerEvidence(_hash_bytes32(evidence_hash)).build_transaction({
            "from": sender,
            "nonce": nonce,
            "chainId": web3.eth.chain_id,
            "gas": contract.functions.registerEvidence(_hash_bytes32(evidence_hash)).estimate_gas({"from": sender}),
            "gasPrice": web3.eth.gas_price,
        })
        signed = web3.eth.account.sign_transaction(transaction, key)
        tx_hash = web3.eth.send_raw_transaction(signed.raw_transaction)
        receipt = web3.eth.wait_for_transaction_receipt(tx_hash)
        block = web3.eth.get_block(receipt.blockNumber)
    except Exception as exc:
        raise BlockchainError(f"Evidence registration failed: {exc}") from exc
    return {
        "transaction_hash": tx_hash.hex(),
        "block_number": receipt.blockNumber,
        "timestamp": datetime.fromtimestamp(block.timestamp, timezone.utc).isoformat().replace("+00:00", "Z"),
        "contract_address": contract.address,
    }


def verify_evidence(evidence_hash: str | bytes, web3=None, contract=None) -> bool:
    web3 = web3 or connect_to_blockchain()
    contract = contract or load_registry(web3)
    try:
        return bool(contract.functions.verifyEvidence(_hash_bytes32(evidence_hash)).call())
    except Exception as exc:
        raise BlockchainError(f"Evidence verification failed: {exc}") from exc


def get_evidence(evidence_hash: str | bytes, web3=None, contract=None) -> dict:
    web3 = web3 or connect_to_blockchain()
    contract = contract or load_registry(web3)
    try:
        value = contract.functions.getEvidence(_hash_bytes32(evidence_hash)).call()
    except Exception as exc:
        raise BlockchainError(f"Unable to retrieve evidence: {exc}") from exc
    return {
        "evidence_hash": "0x" + value[0].hex(),
        "timestamp": value[1],
        "verifier": value[2],
        "exists": bool(value[3]),
        "contract_address": contract.address,
    }
