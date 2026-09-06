"""Image validation and quality checks used before face processing."""

from dataclasses import dataclass
from pathlib import Path

import cv2
import numpy as np

from src.config import settings


class ImageValidationError(ValueError):
    """Raised when an input image cannot be processed."""


@dataclass(frozen=True)
class ImageQuality:
    width: int
    height: int
    brightness: float
    sharpness: float
    quality_score: float


def load_image(image_path: str | Path) -> np.ndarray:
    path = Path(image_path)
    if not path.is_file():
        raise ImageValidationError(f"Image does not exist: {path}")
    if path.suffix.lower() not in settings.IMAGE_EXTENSIONS:
        raise ImageValidationError(
            f"Unsupported image format: {path.suffix or '<none>'}. "
            f"Supported formats: {', '.join(settings.IMAGE_EXTENSIONS)}"
        )
    image = cv2.imread(str(path), cv2.IMREAD_COLOR)
    if image is None:
        raise ImageValidationError(f"Unable to decode image: {path}")
    return image


def check_quality(image: np.ndarray) -> ImageQuality:
    if image is None or not isinstance(image, np.ndarray) or image.size == 0:
        raise ImageValidationError("Image data is empty or invalid")
    if image.ndim != 3 or image.shape[2] != 3:
        raise ImageValidationError("Image must be a color image with three channels")

    height, width = image.shape[:2]
    if width < settings.FACE_MIN_WIDTH or height < settings.FACE_MIN_HEIGHT:
        raise ImageValidationError(
            f"Image resolution {width}x{height} is below the configured minimum "
            f"{settings.FACE_MIN_WIDTH}x{settings.FACE_MIN_HEIGHT}"
        )

    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    brightness = float(np.mean(gray))
    sharpness = float(cv2.Laplacian(gray, cv2.CV_64F).var())
    # A bounded diagnostic score, not a face-recognition confidence value.
    brightness_score = 1.0 - abs(brightness - 127.5) / 127.5
    sharpness_score = sharpness / (sharpness + 100.0)
    quality_score = max(0.0, min(1.0, 0.5 * brightness_score + 0.5 * sharpness_score))
    if quality_score < settings.FACE_MIN_QUALITY:
        raise ImageValidationError(
            f"Image quality score {quality_score:.3f} is below the configured minimum"
        )
    return ImageQuality(width, height, brightness, sharpness, quality_score)


def validate_image(image_path: str | Path) -> tuple[np.ndarray, ImageQuality]:
    image = load_image(image_path)
    return image, check_quality(image)
