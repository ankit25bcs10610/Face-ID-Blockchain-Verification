"""InsightFace model loading and face detection."""

from dataclasses import dataclass
from pathlib import Path

import numpy as np

from src.config import settings
from src.face.quality import ImageQuality, validate_image


class FaceProcessingError(RuntimeError):
    """Base error for face model and detection failures."""


class NoFaceDetectedError(FaceProcessingError):
    """Raised when an image contains no detectable face."""


class MultipleFacesDetectedError(FaceProcessingError):
    """Raised when multiple faces are found but only one is allowed."""


@dataclass(frozen=True)
class DetectedFace:
    bounding_box: tuple[float, float, float, float]
    landmarks: np.ndarray | None
    detection_confidence: float
    quality: ImageQuality


_app = None


def get_face_app():
    global _app
    if _app is None:
        try:
            from insightface.app import FaceAnalysis

            _app = FaceAnalysis(name=settings.FACE_MODEL_NAME)
            _app.prepare(ctx_id=0, det_size=(settings.FACE_DET_SIZE, settings.FACE_DET_SIZE))
        except Exception as exc:
            raise FaceProcessingError(f"Unable to initialize InsightFace: {exc}") from exc
    return _app


def detect_faces(image: np.ndarray) -> list[DetectedFace]:
    from src.face.quality import check_quality

    quality = check_quality(image)
    try:
        faces = get_face_app().get(image)
    except FaceProcessingError:
        raise
    except Exception as exc:
        raise FaceProcessingError(f"InsightFace detection failed: {exc}") from exc

    detected = []
    for face in faces:
        box = np.asarray(face.bbox, dtype=float).reshape(-1)
        if box.size != 4:
            raise FaceProcessingError("InsightFace returned an invalid bounding box")
        landmarks = getattr(face, "kps", None)
        if landmarks is not None:
            landmarks = np.asarray(landmarks, dtype=np.float32)
        detected.append(DetectedFace(tuple(box.tolist()), landmarks, float(face.det_score), quality))
    return detected


def detect_face(image_path: str | Path) -> DetectedFace:
    image, _ = validate_image(image_path)
    faces = detect_faces(image)
    if not faces:
        raise NoFaceDetectedError("No face detected in image")
    if len(faces) > 1 and not settings.ALLOW_MULTIPLE_FACES:
        raise MultipleFacesDetectedError(f"Detected {len(faces)} faces; exactly one is required")
    return max(faces, key=lambda face: face.detection_confidence)
