"""Live reverse-image-search provider backed by SerpAPI's Google Lens engine.

Unlike ``AuthorizedDatasetProvider`` (which only searches a local, curated
folder) this provider performs a genuine runtime search of the public web: it
uploads the query image to SerpAPI, asks Google Lens for pages where a
visually similar image appears, downloads each candidate image, and
re-verifies it with our own ArcFace embedding before treating it as a match
candidate. Nothing here is hardcoded or pre-selected.

The query image is sent only to SerpAPI (which discards it after ten
minutes); it is never published to a public URL of our own.
"""

import io
import time
import uuid
from pathlib import Path
from urllib.parse import urlparse

import numpy as np
import requests

from src.config import settings
from src.search.candidate_ranker import CandidatePost
from src.search.providers.base import SearchProvider

# SerpApi's image upload endpoint rejects anything larger than 500 KB.
_UPLOAD_LIMIT_BYTES = 500 * 1024


class WebSearchError(ValueError):
    """Raised when the live web search cannot be completed."""


def _prepare_upload_bytes(image_path: Path) -> bytes:
    """Return image bytes that fit inside SerpApi's upload size limit.

    Only the reverse-image lookup uses this copy. Face matching still runs on
    the original file, so downscaling here does not affect match accuracy.
    """
    raw = image_path.read_bytes()
    if len(raw) <= _UPLOAD_LIMIT_BYTES:
        return raw
    try:
        from PIL import Image

        image = Image.open(io.BytesIO(raw))
        image = image.convert("RGB")
        for max_edge, quality in ((1600, 85), (1280, 80), (1024, 75), (800, 70)):
            resized = image.copy()
            resized.thumbnail((max_edge, max_edge))
            buffer = io.BytesIO()
            resized.save(buffer, format="JPEG", quality=quality, optimize=True)
            if buffer.tell() <= _UPLOAD_LIMIT_BYTES:
                return buffer.getvalue()
    except Exception as exc:
        raise WebSearchError(f"Unable to prepare the query image for upload: {exc}") from exc
    raise WebSearchError("The query image could not be compressed below SerpApi's 500 KB upload limit")


def _upload_to_serpapi(image_path: Path, api_key: str) -> str:
    """Upload the query image to SerpApi and return its short-lived image id."""
    payload = _prepare_upload_bytes(Path(image_path))
    try:
        response = requests.post(
            settings.SERPAPI_UPLOAD_ENDPOINT,
            files={"image": (Path(image_path).name, payload)},
            data={"api_key": api_key},
            timeout=45,
        )
        response.raise_for_status()
        body = response.json()
    except (requests.RequestException, ValueError) as exc:
        raise WebSearchError(f"Unable to upload the query image to SerpApi: {exc}") from exc
    image_id = body.get("image_id")
    if not image_id:
        raise WebSearchError(f"SerpApi upload did not return an image id: {body!r}")
    return str(image_id)


def _serpapi_visual_matches(image_id: str, api_key: str) -> list[dict]:
    """Return Google Lens visual matches for an uploaded image id."""
    try:
        response = requests.get(
            settings.SERPAPI_ENDPOINT,
            params={
                "engine": "google_lens",
                "image_id": image_id,
                "type": "visual_matches",
                "api_key": api_key,
            },
            timeout=45,
        )
        response.raise_for_status()
        payload = response.json()
    except (requests.RequestException, ValueError) as exc:
        raise WebSearchError(f"SerpApi reverse image search failed: {exc}") from exc
    error = payload.get("error")
    if error:
        # "hasn't returned any results" is a legitimate empty result, not a
        # service failure: the query image simply has no visual match on the
        # public web. Every other error is a real failure.
        if "hasn't returned any results" in error:
            return []
        raise WebSearchError(f"SerpApi reverse image search failed: {error}")
    return payload.get("visual_matches", []) or []


def _platform_from_url(url: str) -> str:
    try:
        host = urlparse(url).netloc.lower()
    except ValueError:
        return "unknown"
    return host[4:] if host.startswith("www.") else host or "unknown"


def _download_image(url: str, destination: Path) -> bool:
    try:
        response = requests.get(url, timeout=20)
        response.raise_for_status()
        destination.write_bytes(response.content)
        return True
    except (OSError, requests.RequestException):
        return False


class WebReverseImageProvider(SearchProvider):
    """Search the live web via SerpApi and re-verify hits with our own face model."""

    name = "web_reverse_image"

    def __init__(self, api_key: str | None = None, cache_dir: str | Path | None = None):
        self.api_key = api_key if api_key is not None else settings.SERPAPI_API_KEY
        self.cache_dir = Path(cache_dir) if cache_dir is not None else Path(settings.WEB_SEARCH_CACHE_DIR)

    def validate_source(self) -> None:
        if not self.api_key:
            raise WebSearchError("SERPAPI_API_KEY is not configured")

    def _discover(self, image_path: Path) -> list[dict]:
        """Upload and search, retrying transient failures and empty responses."""
        last_error: WebSearchError | None = None
        for attempt in range(settings.WEB_SEARCH_MAX_ATTEMPTS):
            if attempt:
                time.sleep(1.5 * attempt)
            try:
                image_id = _upload_to_serpapi(image_path, self.api_key)
                results = _serpapi_visual_matches(image_id, self.api_key)
            except WebSearchError as exc:
                last_error = exc
                continue
            if results:
                return results
        if last_error is not None:
            raise last_error
        return []

    def search(
        self, embedding: np.ndarray, top_k: int, image_path: str | Path | None = None
    ) -> list[CandidatePost]:
        from src.face.encoder import extract_embedding

        self.validate_source()
        if image_path is None:
            raise WebSearchError("WebReverseImageProvider requires the original image path to search the web")

        query_vector = np.asarray(embedding, dtype=np.float32).reshape(-1)
        query_vector = query_vector / (np.linalg.norm(query_vector) or 1.0)

        raw_results = self._discover(Path(image_path))

        self.cache_dir.mkdir(parents=True, exist_ok=True)
        search_batch = uuid.uuid4().hex[:8]

        candidates: list[CandidatePost] = []
        scanned = 0
        for position, result in enumerate(raw_results):
            if scanned >= settings.WEB_SEARCH_MAX_CANDIDATES_SCANNED or len(candidates) >= top_k:
                break
            candidate_image_url = result.get("image") or result.get("thumbnail")
            link = result.get("link") or candidate_image_url
            if not candidate_image_url or not link:
                continue
            scanned += 1
            local_path = self.cache_dir / f"{search_batch}-{position}.jpg"
            if not _download_image(candidate_image_url, local_path):
                continue
            try:
                candidate_embedding = extract_embedding(local_path)
            except Exception:
                local_path.unlink(missing_ok=True)
                continue
            similarity = float(np.dot(query_vector, candidate_embedding))
            candidates.append(
                CandidatePost(
                    post_id=link,
                    similarity_score=similarity,
                    image_path=str(local_path),
                    metadata={
                        "platform": _platform_from_url(link),
                        "post_url": link,
                        "title": result.get("title", ""),
                        "source": result.get("source", ""),
                        "search_provider": "serpapi_google_lens_visual_matches",
                    },
                )
            )
        candidates.sort(key=lambda item: item.similarity_score, reverse=True)
        return candidates[:top_k]

    def fetch_candidates(self) -> list[CandidatePost]:
        raise WebSearchError(
            "WebReverseImageProvider has no static catalog to enumerate; call search() with a query image"
        )

    def fetch_metadata(self, post_id: str) -> dict:
        raise WebSearchError(
            "WebReverseImageProvider does not persist a lookup table; metadata is only available from search() results"
        )
