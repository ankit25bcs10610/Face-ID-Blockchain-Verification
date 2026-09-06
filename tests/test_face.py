import cv2
import numpy as np
import pytest

from src.face import detector, encoder
from src.face.detector import MultipleFacesDetectedError, NoFaceDetectedError
from src.face.quality import ImageValidationError, check_quality, validate_image


def image_file(tmp_path, width=240, height=240):
    rng = np.random.default_rng(42)
    image = rng.integers(0, 256, (height, width, 3), dtype=np.uint8)
    path = tmp_path / "input.png"
    assert cv2.imwrite(str(path), image)
    return path, image


class FakeFace:
    def __init__(self, score=0.99, offset=0):
        self.bbox = np.array([20 + offset, 20, 200 + offset, 220], dtype=np.float32)
        self.kps = np.array(
            [[75 + offset, 90], [145 + offset, 90], [110 + offset, 125],
             [80 + offset, 165], [140 + offset, 165]], dtype=np.float32
        )
        self.det_score = score
        self.normed_embedding = np.ones(512, dtype=np.float32)


def test_validate_image_and_quality(tmp_path):
    path, image = image_file(tmp_path)
    loaded, quality = validate_image(path)
    assert loaded.shape == image.shape
    assert quality.width == 240
    assert 0 <= quality.quality_score <= 1


def test_invalid_and_small_images_are_rejected(tmp_path):
    missing = tmp_path / "missing.jpg"
    with pytest.raises(ImageValidationError):
        validate_image(missing)
    path, _ = image_file(tmp_path, 20, 20)
    with pytest.raises(ImageValidationError):
        validate_image(path)


def test_unsupported_image_extension_is_rejected(tmp_path):
    path = tmp_path / "input.txt"
    path.write_text("not an image", encoding="utf-8")
    with pytest.raises(ImageValidationError, match="Unsupported image format"):
        validate_image(path)


def test_detection_returns_landmarks_and_quality(tmp_path, monkeypatch):
    path, image = image_file(tmp_path)
    monkeypatch.setattr(detector, "get_face_app", lambda: type("App", (), {"get": lambda _, img: [FakeFace()]})())
    result = detector.detect_face(path)
    assert result.bounding_box == (20.0, 20.0, 200.0, 220.0)
    assert result.landmarks.shape == (5, 2)
    assert result.detection_confidence == pytest.approx(0.99)


def test_no_face_and_multiple_faces_are_rejected(tmp_path, monkeypatch):
    path, _ = image_file(tmp_path)
    monkeypatch.setattr(detector, "get_face_app", lambda: type("App", (), {"get": lambda _, img: []})())
    with pytest.raises(NoFaceDetectedError):
        detector.detect_face(path)
    monkeypatch.setattr(detector, "get_face_app", lambda: type("App", (), {"get": lambda _, img: [FakeFace(), FakeFace(offset=5)]})())
    with pytest.raises(MultipleFacesDetectedError):
        detector.detect_face(path)


def test_alignment_and_embedding_are_normalized(tmp_path, monkeypatch):
    path, image = image_file(tmp_path)
    fake_app = type("App", (), {"get": lambda _, img: [FakeFace()]})()
    monkeypatch.setattr(detector, "get_face_app", lambda: fake_app)
    monkeypatch.setattr(encoder, "get_face_app", lambda: fake_app)
    aligned = encoder.align_face(image, detector.detect_face(path))
    embedding = encoder.extract_embedding(path)
    assert aligned.shape == (112, 112, 3)
    assert embedding.shape == (512,)
    assert np.linalg.norm(embedding) == pytest.approx(1.0)
