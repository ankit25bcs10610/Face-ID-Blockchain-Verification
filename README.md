# TraceChain AI

> **From authorized face scans to verifiable, tamper-evident evidence.**

[![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/API-FastAPI-009688?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![Next.js](https://img.shields.io/badge/UI-Next.js-000000?logo=next.js&logoColor=white)](https://nextjs.org/)
[![Tests](https://img.shields.io/badge/tests-35%20passing-2ea44f)](#testing)

TraceChain AI is an end-to-end, consent-first evidence pipeline for authorized visual content. It combines face processing, vector retrieval, multi-signal verification, deterministic evidence hashing, and Ethereum-compatible registry anchoring behind a CLI, REST API, and operator console.

> **Important:** This project is a technical demonstration, not an identity service or a substitute for legal, forensic, or high-impact decision-making review.

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
- [Frontend](#frontend)
- [FastAPI Backend](#fastapi-backend)
- [Running the Pipeline](#running-the-pipeline)
- [Evidence and Tampering](#evidence-and-tampering)
- [Testing](#testing)
- [Security and Limitations](#security-and-limitations)

## Privacy and Authorization

TraceChain AI does **not** identify unknown people across arbitrary public social-media accounts. Its default `AuthorizedDatasetProvider` searches only the configured local `data/posts/` corpus.

Images and metadata added to that corpus must be user-owned, explicitly consented, or otherwise authorized for this demonstration. Any future provider must maintain the same consent, platform-permission, and legal-compliance boundary. A high similarity score is not legal identity proof and must not be used as a sole decision in a high-impact setting.

## Architecture

![TraceChain AI architecture: authorized face processing, FAISS search, verification, evidence hashing, blockchain registration, and re-verification](assets/tracechain-architecture.png)

The diagram summarizes the implemented system. The API and frontend are interaction layers; the business logic remains in the reusable Python core. The optional reverse-image-search branch shown in the diagram is intentionally not enabled by the default provider. Searches are restricted to the configured authorized local dataset.

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
  api/                          # FastAPI routes, schemas, errors, middleware
src/services/
  pipeline_service.py           # Secure API adapter around the core pipeline
src/main.py                     # End-to-end command-line pipeline
tests/                          # Unit and injected-boundary integration tests
frontend/                       # Next.js operator console
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

## Frontend

The `frontend/` directory contains the TraceChain AI operator console. It is a Next.js App Router application written in TypeScript with a custom responsive visual system, Framer Motion transitions, and Lucide icons. The interface is intentionally data-driven: candidate posts, confidence scores, evidence hashes, transaction details, and verdicts are rendered only from API responses.

### Run the frontend

```bash
cd frontend
npm install
cp .env.example .env.local
npm run dev
```

For a production build:

```bash
npm run build
npm start
```

Configure `NEXT_PUBLIC_API_URL` in `frontend/.env.local` with the URL of the FastAPI service, plus endpoint variables if the service uses different routes. The client currently calls the configured health endpoint and pipeline endpoint, defaulting to `/health` and `/pipeline/run` respectively.

### Backend boundary

The frontend communicates with the FastAPI adapter through the configured REST base URL. It renders only backend responses and shows unavailable or error states when the API, FAISS index, or blockchain dependencies are not ready; it does not provide a fabricated demo mode.

### Available pages

- `/` and `/dashboard`: upload an authorized face scan, run the configured pipeline endpoint, and inspect returned match, evidence, blockchain, and re-verification data.
- `/evidence`: locally inspect a selected evidence JSON file without modifying it or sending it anywhere.
- `/verify`: submit an evidence JSON file to the configured verification endpoint.

The frontend does not provide a fake demo mode. With no API configured, its unavailable and error states are the expected behavior.

## FastAPI Backend

The API adapter is available at `src/api/main.py` and delegates execution to the existing core modules. It does not duplicate face processing, FAISS search, evidence hashing, blockchain registration, or re-verification logic.

### Run the API

Install the API dependencies from the repository root, then start Uvicorn:

```bash
pip install -r requirements.txt
python -m src.api
```

Swagger UI is available at `http://127.0.0.1:8000/docs` when the service is running. The host, port, CORS origins, and upload limit are configured through `API_HOST`, `API_PORT`, `ALLOWED_ORIGINS`, and `API_MAX_UPLOAD_BYTES`.

### API endpoints

| Method | Route | Purpose |
| --- | --- | --- |
| `GET` | `/health` | Reports API, InsightFace dependency, FAISS index, and blockchain status. |
| `POST` | `/face/analyze` | Validates an uploaded image and returns actual face-processing diagnostics. |
| `POST` | `/pipeline/run` | Executes the existing end-to-end pipeline with an uploaded image. |
| `POST` | `/search` | Searches the configured authorized FAISS dataset using a supplied 512-dimensional embedding. |
| `POST` | `/verify` | Canonicalizes uploaded evidence, recreates its hash, and compares it with the blockchain record. |

Image uploads are written to unique temporary files, restricted to configured extensions and size, and deleted after processing. API errors use `{ "error": { "code": "...", "message": "..." } }` without returning stack traces or secrets.

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

## Contributor

- [Ankit Pandey](https://github.com/ankit25bcs10610) - Project creator and maintainer

TraceChain AI is maintained by Ankit Pandey.
