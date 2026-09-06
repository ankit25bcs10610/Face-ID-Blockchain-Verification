"""Re-verify an evidence file and demonstrate a real field modification."""

import argparse
import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.blockchain.verifier import demonstrate_tampering


def main() -> int:
    parser = argparse.ArgumentParser(description="Demonstrate TraceChain AI evidence tampering detection")
    parser.add_argument("--evidence", required=True, help="Evidence JSON file")
    parser.add_argument("--field", required=True, help="Existing evidence field to modify")
    parser.add_argument("--value", required=True, help="Replacement value for the selected field")
    args = parser.parse_args()
    try:
        evidence = json.loads(Path(args.evidence).read_text(encoding="utf-8"))
        result = demonstrate_tampering(evidence, args.field, args.value)
    except (OSError, json.JSONDecodeError, ValueError, RuntimeError) as exc:
        parser.error(str(exc))
    print(f"Original: {result['original']['status']}")
    print(f"Tampered field: {result['tampered']['field']}")
    print(f"Tampered: {result['tampered']['result']['status']}")
    print(f"Original hash: {result['original']['local_hash']}")
    print(f"Tampered hash: {result['tampered']['result']['local_hash']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
