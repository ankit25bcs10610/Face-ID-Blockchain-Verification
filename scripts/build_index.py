"""Command-line entry point for building the authorized-content index."""

import argparse
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.search.index_builder import DatasetError, IndexBuildError, build_index


def main() -> int:
    parser = argparse.ArgumentParser(description="Build a FAISS index for authorized face posts")
    parser.add_argument("--posts-dir")
    parser.add_argument("--embeddings-dir")
    parser.add_argument("--faiss-dir")
    args = parser.parse_args()
    try:
        options = {key: value for key, value in {
            "posts_dir": args.posts_dir,
            "embeddings_dir": args.embeddings_dir,
            "faiss_dir": args.faiss_dir,
        }.items() if value is not None}
        result = build_index(**options)
    except (DatasetError, IndexBuildError) as exc:
        parser.error(str(exc))
    print(f"Indexed posts: {result.indexed_count}")
    print(f"Skipped posts: {result.skipped_count}")
    print(f"FAISS index: {result.index_path}")
    print(f"Embeddings: {result.embeddings_path}")
    print(f"Manifest: {result.manifest_path}")
    for error in result.errors:
        print(f"Warning: {error}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
