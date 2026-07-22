#!/usr/bin/env python3
"""Build/lint the Phase-2/3/4 quantitative-claim ledgers.

Thin per-phase configuration over analysis/claim_ledger_common.py (the copied
Phase-1 machinery; the Phase-1 builder/lint stay byte-frozen). Classification
is conservative and mechanical:

  1. a line naming the phase's corrected campaign archive (or a corrected run
     ID, registered at archive time) is a corrected_result and must cite a
     committed file;
  2. a line carrying a withdrawn run ID / headline value / the
     "protocol-affected" marker is historical_protocol_affected;
  3. everything else is a non-result quantity (design, chronology, identifier).

Usage:
  python analysis/build_phase234_claim_ledgers.py --phase 2 [--lint] [--output PATH]
"""

from __future__ import annotations

import argparse
from pathlib import Path

try:
    from analysis import claim_ledger_common as common
except ImportError:  # executed as a script from the repo root
    import claim_ledger_common as common


PHASES = {
    "2": {
        "sources": Path("docs/audit/phase2_claim_sources.json"),
        "ledger": Path("docs/audit/phase2_claim_ledger.csv"),
        "corrected_prefix": "phase2_v2_corrected/",
        # Corrected run IDs are appended in the archive commit (Stage 5).
        "corrected_run_ids": ("29923594983", "29923609054", "29923621835",
                              "29923634620"),
        "historical_tokens": ("29148475671", "29151540231", "29155539633",
                              "29157197853", "29163456132", "29187088096",
                              "28590019536", "28745352239", "28913465680",
                              "-306.5", "-71.4", "-147.6", "+122.3", "+85.0",
                              "protocol-affected"),
        "historical_evidence": "phase2_postinv/;phase2_f2bdead/",
    },
    "3": {
        "sources": Path("docs/audit/phase3_claim_sources.json"),
        "ledger": Path("docs/audit/phase3_claim_ledger.csv"),
        "corrected_prefix": "phase3_v2_corrected/",
        "corrected_run_ids": (),
        "historical_tokens": ("27621106006", "29166356524", "protocol-affected"),
        "historical_evidence": "phase3_postinv/;phase3_download/",
    },
    "4": {
        "sources": Path("docs/audit/phase4_claim_sources.json"),
        "ledger": Path("docs/audit/phase4_claim_ledger.csv"),
        "corrected_prefix": "phase4_v2_corrected/",
        "corrected_run_ids": (),
        "historical_tokens": ("29193486193", "27905392725", "27903687624",
                              "protocol-affected"),
        "historical_evidence": "phase4_postinv/run_29193486193/",
    },
}


def _make_classifier(config):
    prefix = config["corrected_prefix"]
    run_ids = config["corrected_run_ids"]
    tokens = config["historical_tokens"]

    def classify(doc, lineno, line, heading):
        lower = line.lower()
        if prefix in line or any(run_id in line for run_id in run_ids):
            evidence = prefix + "CAMPAIGN_MANIFEST.md"
            for word in line.replace("`", " ").split():
                if word.startswith(prefix):
                    evidence = word.rstrip(".,;:)")
                    break
            # Dispatch-record run IDs are provenance identifiers, not results,
            # until the corrected archive exists.
            if not (common.ROOT / evidence).is_file():
                return ("non_result", doc,
                        "corrected-campaign identifier; archive pending",
                        "non_result")
            return ("corrected_result", evidence,
                    "current protocol-v2 result; committed archive", "match")
        if any(token in lower for token in (t.lower() for t in tokens)):
            return ("historical_protocol_affected", config["historical_evidence"],
                    "historical value only; protocol affected",
                    "superseded_protocol_affected")
        return ("non_result", doc,
                "design, chronology, identifier, citation, or non-result quantity",
                "non_result")

    return classify


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--phase", required=True, choices=sorted(PHASES))
    parser.add_argument("--lint", action="store_true")
    parser.add_argument("--output", type=Path, default=None)
    args = parser.parse_args()
    config = PHASES[args.phase]
    sources = common.ROOT / config["sources"]
    ledger = common.ROOT / config["ledger"]
    if args.lint:
        errors = common.lint(ledger, sources, config["corrected_prefix"])
        if errors:
            print("\n".join(errors))
            return 1
        print(f"Phase-{args.phase} claim ledger: OK")
        return 0
    output = args.output if args.output else ledger
    count = common.build(sources, output, _make_classifier(config))
    print(f"Wrote {count} quantitative source lines to {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
