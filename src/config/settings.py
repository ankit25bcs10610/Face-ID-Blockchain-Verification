"""Runtime configuration for TraceChain AI."""

import os

from dotenv import load_dotenv

load_dotenv()


def _env_bool(name: str, default: bool) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


FACE_MODEL_NAME = os.getenv("FACE_MODEL_NAME", "buffalo_l")
FACE_DET_SIZE = int(os.getenv("FACE_DET_SIZE", "640"))
FACE_MIN_WIDTH = int(os.getenv("FACE_MIN_WIDTH", "160"))
FACE_MIN_HEIGHT = int(os.getenv("FACE_MIN_HEIGHT", "160"))
FACE_MIN_QUALITY = float(os.getenv("FACE_MIN_QUALITY", "0.0"))
FACE_MIN_CONFIDENCE = float(os.getenv("FACE_MIN_CONFIDENCE", "0.0"))
ALLOW_MULTIPLE_FACES = _env_bool("ALLOW_MULTIPLE_FACES", False)
POSTS_DIR = os.getenv("POSTS_DIR", "data/posts")
EMBEDDINGS_DIR = os.getenv("EMBEDDINGS_DIR", "data/embeddings")
FAISS_DIR = os.getenv("FAISS_DIR", "data/faiss")
INDEX_NAME = os.getenv("INDEX_NAME", "faces.index")
MANIFEST_NAME = os.getenv("MANIFEST_NAME", "manifest.json")
INDEX_METADATA_NAME = os.getenv("INDEX_METADATA_NAME", "index_metadata.json")
EMBEDDINGS_NAME = os.getenv("EMBEDDINGS_NAME", "embeddings.npy")
IMAGE_EXTENSIONS = tuple(
    extension.strip().lower()
    for extension in os.getenv("IMAGE_EXTENSIONS", ".jpg,.jpeg,.png").split(",")
    if extension.strip()
)
TOP_K = int(os.getenv("TOP_K", "5"))
MATCH_THRESHOLD = float(os.getenv("MATCH_THRESHOLD", "0.80"))
FACE_SIMILARITY_WEIGHT = float(os.getenv("FACE_SIMILARITY_WEIGHT", "0.70"))
IMAGE_SIMILARITY_WEIGHT = float(os.getenv("IMAGE_SIMILARITY_WEIGHT", "0.20"))
METADATA_CONSISTENCY_WEIGHT = float(os.getenv("METADATA_CONSISTENCY_WEIGHT", "0.10"))
METADATA_FIELDS = tuple(
    field.strip() for field in os.getenv("METADATA_FIELDS", "platform,caption,timestamp").split(",") if field.strip()
)
EVIDENCE_DIR = os.getenv("EVIDENCE_DIR", "data/evidence")
EVIDENCE_VERSION = os.getenv("EVIDENCE_VERSION", "1.0")
BLOCKCHAIN_RPC_URL = os.getenv("BLOCKCHAIN_RPC_URL", "")
PRIVATE_KEY = os.getenv("PRIVATE_KEY", "")
WALLET_ADDRESS = os.getenv("WALLET_ADDRESS", "")
CONTRACT_ADDRESS = os.getenv("CONTRACT_ADDRESS", "")
CONTRACT_ARTIFACT_PATH = os.getenv("CONTRACT_ARTIFACT_PATH", "build/EvidenceRegistry.json")
CHAIN_ID = int(os.getenv("CHAIN_ID", "0"))
BLOCKCHAIN_MODE = os.getenv("BLOCKCHAIN_MODE", "local").strip().lower()


def validate() -> None:
    """Validate cross-field runtime configuration before a pipeline run."""
    if TOP_K <= 0:
        raise ValueError("TOP_K must be greater than zero")
    if not 0 <= MATCH_THRESHOLD <= 1:
        raise ValueError("MATCH_THRESHOLD must be between zero and one")
    weights = (FACE_SIMILARITY_WEIGHT, IMAGE_SIMILARITY_WEIGHT, METADATA_CONSISTENCY_WEIGHT)
    if any(weight < 0 for weight in weights) or sum(weights) <= 0:
        raise ValueError("Match weights must be non-negative and have a positive total")
    if FACE_DET_SIZE <= 0 or FACE_MIN_WIDTH <= 0 or FACE_MIN_HEIGHT <= 0 or not 0 <= FACE_MIN_CONFIDENCE <= 1:
        raise ValueError("Face dimensions must be positive and face confidence must be between zero and one")
    if BLOCKCHAIN_MODE not in {"local", "rpc"}:
        raise ValueError("BLOCKCHAIN_MODE must be either local or rpc")
