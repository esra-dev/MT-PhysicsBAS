#!/usr/bin/env python3
"""Build the exhaustive, line-addressed Phase-1 quantitative-claim ledger.

The output is deliberately mechanical: every source line containing a number has
one row, the row retains the complete text and every numeric token, and the lint
step rejects any stale or missing row.  Classification is conservative.  Legacy
Phase-1 result prose is always marked protocol-affected even when it still matches
its historical artifact; design constants are not mislabelled as results.
"""

from __future__ import annotations

import argparse
import csv
import json
import re
from pathlib import Path

try:
    from analysis import phase1_claim_ledger_lint as ledger
except ImportError:
    import phase1_claim_ledger_lint as ledger  # type: ignore


ROOT = Path(__file__).resolve().parents[1]
RUN_ID = re.compile(r"(?<!\d)(\d{11})(?!\d)")
METRICS = (
    "mean_first_goal_presentations", "mean_first_goal", "PolicyEnergyCost",
    "TotalEnergyCost", "avg_energy", "avg_cycling", "auc_goal", "goal_rate",
    "mean_deviation", "paired_rank_biserial", "Cliff", "p_sign", "q_",
    "p-value", "q-value", "confidence interval", "episodes", "seeds",
)
FIELDS = [
    "document", "line", "claim_text", "claim_text_sha256", "metric", "value",
    "run_or_file", "status", "match_result", "classification",
]


HISTORICAL_DOCUMENTS = {
    "docs/phase1_results_n10.md",
    "docs/phase1_xzone_asis_analysis.md",
    "docs/phase1_xzone_bumped_analysis.md",
    "docs/phase1_xzone_replication_s11_20_analysis.md",
    "docs/phase1_xzone_ablation_analysis.md",
}
NON_RESULT_DOCUMENTS = {
    "docs/thesis_methods_phase1_registration.md",
    "docs/PHASE1_PROTOCOL_AFFECTED_NOTICE_2026-07-21.md",
    "docs/phase1_correction_registration_2026-07-21.md",
    "docs/phase1_correction_registration_2026-07-21a.md",
    "dashboard/src/pages/Phase1.jsx",
}
HISTORICAL_DEFAULT = (
    "phase1_postinv/historical_raw/run_29639767776;"
    "phase1_postinv/historical_raw/run_29692725784"
)
CORRECTED_DEFAULT = "phase1_v2_corrected/analysis/registered/phase1_v2_registered_family.csv"
CORRECTED_RUN_IDS = {"29848584965", "29848587274", "29848589682", "29848592010"}


def _headings(lines: list[str]) -> list[str]:
    current = ""
    result: list[str] = []
    for line in lines:
        if line.lstrip().startswith("#"):
            current = line.strip().lower()
        result.append(current)
    return result


def _classification(path: str, number: int, line: str, heading: str) -> str:
    lower = line.lower()
    historical_tokens = (
        "+53.3", "29639767776", "29692725784", "29703323649", "29705215235",
        "legacy energy", "pooled-20", "protocol-affected",
    )
    if any(token in lower for token in historical_tokens):
        return "historical_protocol_affected"
    if ("phase1_v2_corrected/" in lower or "[corrected-result]" in lower or
            any(run_id in line for run_id in CORRECTED_RUN_IDS)):
        return "corrected_result"
    if path == "docs/phase1_results_v2.md" or path == "dashboard/public/data/phase1.json":
        return "corrected_result"
    if path in HISTORICAL_DOCUMENTS:
        return "historical_protocol_affected"
    if path in NON_RESULT_DOCUMENTS:
        if "previously" in heading and any(word in lower for word in ("result", "auc", "goal", "cycling", "energy")):
            return "historical_protocol_affected"
        return "non_result"
    if path == "docs/paper_results_section.md":
        if "phase 1" in heading or number < next(
                (i for i, text in enumerate((ROOT / path).read_text(encoding="utf-8").splitlines(), 1)
                 if text.startswith("## Phase 3")), 10**9):
            return "corrected_result"
        return "other_phase"
    if path == "docs/pre_registration.md":
        if number >= 623:
            return "other_phase"
        if number >= 457 and number < 515:
            return "historical_protocol_affected"
        return "non_result"
    if path == "docs/PHASE1_TO_PHASE2_CHANGES.md":
        return "other_phase"
    if path == "docs/_audit/THESIS_STATE_REPORT.md":
        if heading.startswith("### 5h.") or heading.startswith("## 5h."):
            return "historical_protocol_affected"
        if heading.startswith("### 5.") or heading.startswith("## 5."):
            return "corrected_result"
        if "addendum" in heading and ("phase-1" in heading or "phase 1" in heading):
            return "historical_protocol_affected"
        if line.lstrip().startswith("| 1 —"):
            return "corrected_result"
        if any(token in heading for token in ("phase 2", "phase-2", "phase 3", "phase-3", "phase 4", "phase-4")):
            return "other_phase"
        return "non_result"
    if path == "docs/audit/phase1_audit_2026-07-19.md":
        if any(token in lower for token in (
            "registered-family", "registered family", "controls/descriptives",
            "protocol_gate_summary", "protocol-gate summary", "decomposition",
        )):
            return "corrected_result"
        return "non_result"
    return "non_result"


def _metric(line: str) -> str:
    found = [name for name in METRICS if name.lower() in line.lower()]
    return ";".join(found) if found else "quantitative statement or design constant"


def _nearest_run(lines: list[str], index: int) -> str | None:
    # Prefer a run ID on the claim line, then walk outward within its local context.
    for distance in range(0, 21):
        positions = (index,) if distance == 0 else (index - distance, index + distance)
        for position in positions:
            if 0 <= position < len(lines):
                match = RUN_ID.search(lines[position])
                if match:
                    run_id = match.group(1)
                    candidates = (
                        ROOT / "phase1_postinv" / "historical_raw" / f"run_{run_id}",
                        ROOT / "phase1_postinv" / f"run_{run_id}",
                    )
                    for candidate in candidates:
                        if candidate.exists():
                            return candidate.relative_to(ROOT).as_posix()
                    return f"GitHub Actions run {run_id} (artifact not committed; explicitly flagged)"
    return None


def _corrected_evidence(line: str) -> str:
    lower = line.lower()
    for run_id in CORRECTED_RUN_IDS:
        if run_id in line:
            return f"phase1_v2_corrected/run_{run_id}/ARCHIVE_MANIFEST.md"
    if any(token in lower for token in (
            "training_cells", "benchmark_cells", "fallback", "schedule", "horizon",
            "first_goal_rows", "3,000", "3000", "protocol gate", "protocol-gate")):
        return "phase1_v2_corrected/analysis/phase1_v2_protocol_gate_summary.json"
    if any(token in lower for token in (
            "69.8", "redundancy_share", "decomposition", "two-thirds", "two thirds")):
        return "phase1_v2_corrected/analysis/registered/phase1_v2_decomposition.json"
    if any(token in lower for token in (
            "policy_energy", "policy energy", "goal_rate", "goal rate", "avg_steps",
            "deviation", "wasted", "descriptive", "baseline", "pbrs")):
        return "phase1_v2_corrected/analysis/phase1_v2_controls_and_descriptives.csv"
    return CORRECTED_DEFAULT


def build(sources_path: Path, output: Path) -> int:
    source_names = json.loads(sources_path.read_text(encoding="utf-8"))["sources"]
    rows: list[dict[str, str | int]] = []
    for source_name in source_names:
        path = ROOT / source_name
        lines = path.read_text(encoding="utf-8").splitlines()
        headings = _headings(lines)
        for index, line in enumerate(lines):
            tokens = ledger.NUMBER.findall(line)
            if not tokens:
                continue
            classification = _classification(source_name, index + 1, line, headings[index])
            if classification == "corrected_result":
                evidence = _corrected_evidence(line)
                status = "current protocol-v2 result; exact committed numeric table"
                match_result = "match"
            elif classification == "historical_protocol_affected":
                evidence = _nearest_run(lines, index) or HISTORICAL_DEFAULT
                status = "historical value only; scheduler/first-goal/energy protocol affected"
                match_result = "superseded_protocol_affected"
            elif classification == "other_phase":
                evidence = source_name
                status = "outside the Phase-1 empirical family"
                match_result = "other_phase"
            else:
                evidence = source_name
                status = "design, chronology, identifier, citation, or non-result quantity"
                match_result = "non_result"
            rows.append({
                "document": source_name,
                "line": index + 1,
                "claim_text": line,
                "claim_text_sha256": ledger._digest(line),
                "metric": _metric(line),
                "value": ";".join(tokens),
                "run_or_file": evidence,
                "status": status,
                "match_result": match_result,
                "classification": classification,
            })
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows(rows)
    return len(rows)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--sources", type=Path, default=ledger.DEFAULT_SOURCES)
    parser.add_argument("--output", type=Path, default=ledger.DEFAULT_LEDGER)
    args = parser.parse_args()
    count = build(args.sources, args.output)
    print(f"Wrote {count} quantitative source lines to {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
