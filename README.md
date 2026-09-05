# TraceChain AI

TraceChain AI is an authorized-content face matching and evidence verification pipeline. It processes a supplied face image, searches a consented local post dataset with real InsightFace embeddings and FAISS nearest-neighbor search, creates deterministic evidence, anchors its SHA-256 fingerprint on an EVM blockchain, and re-verifies the evidence later.

## Privacy and Authorization

The default provider searches only `data/posts/`, which must contain user-owned, authorized, or consented demonstration content. This project does not identify unknown people across unrestricted public social-media accounts. Any future provider must enforce the same authorization boundary and the applicable platform terms.

## Architecture

```text
Face image
  -> validation and quality checks
  -> InsightFace detection, landmarks, alignment, ArcFace embedding
  -> authorized dataset provider
  -> FAISS vector search and candidate ranking
  -> multi-signal match verification
  -> canonical evidence JSON
  -> SHA-256 fingerprint
  -> EvidenceRegistry smart contract
  -> on-chain re-verification
```

## Technology Stack

- Python 3.10+
- OpenCV, InsightFace, ArcFace, NumPy
- FAISS with normalized inner-product vectors
- Solidity and Web3.py
- Ganache or another Ethereum-compatible local/test network
- Pytest

## Project Structure

```text
src/face/          image validation, detection, alignment, embeddings
src/search/        providers, indexing, FAISS search, ranking
src/verification/  match scoring, evidence, canonical hashing
src/blockchain/    Web3 client, registry operations, re-verification
contracts/         EvidenceRegistry.sol
scripts/           index building and contract deployment
demo/              demonstration utilities
tests/             unit and integration tests
data/posts/        authorized post directories
data/embeddings/   generated embedding matrix
data/faiss/        generated FAISS index and manifest
data/evidence/     generated evidence records
```

## Installation

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

InsightFace downloads its configured model the first time it is initialized. A machine with a compatible ONNX Runtime installation is required for real inference.

## Dataset Setup

Create one directory per authorized post:

```text
data/posts/post_001/image.jpg
data/posts/post_001/metadata.json
```

The metadata file must be a JSON object with a non-empty `post_id`. Additional fields such as `platform`, `post_url`, `caption`, and `timestamp` are preserved and used when available.

## Build the FAISS Index

```bash
python3 scripts/build_index.py
```

The command generates the normalized embedding matrix, FAISS index, manifest, and versioned index metadata under the configured output directories. Invalid post directories are skipped and reported; a build with no valid posts fails.

## Blockchain Setup

Start Ganache or another local EVM node, then set these values in `.env`:

```env
BLOCKCHAIN_RPC_URL=http://127.0.0.1:7545
PRIVATE_KEY=your_development_wallet_private_key
WALLET_ADDRESS=your_development_wallet_address
BLOCKCHAIN_MODE=local
CHAIN_ID=0
```

Deploy the registry:

```bash
python3 scripts/deploy_contract.py
```

Set `CONTRACT_ADDRESS` to the address printed by deployment. The deployment artifact is written to `CONTRACT_ARTIFACT_PATH` and contains the ABI used by Web3.py. Never commit `.env` or private credentials.

## Run the Pipeline

```bash
python3 -m src.main --image path/to/authorized-face.jpg
```

Optional arguments:

```bash
python3 -m src.main --image path/to/input.jpg --top-k 5 --threshold 0.80 --query-metadata path/to/query-metadata.json
```

The output displays values produced by the actual run, including candidate IDs, calculated confidence, evidence hash, transaction hash, block number, timestamp, contract address, and re-verification status.

## Tampering Demonstration

After a successful run, use the generated evidence file with a configured blockchain:

```bash
python3 demo/tamper_demo.py --evidence path/to/evidence.json --field caption --value "Modified caption"
```

The original evidence is re-hashed and checked against the chain. A copy with the selected field changed is hashed again and checked against the original on-chain fingerprint. The result is based on actual hashes and contract reads.

## Testing

```bash
python3 -m pytest -q
```

Unit tests use dependency injection at model, FAISS, and blockchain boundaries, so they do not require production credentials. Live blockchain tests require a running node and are separate from the default unit suite.

## Configuration

Face model settings, image limits, FAISS paths, top-k, match weights, evidence output, RPC settings, and chain validation are controlled through `.env`. Run-time configuration is validated before the pipeline starts.

## Known Limitations

- The default search source is a local authorized dataset; no unrestricted social-media crawler is included.
- InsightFace model weights and compatible ONNX Runtime are required for real face inference.
- FAISS and Web3.py must be installed for their respective live stages.
- The current registry stores a fingerprint and provenance fields, not the original post contents.
- A live end-to-end run requires a populated dataset, built index, deployed contract, funded wallet, and reachable RPC endpoint.

## Security Notes

Private keys are read from environment variables only. Do not place secrets in source files, evidence records, logs, or Git. Evidence should be generated only from content that the operator is authorized to process.
