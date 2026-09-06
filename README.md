# TraceChain AI

> **From a face scan to a verifiable, tamper-evident record.**

[![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/API-FastAPI-009688?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![Next.js](https://img.shields.io/badge/UI-Next.js%2015-000000?logo=next.js&logoColor=white)](https://nextjs.org/)
[![Solidity](https://img.shields.io/badge/Contract-Solidity%200.8.20-363636?logo=solidity&logoColor=white)](https://soliditylang.org/)
[![Tests](https://img.shields.io/badge/tests-37%20passing-2ea44f)](#testing)

TraceChain AI takes a face image, **searches the live public web** for content showing the same
person, **independently re-verifies** each hit with its own face-recognition model, then **seals the
result on an Ethereum-compatible chain** so it can be re-checked later and proven untampered.

Every number in the interface comes from an actual run. There is no demo mode, no seeded results,
and no fabricated data anywhere in the pipeline.

```text
Face image
  → validation + quality checks
  → InsightFace detection (SCRFD) + 512-d ArcFace embedding
  → live reverse-image search on the public web (Google Lens via SerpApi)
  → download each candidate + re-embed it with our own model
  → multi-signal match scoring (face + perceptual image + metadata)
  → canonical evidence JSON → SHA-256 fingerprint
  → registered in an on-chain evidence registry
  → independent re-verification (local hash vs on-chain hash)
```

---

## Contents

- [How it meets the brief](#how-it-meets-the-brief)
- [What makes the search genuine](#what-makes-the-search-genuine)
- [Quick start](#quick-start)
- [Configuration](#configuration)
- [Blockchain](#blockchain)
- [Interface](#interface)
- [API reference](#api-reference)
- [Evidence and tamper detection](#evidence-and-tamper-detection)
- [Testing](#testing)
- [Privacy and authorization](#privacy-and-authorization)
- [Known limitations](#known-limitations)

---

## How it meets the brief

| Requirement | How it is implemented |
| --- | --- |
| **Face identification** | InsightFace `buffalo_l`: SCRFD detection with quality and confidence gates, then a normalized 512-dimensional ArcFace embedding. |
| **Web / social-media search** | A live Google Lens reverse-image search through SerpApi at runtime. Results are whatever the public web returns for that image — never a fixed list. |
| **Blockchain verification** | `EvidenceRegistry.sol` stores the SHA-256 fingerprint of the canonical evidence. Re-verification reads the record back and compares hashes, so any edit produces `TAMPER DETECTED`. |
| **Genuine, not hardcoded** | The search provider has no local corpus. Every candidate is fetched from the live web, downloaded, and re-scored with our own model before it can become a match. |

---

## What makes the search genuine

The weak point in a project like this is faking the "search" step. TraceChain avoids that in three ways.

**1. The search is a live external query.** The query image is uploaded to SerpApi, which runs a real
Google Lens visual-match search. Nothing is cached or pre-selected; two runs of the same image can
legitimately return different sources as the web changes.

**2. Google's ranking is not trusted as the answer.** Lens only proposes candidates. TraceChain then
downloads each candidate image, runs the *same* detection and ArcFace embedding used on the query,
and computes a real cosine similarity. A visually similar page with no detectable face is discarded.
The similarity you see is computed locally, not reported by Google.

**3. The match must clear a configured threshold.** Face similarity is combined with perceptual image
similarity (pHash) and, when supplied, metadata consistency. Only available signals contribute and
their weights are renormalized. Below `MATCH_THRESHOLD`, the run reports no match rather than
inventing one.

> **The honest constraint:** reverse image search can only find images that are *already published
> and indexed on the public web*. A private photo from your phone has nothing to match against and
> will correctly return no results. This is a property of reverse image search, not a defect — the
> interface says so explicitly when it happens.

---

## Quick start

### 1. Install

```bash
git clone https://github.com/ankit25bcs10610/Face-ID-Blockchain-Verification.git
cd Face-ID-Blockchain-Verification

python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

InsightFace downloads its `buffalo_l` model pack (~280 MB) on first use. Run any pipeline command
once before a demo so this happens ahead of time rather than mid-run.

### 2. Get a SerpApi key

The live search needs a [SerpApi](https://serpapi.com/) key (the free tier allows 250 searches per
month). Put it in `.env` and switch the provider on:

```env
SEARCH_PROVIDER=web_reverse_image
SERPAPI_API_KEY=your_key_here
```

### 3. Start a local chain and deploy the registry

```bash
npx ganache --port 7545 --wallet.deterministic --chain.chainId 1337
```

Copy the first account's address and private key into `.env`, then deploy:

```bash
python3 scripts/deploy_contract.py
```

Set the printed address as `CONTRACT_ADDRESS` in `.env`.

### 4. Run it

```bash
# Backend (http://127.0.0.1:8000, Swagger at /docs)
python3 -m src.api

# Frontend (http://localhost:3000)
cd frontend && npm install && cp .env.example .env.local && npm run dev
```

Point `NEXT_PUBLIC_API_URL` in `frontend/.env.local` at the backend, and make sure that origin is
listed in `ALLOWED_ORIGINS` in `.env` — a mismatch here is the usual cause of a browser-side
"failed to fetch".

### Command line

The whole pipeline also runs headless:

```bash
python3 -m src.main --image path/to/face.jpg
python3 -m src.main --image path/to/face.jpg --top-k 5 --threshold 0.80
```

---

## Configuration

All behavior is environment-backed. Copy `.env.example` to `.env` and set what you need.

| Group | Purpose |
| --- | --- |
| `FACE_*` | Model choice, detector size, minimum dimensions, quality and confidence gates. |
| `SEARCH_PROVIDER` | `web_reverse_image` for the live web search, or `authorized_dataset` for the offline local-corpus mode. |
| `SERPAPI_API_KEY`, `SERPAPI_ENDPOINT`, `SERPAPI_UPLOAD_ENDPOINT` | Live search credentials and endpoints. |
| `WEB_SEARCH_MAX_ATTEMPTS`, `WEB_SEARCH_MAX_CANDIDATES_SCANNED` | Retry budget and how many candidates get re-verified per run. |
| `TOP_K`, `MATCH_THRESHOLD`, `*_WEIGHT` | Candidate count, match decision, and multi-signal weighting. |
| `EVIDENCE_DIR`, `EVIDENCE_VERSION` | Where canonical evidence is written. |
| `BLOCKCHAIN_RPC_URL`, `PRIVATE_KEY`, `WALLET_ADDRESS`, `CONTRACT_ADDRESS`, `CHAIN_ID` | Chain connection, signing, and the deployed registry. |
| `API_HOST`, `API_PORT`, `ALLOWED_ORIGINS`, `API_MAX_UPLOAD_BYTES` | API binding, CORS, and upload limit. |

Configuration is validated before every run: weights, thresholds, detector dimensions, blockchain
mode, and provider-specific requirements are all checked up front rather than failing mid-pipeline.

`.env` is git-ignored. Only `.env.example` (placeholders) is tracked.

### Two search modes

| Mode | Behavior |
| --- | --- |
| `web_reverse_image` | Live Google Lens search of the public web. Needs a SerpApi key. This is the mode the project is built around. |
| `authorized_dataset` | Offline FAISS search over a local consented corpus in `data/posts/`, built with `python3 scripts/build_index.py`. Useful for development without spending search credits. |

---

## Blockchain

**Chain used:** a local Ganache EVM (chain ID `1337`) by default. Any Ethereum-compatible endpoint
works — point `BLOCKCHAIN_RPC_URL` at a testnet and set a funded key to use one instead.

`contracts/EvidenceRegistry.sol` is deliberately minimal:

```solidity
function registerEvidence(bytes32 evidenceHash) external;   // rejects empty and duplicate hashes
function verifyEvidence(bytes32 evidenceHash) external view returns (bool);
function getEvidence(bytes32 evidenceHash) external view returns (bytes32, uint256, address, bool);
```

Only the fingerprint and its provenance go on-chain — never the image, and never personal data.
The Web3 client can enforce an expected `CHAIN_ID` so evidence cannot be silently registered against
the wrong network.

---

## Interface

The Next.js operator console has three pages, all rendering backend responses only:

- **Home** — upload a scan, watch the ten pipeline stages resolve live, then read the match, its
  discovered source, the evidence hash, the transaction, and the re-verification verdict.
- **Evidence** — browse every record this machine has generated, with its discovered source, face
  scores, and fingerprints. Records are read from the API, and any JSON file can be opened locally.
- **Verify** — submit an evidence file for independent canonicalization, re-hashing, and comparison
  against the chain.

It ships with a dark theme and a light theme, toggled from the header. When the API, search provider,
or chain is unreachable the header says so, and failures name the stage that actually failed rather
than a generic error.

---

## API reference

| Method | Route | Purpose |
| --- | --- | --- |
| `GET` | `/health` | API, face model, search provider, and chain status. |
| `POST` | `/face/analyze` | Validate an image and return real face-processing diagnostics. |
| `POST` | `/pipeline/run` | Run the full end-to-end pipeline on an uploaded image. |
| `POST` | `/search` | Search with a supplied 512-dimensional embedding. |
| `GET` | `/evidence` | List stored evidence records. |
| `GET` | `/evidence/{id}` | Read one stored evidence record. |
| `POST` | `/verify` | Re-hash uploaded evidence and compare it with the chain. |

Uploads are written to unique temporary files, restricted by extension and size, and deleted after
processing. Errors return `{ "error": { "code": "...", "message": "..." } }` with no stack traces or
secrets. Swagger UI is at `/docs`.

---

## Evidence and tamper detection

Evidence is canonicalized with sorted keys, stable separators, and UTF-8 before hashing, so the same
record always produces the same SHA-256 — and any change produces a different one.

After a successful run:

```bash
python3 demo/tamper_demo.py \
  --evidence data/evidence/<evidence-id>.json \
  --field caption \
  --value "Modified caption"
```

The command hashes the original, fetches the real on-chain record, deep-copies and modifies the
evidence, hashes the copy, and compares both against the chain. The original returns `VERIFIED`;
the modified copy returns `TAMPER DETECTED`. Both verdicts are computed from real hashes and real
contract reads.

---

## Testing

```bash
python3 -m pytest -q      # 37 passing
```

Covers image validation, detection behavior, embedding normalization, index generation, FAISS result
mapping, ranking, confidence scoring, canonical JSON, hashing, evidence persistence, tamper
detection, and injected-boundary pipeline integration. Doubles are used only at the external model,
FAISS, and blockchain boundaries — no test claims a live transaction.

---

## Privacy and authorization

- Only upload images you own or are authorized to process.
- The query image is sent to SerpApi to perform the lookup and is discarded there after ten minutes.
  It is never published to a public URL by this project.
- Nothing about the person goes on-chain — only a hash.
- `.env`, keys, wallets, generated evidence, indexes, and the downloaded-candidate cache are all
  git-ignored.
- A high similarity score is not proof of legal identity and must not be the sole basis of a
  high-impact decision.

---

## Known limitations

- **Reverse image search only finds already-public images.** A private photo with no web presence
  returns no matches. That is correct behavior, not a failure.
- **Search results vary between runs.** The live web changes, and Google's matching is not
  deterministic. The pipeline retries, but a run can legitimately come back empty.
- **The free SerpApi tier allows 250 searches per month**, and each pipeline run uses at least one.
- **Candidate re-verification depends on the candidate image being fetchable** and containing a
  detectable face; pages that only expose tiny thumbnails are skipped.
- **Perceptual image similarity is a supporting signal**, not standalone image forensics.
- **On-chain registration proves a fingerprint existed at a chain state.** It does not prove the
  underlying content is truthful, nor that the identification is correct.
- Face recognition accuracy varies with pose, lighting, occlusion, and demographic factors. Treat
  every result as a lead requiring human review.
