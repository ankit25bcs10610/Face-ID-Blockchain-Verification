"""Face alignment and ArcFace embedding generation."""

from pathlib import Path

import cv2
import numpy as np

from src.face.detector import DetectedFace, FaceProcessingError, detect_face, get_face_app
from src.face.quality import validate_image


class EmbeddingError(FaceProcessingError):
    """Raised when alignment or embedding generation fails."""


def align_face(image: np.ndarray, face: DetectedFace, output_size: int = 112) -> np.ndarray:
    landmarks = face.landmarks
    if landmarks is None or landmarks.shape != (5, 2):
        raise EmbeddingError("Five facial landmarks are required for alignment")
    template = np.array(
        [[38.2946, 51.6963], [73.5318, 51.5014], [56.0252, 71.7366],
         [41.5493, 92.3655], [70.7299, 92.2041]], dtype=np.float32
    )
    if output_size != 112:
        template *= output_size / 112.0
    transform, _ = cv2.estimateAffinePartial2D(landmarks, template, method=cv2.LMEDS)
    if transform is None:
        raise EmbeddingError("Unable to estimate face alignment transform")
    return cv2.warpAffine(image, transform, (output_size, output_size), borderValue=0)


def extract_embedding(image_path: str | Path) -> np.ndarray:
    image, _ = validate_image(image_path)
    face = detect_face(image_path)
    aligned = align_face(image, face)
    try:
        faces = get_face_app().get(aligned)
        if not faces:
            raise EmbeddingError("No face detected after alignment")
        embedding = getattr(faces[0], "normed_embedding", None)
        if embedding is None:
            embedding = getattr(faces[0], "embedding", None)
    except EmbeddingError:
        raise
    except Exception as exc:
        raise EmbeddingError(f"InsightFace embedding generation failed: {exc}") from exc
    vector = np.asarray(embedding, dtype=np.float32).reshape(-1) if embedding is not None else None
    if vector is None or vector.size != 512 or not np.all(np.isfinite(vector)):
        raise EmbeddingError("InsightFace must return a finite 512-dimensional embedding")
    norm = float(np.linalg.norm(vector))
    if norm == 0:
        raise EmbeddingError("InsightFace returned a zero-length embedding")
    return vector / norm


def validate_face(image_path: str | Path) -> DetectedFace:
    return detect_face(image_path)
