#!/usr/bin/env python3
"""Write stable Phase-1 workflow-dispatch provenance into the consolidated artifact."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", required=True)
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--sha", required=True)
    parser.add_argument("--ref", required=True)
    parser.add_argument("--run-mode", required=True)
    parser.add_argument("--profiles", required=True)
    parser.add_argument("--seeds", required=True)
    parser.add_argument("--publish-results", required=True)
    # Phase-2 structure-only campaign (2026-11-14): the adapt-step KG layer.
    # Optional and omitted from the payload when not passed, so the Phase-1 and
    # Phase-4 workflows (which do not use it) keep their payload shape.
    parser.add_argument("--knowledge-layer", default=None)
    args = parser.parse_args()
    payload = {
        "workflow": ".github/workflows/phase1.yml",
        "run_id": int(args.run_id),
        "head_sha": args.sha,
        "ref": args.ref,
        "run_mode": args.run_mode,
        "profiles": [value.strip() for value in args.profiles.split(",") if value.strip()],
        "seeds": [int(value) for value in args.seeds.split(",") if value.strip()],
        "publish_results": args.publish_results.strip().lower() == "true",
    }
    if args.knowledge_layer is not None:
        payload["knowledge_layer"] = args.knowledge_layer.strip().lower()
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
