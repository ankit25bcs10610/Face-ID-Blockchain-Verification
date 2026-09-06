# ORYNEX AI

> Identity intelligence that turns an authorized face scan into verifiable, tamper-evident evidence.

[![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB?logo=python&logoColor=white)](https://www.python.org/) [![FastAPI](https://img.shields.io/badge/API-FastAPI-009688?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/) [![Next.js](https://img.shields.io/badge/UI-Next.js%2015-000000?logo=next.js&logoColor=white)](https://nextjs.org/) [![Solidity](https://img.shields.io/badge/Contract-Solidity%200.8.20-363636?logo=solidity&logoColor=white)](https://soliditylang.org/)

ORYNEX AI analyzes an authorized face image, searches for related public-web content, independently re-verifies candidate images, and seals the resulting evidence fingerprint on an Ethereum-compatible blockchain.

The platform is evidence-first: scores come from the running pipeline, search results come from the configured provider, and the blockchain stores only a cryptographic fingerprint—not an image or personal data.

## How it works

```text
Authorized image → validation → InsightFace + ArcFace embedding
                 → live reverse-image search or authorized local corpus
                 → candidate re-verification → multi-signal scoring
                 → canonical evidence JSON → SHA-256 → on-chain verification
```

## Capabilities

| Capability | Implementation |
| --- | --- |
| Face analysis | InsightFace `buffalo_l`, SCRFD detection, and normalized 512-dimensional ArcFace embeddings |
| Search | Live Google Lens through SerpApi, or offline FAISS search over an authorized dataset |
| Match scoring | Weighted face similarity, perceptual image similarity, and optional metadata consistency |
| Evidence | Canonical JSON with stable serialization and SHA-256 hashing |
| Blockchain | Minimal Solidity evidence registry on Ganache or another EVM-compatible network |
| Console | Next.js dashboard with live pipeline stages, evidence browsing, and verification |

ORYNEX AI does not treat a search provider’s ranking as proof. Candidates are fetched at runtime, processed by the same local face pipeline as the query, and discarded if no face can be detected. Only candidates above `MATCH_THRESHOLD` are reported.

## Project structure

```text
├── contracts/       Solidity evidence registry
├── frontend/        Next.js operator console
├── scripts/         Deployment and index-building utilities
├── src/             FastAPI, face, search, verification, and services
├── tests/            Automated test suite
├── data/             Local evidence, indexes, and runtime artifacts
└── .env.example      Configuration template
```

## Quick start

### Prerequisites

- Python 3.10+
- Node.js 18+ and npm
- Ganache or another Ethereum-compatible JSON-RPC endpoint
- A SerpApi key for live reverse-image search

### Install

```bash
git clone https://github.com/ankit25bcs10610/Face-ID-Blockchain-Verification.git
cd Face-ID-Blockchain-Verification
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

InsightFace downloads the `buffalo_l` model pack on first use.

### Configure search

```env
# Live public-web search
SEARCH_PROVIDER=web_reverse_image
SERPAPI_API_KEY=your_serpapi_key

# Or use the local authorized corpus during development
# SEARCH_PROVIDER=authorized_dataset
```

### Start the blockchain

```bash
npx ganache --port 7545 --wallet.deterministic --chain.chainId 1337
python3 scripts/deploy_contract.py
```

Set the deployed address as `CONTRACT_ADDRESS` in `.env`.

### Start the API and frontend

```bash
# Terminal 1 — API at http://127.0.0.1:8000
source .venv/bin/activate
python3 -m src.api

# Terminal 2 — frontend at http://localhost:3000
cd frontend
npm install
cp .env.example .env.local
npm run dev -- --port 3000
```

Swagger UI is available at `http://127.0.0.1:8000/docs`. If the API uses another origin, set `NEXT_PUBLIC_API_URL` in `frontend/.env.local` and include the frontend origin in `ALLOWED_ORIGINS`.

## Console pages

- **Home** — upload an image, follow the ten pipeline stages, and inspect scores, evidence, and the blockchain transaction.
- **Evidence** — browse stored records or open an evidence JSON file locally.
- **Verify** — canonicalize, re-hash, and compare a record against the on-chain fingerprint.

## Configuration

| Variables | Purpose |
| --- | --- |
| `FACE_*` | Model, detector size, dimensions, confidence, and quality gates |
| `SEARCH_PROVIDER` | `web_reverse_image` or `authorized_dataset` |
| `SERPAPI_*` | Live reverse-image search credentials and endpoints |
| `TOP_K`, `MATCH_THRESHOLD`, `*_WEIGHT` | Candidate count, threshold, and scoring weights |
| `EVIDENCE_DIR`, `EVIDENCE_VERSION` | Evidence storage and schema version |
| `BLOCKCHAIN_*`, `PRIVATE_KEY`, `CONTRACT_ADDRESS` | RPC, wallet, chain, and registry settings |
| `API_HOST`, `API_PORT`, `ALLOWED_ORIGINS` | API binding and CORS |

## API reference

| Method | Route | Description |
| --- | --- | --- |
| `GET` | `/health` | API, face model, search, and blockchain status |
| `POST` | `/face/analyze` | Validate an image and return face diagnostics |
| `POST` | `/pipeline/run` | Run the complete pipeline on an uploaded image |
| `POST` | `/search` | Search using a supplied face embedding |
| `GET` | `/evidence` | List stored evidence summaries |
| `GET` | `/evidence/{id}` | Read one evidence record |
| `POST` | `/verify` | Re-hash evidence and compare it with the chain |

Errors use a consistent shape: `{"error":{"code":"...","message":"..."}}`.

## Evidence and tamper detection

Evidence is serialized with sorted keys, stable separators, and UTF-8 encoding before hashing. The same canonical record produces the same SHA-256; any content change produces a different fingerprint. Only the fingerprint and provenance are registered on-chain.

```bash
python3 demo/tamper_demo.py \
  --evidence data/evidence/<evidence-id>.json \
  --field caption \
  --value "Modified caption"
```

The original record should verify; the modified copy should report `TAMPER DETECTED`.

## Testing

```bash
python3 -m pytest -q
```

The suite covers image validation, face detection, embedding normalization, indexing, ranking, confidence scoring, canonical JSON, hashing, evidence persistence, tamper detection, and pipeline integration at external boundaries.

## Security, privacy, and limitations

- Process only images you own or are authorized to analyze.
- The live search provider receives the query image as required for reverse-image search.
- No image or personal data is written to the blockchain; only a cryptographic fingerprint is registered.
- Uploads are size/extension limited, written to unique temporary files, and removed after processing.
- Search only finds public, indexed, reachable content; results can vary as the web changes.
- A similarity score is not proof of legal identity and must not be the sole basis of a high-impact decision.
- Face recognition varies with pose, lighting, occlusion, image quality, and demographic factors. Every result requires human review.

## Responsible use

ORYNEX AI is an evidence-assistance system, not an autonomous identity authority. Use it with consent, document the review process, and require qualified human judgment for consequential decisions.
