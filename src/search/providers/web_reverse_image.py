"""Live reverse-image-search provider backed by SerpAPI's Google Lens (visual_matches) engine.

Unlike ``AuthorizedDatasetProvider`` (which only searches a local, curated
folder) this provider performs a genuine runtime search of the public web: it
temporarily hosts the query image, asks SerpAPI to find pages where a
visually similar image appears, downloads each candidate image, and
re-verifies it with our own ArcFace embedding before treating it as a match
candidate. Nothing here is hardcoded or pre-selected.
"""

import base64
import subprocess
import uuid
from pathlib import Path
from urllib.parse import urlparse

import numpy as np
import requests

from src.config import settings
from src.search.candidate_ranker import CandidatePost
from src.search.providers.base import SearchProvider


class WebSearchError(ValueError):
    """Raised when the live web search cannot be completed."""


def _github_token() -> str:
    if settings.GITHUB_TOKEN:
        return settings.GITHUB_TOKEN
    try:
        result = subprocess.run(
            ["gh", "auth", "token"], capture_output=True, text=True, timeout=10, check=True
        )
    except (OSError, subprocess.SubprocessError) as exc:
        raise WebSearchError(
            "No GITHUB_TOKEN configured and `gh auth token` is unavailable"
        ) from exc
    token = result.stdout.strip()
    if not token:
        raise WebSearchError("`gh auth token` returned an empty token")
    return token


def _host_image_publicly(image_path: Path) -> str:
    """Push the query image to a public GitHub repo so SerpAPI/Google can fetch it.

    Google's reverse-image-by-URL backends will only fetch images from
    domains they already trust and crawl; anonymous throwaway file hosts
    (tested: catbox.moe, litterbox) reliably return zero results even for
    images that DO have real matches elsewhere on the web. raw content on
    GitHub (raw.githubusercontent.com) is fetched successfully even seconds
    after upload, so this pushes the query image into a dedicated public
    repository (configured via GITHUB_HOST_OWNER/GITHUB_HOST_REPO) via the
    GitHub Contents API.

    Note: the pushed image becomes a public, world-readable file in that
    repository. It is not automatically deleted. Only use this with images
    you're comfortable being publicly hosted.
    """
    owner, repo, branch = settings.GITHUB_HOST_OWNER, settings.GITHUB_HOST_REPO, settings.GITHUB_HOST_BRANCH
    if not owner:
        raise WebSearchError("GITHUB_HOST_OWNER is not configured")
    token = _github_token()
    suffix = Path(image_path).suffix or ".jpg"
    remote_path = f"queries/{uuid.uuid4().hex}{suffix}"
    try:
        content_b64 = base64.b64encode(Path(image_path).read_bytes()).decode("ascii")
        response = requests.put(
            f"https://api.github.com/repos/{owner}/{repo}/contents/{remote_path}",
            headers={"Authorization": f"token {token}", "Accept": "application/vnd.github+json"},
            json={"message": "TraceChain AI search query image", "content": content_b64, "branch": branch},
            timeout=30,
        )
        response.raise_for_status()
        payload = response.json()
    except (OSError, requests.RequestException, ValueError) as exc:
        raise WebSearchError(f"Unable to publicly host the query image on GitHub: {exc}") from exc
    url = payload.get("content", {}).get("download_url")
    if not url:
        raise WebSearchError(f"GitHub upload did not return a usable URL: {payload!r}")
    return url


def _serpapi_reverse_image_search(image_url: str, api_key: str) -> list[dict]:
    # engine=google_reverse_image only exposes tiny (~90px) gstatic cache
    # thumbnails per result, too small for reliable face re-detection.
    # google_lens with type=visual_matches exposes the actual full-resolution
    # source image URL for each match, so that's used instead.
    try:
        response = requests.get(
            settings.SERPAPI_ENDPOINT,
            params={"engine": "google_lens", "url": image_url, "type": "visual_matches", "api_key": api_key},
            timeout=30,
        )
        response.raise_for_status()
        payload = response.json()
    except (requests.RequestException, ValueError) as exc:
        raise WebSearchError(f"SerpAPI reverse image search failed: {exc}") from exc
    if payload.get("error"):
        raise WebSearchError(f"SerpAPI reverse image search failed: {payload['error']}")
    return payload.get("visual_matches", []) or []


def _platform_from_url(url: str) -> str:
    try:
        host = urlparse(url).netloc.lower()
    except ValueError:
        return "unknown"
    return host[4:] if host.startswith("www.") else host or "unknown"


def _download_image(url: str, destination: Path) -> bool:
    try:
        response = requests.get(url, timeout=20, stream=True)
        response.raise_for_status()
        destination.write_bytes(response.content)
        return True
    except (OSError, requests.RequestException):
        return False


class WebReverseImageProvider(SearchProvider):
    """Search the live web via SerpAPI and re-verify hits with our own face model."""

    name = "web_reverse_image"

    def __init__(self, api_key: str | None = None, cache_dir: str | Path | None = None):
        self.api_key = api_key if api_key is not None else settings.SERPAPI_API_KEY
        self.cache_dir = Path(cache_dir) if cache_dir is not None else Path(settings.WEB_SEARCH_CACHE_DIR)

    def validate_source(self) -> None:
        if not self.api_key:
            raise WebSearchError("SERPAPI_API_KEY is not configured")
        if not settings.GITHUB_HOST_OWNER:
            raise WebSearchError("GITHUB_HOST_OWNER is not configured")

    def search(
        self, embedding: np.ndarray, top_k: int, image_path: str | Path | None = None
    ) -> list[CandidatePost]:
        from src.face.encoder import extract_embedding

        self.validate_source()
        if image_path is None:
            raise WebSearchError("WebReverseImageProvider requires the original image path to search the web")

        query_vector = np.asarray(embedding, dtype=np.float32).reshape(-1)
        query_vector = query_vector / (np.linalg.norm(query_vector) or 1.0)

        raw_results: list[dict] = []
        last_error: WebSearchError | None = None
        for _attempt in range(settings.WEB_SEARCH_MAX_ATTEMPTS):
            # A fresh upload path each attempt: Google's fetch-and-match step is
            # empirically flaky per-URL (a brand-new URL can succeed or come back
            # empty with no discernible reason), so retrying with a new URL gives
            # each attempt an independent chance rather than repeating a query
            # Google has already cached as empty.
            image_url = _host_image_publicly(Path(image_path))
            try:
                raw_results = _serpapi_reverse_image_search(image_url, self.api_key)
                break
            except WebSearchError as exc:
                last_error = exc
        else:
            if last_error is not None:
                raise last_error

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
