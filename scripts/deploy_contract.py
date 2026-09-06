"""Compile and deploy EvidenceRegistry to a configured EVM node."""

import argparse
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from dotenv import load_dotenv
from solcx import compile_source, install_solc, set_solc_version
from web3 import Web3


class DeploymentError(RuntimeError):
    """Raised when contract compilation or deployment fails."""


def deploy(
    rpc_url: str,
    private_key: str,
    wallet_address: str,
    contract_path: str | Path,
    artifact_path: str | Path,
    compiler_version: str,
) -> dict:
    if not rpc_url or not private_key or not wallet_address:
        raise DeploymentError("RPC URL, private key, and wallet address are required")
    source_path = Path(contract_path)
    if not source_path.is_file():
        raise DeploymentError(f"Contract source does not exist: {source_path}")
    web3 = Web3(Web3.HTTPProvider(rpc_url))
    if not web3.is_connected():
        raise DeploymentError(f"Unable to connect to EVM RPC: {rpc_url}")
    try:
        wallet_address = web3.to_checksum_address(wallet_address)
        install_solc(compiler_version)
        set_solc_version(compiler_version)
        compiled = compile_source(source_path.read_text(encoding="utf-8"), output_values=["abi", "bin"])
        contract_interface = next(iter(compiled.values()))
        contract = web3.eth.contract(abi=contract_interface["abi"], bytecode=contract_interface["bin"])
        nonce = web3.eth.get_transaction_count(wallet_address)
        deployment = contract.constructor()
        transaction = deployment.build_transaction({
            "from": wallet_address,
            "nonce": nonce,
            "chainId": web3.eth.chain_id,
            "gas": deployment.estimate_gas({"from": wallet_address}),
            "gasPrice": web3.eth.gas_price,
        })
        signed = web3.eth.account.sign_transaction(transaction, private_key=private_key)
        tx_hash = web3.eth.send_raw_transaction(signed.raw_transaction)
        receipt = web3.eth.wait_for_transaction_receipt(tx_hash)
        if int(receipt.status) != 1:
            raise DeploymentError(f"Contract deployment transaction reverted: {tx_hash.hex()}")
        block = web3.eth.get_block(receipt.blockNumber)
    except Exception as exc:
        raise DeploymentError(f"Contract deployment failed: {exc}") from exc

    artifact = {
        "contractName": "EvidenceRegistry",
        "abi": contract_interface["abi"],
        "bytecode": contract_interface["bin"],
        "address": receipt.contractAddress,
        "transactionHash": tx_hash.hex(),
        "blockNumber": receipt.blockNumber,
        "chainId": web3.eth.chain_id,
        "status": int(receipt.status),
        "deployer": wallet_address,
        "timestamp": datetime.fromtimestamp(block.timestamp, timezone.utc).isoformat().replace("+00:00", "Z"),
    }
    output = Path(artifact_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(artifact, indent=2), encoding="utf-8")
    return artifact


def main() -> int:
    load_dotenv()
    parser = argparse.ArgumentParser(description="Deploy EvidenceRegistry to an EVM blockchain")
    parser.add_argument("--rpc-url", default=os.getenv("BLOCKCHAIN_RPC_URL"))
    parser.add_argument("--private-key", default=os.getenv("PRIVATE_KEY"))
    parser.add_argument("--wallet-address", default=os.getenv("WALLET_ADDRESS"))
    parser.add_argument("--contract-path", default="contracts/EvidenceRegistry.sol")
    parser.add_argument("--artifact-path", default=os.getenv("CONTRACT_ARTIFACT_PATH", "build/EvidenceRegistry.json"))
    parser.add_argument("--compiler-version", default=os.getenv("SOLIDITY_COMPILER_VERSION"))
    args = parser.parse_args()
    if not args.compiler_version:
        parser.error("Solidity compiler version is required")
    try:
        result = deploy(args.rpc_url, args.private_key, args.wallet_address, args.contract_path, args.artifact_path, args.compiler_version)
    except DeploymentError as exc:
        parser.error(str(exc))
    print(f"Contract address: {result['address']}")
    print(f"Transaction hash: {result['transactionHash']}")
    print(f"Block number: {result['blockNumber']}")
    print(f"Transaction status: {result['status']}")
    print(f"Deployer: {result['deployer']}")
    print(f"Artifact: {args.artifact_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
