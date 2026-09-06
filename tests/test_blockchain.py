from types import SimpleNamespace

import pytest

from src.blockchain.client import BlockchainError
from src.blockchain.registry import _hash_bytes32, get_evidence, register_evidence, verify_evidence


class FakeCall:
    def __init__(self, result=None):
        self.result = result

    def call(self):
        return self.result

    def estimate_gas(self, _options):
        return 21000

    def build_transaction(self, options):
        return options


class FakeFunctions:
    def __init__(self, record, exists=True):
        self.record = record
        self.exists = exists

    def registerEvidence(self, _hash):
        return FakeCall()

    def verifyEvidence(self, _hash):
        return FakeCall(self.exists)

    def getEvidence(self, _hash):
        return FakeCall(self.record)


class FakeContract:
    address = "0xcontract"

    def __init__(self, record, exists=True):
        self.functions = FakeFunctions(record, exists)


class FakeWeb3:
    def __init__(self):
        self.eth = SimpleNamespace(
            chain_id=123,
            gas_price=100,
            get_transaction_count=lambda _address: 7,
            account=SimpleNamespace(sign_transaction=lambda _tx, _key: SimpleNamespace(raw_transaction=b"signed")),
            send_raw_transaction=lambda _raw: SimpleNamespace(hex=lambda: "0xtx"),
            wait_for_transaction_receipt=lambda _hash: SimpleNamespace(status=1, blockNumber=9),
            get_block=lambda _number: SimpleNamespace(timestamp=0),
        )

    @staticmethod
    def to_checksum_address(address):
        return address


def test_hash_bytes32_requires_sha256_length():
    assert _hash_bytes32("ab" * 32) == bytes.fromhex("ab" * 32)
    with pytest.raises(BlockchainError):
        _hash_bytes32("ab")


def test_registry_reads_and_verifies_actual_contract_values():
    evidence_hash = "cd" * 32
    contract = FakeContract((bytes.fromhex(evidence_hash), 12, "0xverifier", True))
    web3 = FakeWeb3()
    assert verify_evidence(evidence_hash, web3=web3, contract=contract) is True
    result = get_evidence(evidence_hash, web3=web3, contract=contract)
    assert result["evidence_hash"] == "0x" + evidence_hash
    assert result["timestamp"] == 12
    assert result["verifier"] == "0xverifier"


def test_registry_registration_uses_transaction_receipt():
    evidence_hash = "ef" * 32
    contract = FakeContract((bytes.fromhex(evidence_hash), 0, "0xverifier", False))
    result = register_evidence(
        evidence_hash,
        web3=FakeWeb3(),
        contract=contract,
        private_key="test-only-key",
        wallet_address="0xsender",
    )
    assert result["transaction_hash"] == "0xtx"
    assert result["block_number"] == 9
    assert result["status"] == 1
    assert result["verifier"] == "0xsender"
