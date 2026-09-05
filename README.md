# TraceChain AI

> **From authorized face scans to verifiable, tamper-evident evidence.**

TraceChain AI is a privacy-aware Python pipeline that demonstrates how a face image can be matched against **authorized content only**, verified using multiple signals, converted into deterministic evidence, and anchored to an Ethereum-compatible blockchain.

```text
Authorized face image
  -> validation and face processing
  -> authorized dataset search
  -> FAISS similarity ranking
  -> multi-signal match verification
  -> canonical evidence JSON
  -> SHA-256 fingerprint
  -> EVM smart-contract registration
  -> independent re-verification
```

## Contents

- [Privacy and Authorization](#privacy-and-authorization)
- [Architecture](#architecture)
- [Workflow](#workflow)
- [Technology Stack](#technology-stack)
- [Installation](#installation)
- [Configuration](#configuration)
- [Dataset and Indexing](#authorized-dataset-and-indexing)
- [Blockchain Deployment](#blockchain-deployment)
- [Running the Pipeline](#running-the-pipeline)
- [Evidence and Tampering](#evidence-and-tampering)
- [Testing](#testing)
- [Security and Limitations](#security-and-limitations)

## Privacy and Authorization

TraceChain AI does **not** identify unknown people across arbitrary public social-media accounts. Its default `AuthorizedDatasetProvider` searches only the configured local `data/posts/` corpus.

Images and metadata added to that corpus must be user-owned, explicitly consented, or otherwise authorized for this demonstration. Any future provider must maintain the same consent, platform-permission, and legal-compliance boundary. A high similarity score is not legal identity proof and must not be used as a sole decision in a high-impact setting.

## Architecture

![TraceChain AI architecture: authorized face processing, FAISS search, verification, evidence hashing, blockchain registration, and re-verification](assets/tracechain-architecture.png)

The diagram summarizes the real pipeline implementation. The optional reverse-image-search branch shown is intentionally not enabled by the default provider; the repository searches only the authorized local dataset described in this README.

## Workflow

1. **Validate and process the input.** The image must decode as color, satisfy configurable dimensions and quality limits, and contain one face by default. InsightFace returns landmarks, detection confidence, and a normalized 512-dimensional embedding.
2. **Index authorized content.** The index builder processes permitted post images, creates real embeddings, normalizes them, and persists a FAISS `IndexFlatIP` index, embedding matrix, manifest, and index metadata.
3. **Search dynamically.** The query embedding is submitted to the configured provider. FAISS performs nearest-neighbor retrieval at runtime; results are mapped back to persisted post metadata and ranked by actual similarity.
4. **Verify the best candidate.** Face-vector similarity is combined with perceptual image similarity when both images exist and metadata consistency when query metadata is supplied. Only available signals participate, and their configured weights are normalized.
5. **Generate evidence.** A successful match produces a JSON-safe record containing generated IDs, source data, calculated scores, fingerprints, and timestamps.
6. **Anchor the fingerprint.** Canonical JSON is serialized with sorted keys, stable separators, UTF-8 encoding, and SHA-256. The 32-byte hash is registered through the Solidity contract.
7. **Re-verify later.** The evidence is canonicalized and hashed again, the on-chain record is fetched, and the hashes are compared. A changed evidence field produces a different hash and `TAMPER DETECTED`.

## Technology Stack

| Area | Components |
| --- | --- |
| Runtime | Python 3.10+ |
| Vision | InsightFace, ArcFace, OpenCV, Pillow, NumPy |
| Search | FAISS normalized inner-product index |
| Integrity | Canonical JSON, UTF-8, SHA-256, ImageHash |
| Blockchain | Solidity, Web3.py, py-solc-x, local EVM or testnet |
| Testing | Pytest |

## Repository Layout

```text
contracts/
  EvidenceRegistry.sol          # On-chain evidence fingerprint registry
data/
  posts/                        # Authorized post directories
  embeddings/                   # Generated normalized embedding matrix
  faiss/                        # FAISS index, manifest, and metadata
  evidence/                     # Generated canonical evidence files
demo/
  demo_pipeline.py              # Pipeline entry-point wrapper
  tamper_demo.py                # Re-verification/tampering CLI
scripts/
  build_index.py                # Authorized dataset index builder
  deploy_contract.py            # Contract compile and deployment script
src/
  face/                         # Validation, detection, alignment, encoding
  search/                       # Providers, indexing, FAISS, ranking
  verification/                 # Match scoring, evidence, hashing
  blockchain/                   # RPC client, registry, re-verification
  config/                       # Environment-backed settings
  main.py                       # End-to-end command-line pipeline
tests/                          # Unit and injected-boundary integration tests
```

## Installation

```bash
git clone https://github.com/ankit25bcs10610/Face-ID-Blockchain-Verification.git
cd Face-ID-Blockchain-Verification

python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

InsightFace may download model assets when first initialized. Real inference also needs a compatible ONNX Runtime environment; install the platform-appropriate runtime if InsightFace reports it missing.

## Configuration

All runtime behavior is environment-backed. Copy `.env.example` to `.env`, then set only the values appropriate for your chosen environment.

| Variable group | Purpose |
| --- | --- |
| `FACE_*` | InsightFace model choice, detector size, image limits, quality, and face confidence. |
| `POSTS_DIR`, `EMBEDDINGS_DIR`, `FAISS_DIR` | Authorized corpus and generated artifact locations. |
| `TOP_K` | Number of nearest-neighbor candidates returned. |
| `MATCH_THRESHOLD`, `*_WEIGHT` | Match decision and multi-signal scoring. |
| `EVIDENCE_DIR`, `EVIDENCE_VERSION` | Evidence persistence configuration. |
| `BLOCKCHAIN_RPC_URL` | Local or testnet Ethereum-compatible RPC endpoint. |
| `PRIVATE_KEY`, `WALLET_ADDRESS` | Signing credentials; never commit these. |
| `CONTRACT_ADDRESS`, `CONTRACT_ARTIFACT_PATH` | Deployed registry configuration. |
| `CHAIN_ID` | Optional expected chain ID; `0` disables enforcement. |
| `BLOCKCHAIN_MODE` | Validated as `local` or `rpc`. |

The application validates top-k, thresholds, weights, detector dimensions, confidence limits, and blockchain mode before a run.

## Authorized Dataset and Indexing

Each authorized post belongs in its own directory:

```text
data/posts/
  post_001/
    image.jpg
    metadata.json
```

`metadata.json` requires a non-empty `post_id`. The following fields are strongly recommended because they are preserved in evidence and can be used during metadata verification:

```json
{
  "post_id": "post_001",
  "platform": "authorized_demo",
  "post_url": "https://example.invalid/post_001",
  "caption": "Authorized demonstration content",
  "timestamp": "2026-09-06T10:00:00Z"
}
```

This is a schema example, not a preselected result. The pipeline does not insert sample post data or preselect the winner.

Build the index:

```bash
python3 scripts/build_index.py
```

Optional artifact paths can be passed without source edits:

```bash
python3 scripts/build_index.py \
  --posts-dir data/posts \
  --embeddings-dir data/embeddings \
  --faiss-dir data/faiss
```

The builder creates the embedding matrix, FAISS index, row-aligned candidate manifest, and versioned metadata. Invalid directories are reported and skipped. A build with no valid authorized records fails rather than fabricating embeddings or candidates.

## Blockchain Deployment

Start Ganache or another Ethereum-compatible local/test network, then set a funded development or test account in `.env`:

```env
BLOCKCHAIN_RPC_URL=http://127.0.0.1:7545
PRIVATE_KEY=your_private_key
WALLET_ADDRESS=your_wallet_address
BLOCKCHAIN_MODE=local
CHAIN_ID=0
```

Compile and deploy:

```bash
python3 scripts/deploy_contract.py
```

The deployment artifact contains ABI, bytecode, deployed address, transaction hash, block number, and chain ID. Set `CONTRACT_ADDRESS` in `.env` to the printed deployed address.

## Running the Pipeline

Build the index and deploy the registry first, then run:

```bash
python3 -m src.main --image path/to/authorized-face.jpg
```

Optional controls:

```bash
python3 -m src.main \
  --image path/to/authorized-face.jpg \
  --top-k 5 \
  --threshold 0.80 \
  --query-metadata path/to/query-metadata.json
```

The CLI prints values from the current execution: image dimensions, face confidence, candidate count, calculated confidence, evidence path and hash, transaction receipt data, and re-verification status. It does not display a successful stage when that stage fails.

The same entry point is available as:

```bash
python3 demo/demo_pipeline.py --image path/to/authorized-face.jpg
```

## Evidence and Tampering

Evidence contains dynamic provenance: a generated evidence ID, generated search ID, provider name, retrieved candidate metadata, calculated signals, configured threshold, image fingerprint, and UTC creation time. Canonicalization sorts keys and uses stable JSON separators before SHA-256 hashing.

After a successful pipeline run, demonstrate tamper detection with the saved evidence file:

```bash
python3 demo/tamper_demo.py \
  --evidence data/evidence/your-evidence-id.json \
  --field caption \
  --value "Modified authorized caption"
```

The command re-hashes the original evidence, fetches the actual chain record, deep-copies the evidence, modifies the specified field, hashes the modified copy, and compares both hashes with the original record. The verdict is calculated from real hashes and contract reads: the original can be `VERIFIED`; a meaningful modification is `TAMPER DETECTED`.

## Testing

```bash
python3 -m pytest -q
```

The suite covers image validation, detection behavior, embedding normalization, index generation, FAISS-result mapping, ranking, confidence scoring, canonical JSON, hashing, evidence persistence, tampering detection, and injected-boundary pipeline integration.

Unit tests use controlled doubles only at external model, FAISS, and blockchain boundaries. They do not claim a live transaction. A live end-to-end validation needs a populated authorized dataset, InsightFace runtime, FAISS installation, reachable EVM node, deployed contract, and funded wallet.

## Security and Limitations

### Security model

- `.env`, key files, PEM files, wallet folders, generated evidence, indexes, build artifacts, and logs are ignored by Git.
- Private keys are read from environment variables or explicit function parameters only.
- The contract rejects empty and duplicate fingerprints.
- The Web3 client can enforce a configured chain ID.
- The blockchain stores an evidence fingerprint and provenance, not the original image bytes.

### Known limitations

- The only built-in source is a local authorized dataset; no unrestricted public-social-media crawler is included.
- `IndexFlatIP` is exact and appropriate for a demonstration corpus; a large deployment may require a different FAISS index strategy.
- Similarity is not legal identity proof or source-truth proof.
- Perceptual image similarity is optional and is not standalone image-forensics proof.
- Blockchain registration proves a particular fingerprint existed at a chain state; it does not prove that underlying content was truthful or authorized.
- Live blockchain execution cannot be verified without user-provided local/testnet infrastructure and credentials.

## Submission Checklist

- [ ] Add only authorized or consented content to `data/posts/`
- [ ] Build the FAISS index
- [ ] Start and configure an EVM node
- [ ] Deploy `EvidenceRegistry.sol`
- [ ] Set `CONTRACT_ADDRESS` in `.env`
- [ ] Run the pipeline successfully
- [ ] Run the tampering demonstration
- [ ] Record the terminal demonstration
