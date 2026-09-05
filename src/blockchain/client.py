"""Web3 connection and deployed contract loading."""

import json
from pathlib import Path

from web3 import Web3

from src.config import settings


class BlockchainError(RuntimeError):
    """Raised when blockchain configuration or RPC operations fail."""


def connect_to_blockchain(rpc_url: str | None = None) -> Web3:
    endpoint = rpc_url or settings.BLOCKCHAIN_RPC_URL
    if not endpoint:
        raise BlockchainError("BLOCKCHAIN_RPC_URL is required")
    web3 = Web3(Web3.HTTPProvider(endpoint))
    if not web3.is_connected():
        raise BlockchainError(f"Unable to connect to blockchain RPC: {endpoint}")
    if settings.CHAIN_ID and web3.eth.chain_id != settings.CHAIN_ID:
        raise BlockchainError(
            f"Connected to chain ID {web3.eth.chain_id}, expected {settings.CHAIN_ID}"
        )
    return web3


def load_registry(web3: Web3, artifact_path: str | Path | None = None, contract_address: str | None = None):
    path = Path(artifact_path or settings.CONTRACT_ARTIFACT_PATH)
    address = contract_address or settings.CONTRACT_ADDRESS
    if not address:
        raise BlockchainError("CONTRACT_ADDRESS is required")
    if not path.is_file():
        raise BlockchainError(f"Contract artifact does not exist: {path}")
    try:
        artifact = json.loads(path.read_text(encoding="utf-8"))
        abi = artifact["abi"]
        checksum_address = web3.to_checksum_address(address)
        return web3.eth.contract(address=checksum_address, abi=abi)
    except (OSError, json.JSONDecodeError, KeyError, ValueError) as exc:
        raise BlockchainError(f"Unable to load contract artifact: {path}") from exc
