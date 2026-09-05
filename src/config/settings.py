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
ALLOW_MULTIPLE_FACES = _env_bool("ALLOW_MULTIPLE_FACES", False)
POSTS_DIR = os.getenv("POSTS_DIR", "data/posts")
EMBEDDINGS_DIR = os.getenv("EMBEDDINGS_DIR", "data/embeddings")
FAISS_DIR = os.getenv("FAISS_DIR", "data/faiss")
INDEX_NAME = os.getenv("INDEX_NAME", "faces.index")
MANIFEST_NAME = os.getenv("MANIFEST_NAME", "manifest.json")
EMBEDDINGS_NAME = os.getenv("EMBEDDINGS_NAME", "embeddings.npy")
IMAGE_EXTENSIONS = tuple(
    extension.strip().lower()
    for extension in os.getenv("IMAGE_EXTENSIONS", ".jpg,.jpeg,.png").split(",")
    if extension.strip()
)
