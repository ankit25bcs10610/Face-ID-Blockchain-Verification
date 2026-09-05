"""TraceChain AI end-to-end command-line pipeline."""

import argparse
import json
import logging
import time
import uuid
from pathlib import Path

import imagehash
from PIL import Image

from src.blockchain.verifier import reverify_evidence
from src.face.detector import detect_face
from src.face.encoder import extract_embedding
from src.face.quality import validate_image
from src.search.orchestrator import search_detailed
from src.verification.evidence import create_evidence, save_evidence
from src.verification.hasher import generate_hash
from src.verification.matcher import verify_match


logger = logging.getLogger("tracechain")


def _read_query_metadata(path: str | Path | None) -> dict | None:
    if path is None:
        return None
    try:
        value = json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(f"Unable to read query metadata: {path}") from exc
    if not isinstance(value, dict):
        raise ValueError("Query metadata must be a JSON object")
    return value


def _image_hash(path: str | Path) -> str:
    try:
        return str(imagehash.phash(Image.open(path)))
    except (OSError, ValueError) as exc:
        raise ValueError(f"Unable to hash input image: {path}") from exc


def run_pipeline(
    image_path: str | Path,
    top_k: int,
    threshold: float,
    query_metadata: dict | None = None,
    blockchain_register=None,
    evidence_reader=None,
) -> dict:
    """Run every pipeline stage and return a serializable execution result."""
    image_path = Path(image_path)
    from src.config import settings
    settings.validate()
    pipeline_id = str(uuid.uuid4())

    def stage(name: str, started: float, success: bool = True, error: str | None = None) -> None:
        logger.info(
            "pipeline_stage pipeline_id=%s stage=%s success=%s duration_ms=%.2f%s",
            pipeline_id, name, success, (time.perf_counter() - started) * 1000,
            f" error={error}" if error else "",
        )
    print("TRACECHAIN AI")
    print("Face Identification & Blockchain Verification")
    print("=" * 48)

    print("[1/10] Validating image...")
    started = time.perf_counter()
    _, quality = validate_image(image_path)
    stage("IMAGE_VALIDATION", started)
    print(f"  Image valid: {quality.width}x{quality.height}, quality={quality.quality_score:.3f}")

    print("[2/10] Detecting face...")
    started = time.perf_counter()
    detected_face = detect_face(image_path)
    stage("FACE_DETECTION", started)
    print(f"  Face detected: confidence={detected_face.detection_confidence:.3f}")

    print("[3/10] Generating embedding...")
    started = time.perf_counter()
    embedding = extract_embedding(image_path)
    stage("EMBEDDING_GENERATION", started)
    print(f"  Embedding dimensions: {embedding.shape[0]}")

    print("[4/10] Searching authorized content...")
    started = time.perf_counter()
    search_response = search_detailed(embedding, top_k=top_k)
    stage("CONTENT_SEARCH", started)
    candidates = search_response.results
    if not candidates:
        raise RuntimeError("No candidate posts found")
    print(f"  Candidates found: {len(candidates)}")

    print("[5/10] Ranking candidates...")
    candidate = candidates[0]
    print(f"  Best candidate: {candidate.post_id} ({candidate.similarity_score:.3f})")

    print("[6/10] Verifying best match...")
    started = time.perf_counter()
    match = verify_match(candidate, query_image_path=image_path, query_metadata=query_metadata, threshold=threshold)
    stage("MATCH_VERIFICATION", started)
    print(f"  Match: {'FOUND' if match.match else 'NOT FOUND'}; confidence={match.confidence:.3f}")
    if not match.match:
        raise RuntimeError(f"No match exceeded the configured threshold ({threshold:.3f})")

    print("[7/10] Generating evidence...")
    started = time.perf_counter()
    evidence = create_evidence(
        match,
        image_hash=_image_hash(candidate.image_path) if candidate.image_path else None,
        search=search_response,
        threshold=threshold,
    )
    evidence_path = save_evidence(evidence)
    stage("EVIDENCE_GENERATION", started)
    print(f"  Evidence: {evidence_path}")

    print("[8/10] Hashing evidence...")
    started = time.perf_counter()
    evidence_hash = generate_hash(evidence)
    stage("HASH_GENERATION", started)
    print(f"  SHA-256: {evidence_hash}")

    print("[9/10] Registering evidence on blockchain...")
    if blockchain_register is None:
        from src.blockchain.registry import register_evidence
        blockchain_register = register_evidence
    started = time.perf_counter()
    blockchain = blockchain_register(evidence_hash)
    stage("BLOCKCHAIN_UPLOAD", started)
    print(f"  Transaction hash: {blockchain['transaction_hash']}")
    print(f"  Block number: {blockchain['block_number']}")
    print(f"  Timestamp: {blockchain['timestamp']}")
    print(f"  Contract address: {blockchain['contract_address']}")

    print("[10/10] Re-verifying evidence...")
    started = time.perf_counter()
    verification = reverify_evidence(evidence, evidence_reader=evidence_reader)
    stage("RE_VERIFICATION", started)
    print(f"  {verification['status']}")
    return {
        "pipeline_id": pipeline_id,
        "search": search_response.as_dict(),
        "candidate": candidate,
        "match": match.as_dict(),
        "evidence": evidence,
        "evidence_path": str(evidence_path),
        "evidence_hash": evidence_hash,
        "blockchain": blockchain,
        "reverification": verification,
    }


def main() -> int:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
    )
    parser = argparse.ArgumentParser(description="Run TraceChain AI end-to-end")
    parser.add_argument("--image", required=True, help="Input face image")
    parser.add_argument("--top-k", type=int, default=None)
    parser.add_argument("--threshold", type=float, default=None)
    parser.add_argument("--query-metadata", help="Optional JSON metadata file for consistency scoring")
    args = parser.parse_args()
    from src.config import settings
    try:
        run_pipeline(
            args.image,
            args.top_k if args.top_k is not None else settings.TOP_K,
            args.threshold if args.threshold is not None else settings.MATCH_THRESHOLD,
            _read_query_metadata(args.query_metadata),
        )
    except Exception as exc:
        parser.error(str(exc))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
