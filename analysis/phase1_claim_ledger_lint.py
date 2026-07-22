#!/usr/bin/env python3
"""Fail CI when a quantitative Phase-1 source line is absent from the ledger."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_LEDGER = ROOT / "docs" / "audit" / "phase1_claim_ledger.csv"
DEFAULT_SOURCES = ROOT / "docs" / "audit" / "phase1_claim_sources.json"
NUMBER = re.compile(r"(?<![A-Za-z_])[-+]?\d+(?:\.\d+)?(?:[eE][-+]?\d+)?")
TAGS = ("[VERIFIED]", "[STATED]", "[INFERRED]")
SOURCE_HINT = re.compile(
    r"(?:Evidence|Source|Sources?):|"
    r"(?:[A-Za-z0-9_.\\/\-]+\.(?:java|asl|py|json|ttl|ya?ml|md|csv|ps1|jsx))"
    r"(?::\d|#|\s§|`)|"
    r"(?:GitHub Actions )?run\s+`?\d{11}`?|"
    r"docs?\. section|registration §",
    re.IGNORECASE,
)
BACKTICK_LINE_REF = re.compile(
    r"`(?P<path>[A-Za-z0-9_./*\\\-]+\.(?:java|asl|py|json|ttl|ya?ml|md|csv|ps1|jsx))"
    r":(?P<lines>\d+(?:-\d+)?(?:,\d+(?:-\d+)?)*)`"
)
REQUIRED = {
    "document", "line", "claim_text", "claim_text_sha256", "metric", "value", "run_or_file",
    "status", "match_result", "classification",
}
CLASSIFICATIONS = {
    "corrected_result",
    "historical_protocol_affected",
    "non_result",
    "other_phase",
}
MATCH_RESULTS = {
    "match",
    "superseded_protocol_affected",
    "non_result",
    "other_phase",
}


def _normalise(path: Path) -> str:
    return path.resolve().relative_to(ROOT).as_posix()


def _digest(line: str) -> str:
    return hashlib.sha256(line.encode("utf-8")).hexdigest()


def quantitative_lines(source_paths: list[Path]) -> dict[tuple[str, int], tuple[str, list[str]]]:
    found: dict[tuple[str, int], tuple[str, list[str]]] = {}
    for path in source_paths:
        if not path.is_file():
            raise ValueError(f"Claim-ledger source is missing: {_normalise(path)}")
        for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
            tokens = NUMBER.findall(line)
            if tokens:
                found[(_normalise(path), number)] = (line, tokens)
    return found


def _audit_paragraph_errors(path: Path) -> list[str]:
    """Require a provenance tag and source on every factual block/table/list row."""
    errors: list[str] = []
    lines = path.read_text(encoding="utf-8").splitlines()
    table_headers = {
        number for number in range(1, len(lines))
        if lines[number - 1].strip().startswith("|")
        and lines[number].strip().startswith("|---")
    }
    in_fence = False
    paragraph_start = True
    block_start = 0
    block: list[str] = []

    def finish_block() -> None:
        nonlocal block, block_start
        if block and not SOURCE_HINT.search(" ".join(block)):
            errors.append(
                f"{_normalise(path)}:{block_start}: factual block lacks a source pointer"
            )
        block = []
        block_start = 0

    for number, raw in enumerate(lines, 1):
        stripped = raw.strip()
        if stripped.startswith("```"):
            finish_block()
            in_fence = not in_fence
            paragraph_start = True
            continue
        if in_fence or not stripped:
            if not in_fence:
                finish_block()
            paragraph_start = True
            continue
        if stripped.startswith("#"):
            finish_block()
            paragraph_start = True
            continue
        if number in table_headers:
            finish_block()
            paragraph_start = True
            continue
        if stripped.startswith("|---") or set(stripped) <= {"|", "-", ":", " "}:
            finish_block()
            paragraph_start = True
            continue
        is_row = stripped.startswith("|") or re.match(r"^(?:[-*]|\d+\.)\s+", stripped)
        if paragraph_start or is_row:
            finish_block()
            candidate = stripped
            candidate = re.sub(r"^(?:>|[-*]|\d+\.)\s*", "", candidate)
            if candidate.startswith("|"):
                candidate = candidate[1:].lstrip()
            if not candidate.startswith(TAGS):
                errors.append(f"{_normalise(path)}:{number}: factual block lacks provenance tag")
            block_start = number
            block = [stripped]
        else:
            block.append(stripped)
        paragraph_start = False
    finish_block()
    return errors


def _audit_source_reference_errors(path: Path) -> list[str]:
    """Reject broken or out-of-range path:line citations in the audit."""
    errors: list[str] = []
    for audit_line, text in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        for match in BACKTICK_LINE_REF.finditer(text):
            source = match.group("path").replace("\\", "/")
            candidates = list(ROOT.glob(source)) if "*" in source else [ROOT / source]
            if not candidates or any(not candidate.is_file() for candidate in candidates):
                errors.append(
                    f"{_normalise(path)}:{audit_line}: source citation does not exist: {source}"
                )
                continue
            cited = [int(value) for value in re.findall(r"\d+", match.group("lines"))]
            for candidate in candidates:
                line_count = len(candidate.read_text(encoding="utf-8").splitlines())
                if max(cited) > line_count:
                    errors.append(
                        f"{_normalise(path)}:{audit_line}: source line exceeds {line_count}: "
                        f"{_normalise(candidate)}:{match.group('lines')}"
                    )
    return errors


def lint(ledger_path: Path, sources_path: Path, audit_path: Path | None = None) -> list[str]:
    errors: list[str] = []
    source_names = json.loads(sources_path.read_text(encoding="utf-8"))["sources"]
    source_paths = [ROOT / name for name in source_names]
    expected = quantitative_lines(source_paths)

    with ledger_path.open(encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        if not reader.fieldnames or not REQUIRED.issubset(reader.fieldnames):
            missing = sorted(REQUIRED - set(reader.fieldnames or []))
            return [f"Ledger is missing required columns: {missing}"]
        rows = list(reader)

    seen: dict[tuple[str, int], dict[str, str]] = {}
    for row_number, row in enumerate(rows, 2):
        try:
            key = (row["document"], int(row["line"]))
        except (TypeError, ValueError):
            errors.append(f"ledger row {row_number}: invalid document/line")
            continue
        if key in seen:
            errors.append(f"ledger row {row_number}: duplicate key {key[0]}:{key[1]}")
        seen[key] = row
        if key not in expected:
            errors.append(f"ledger row {row_number}: no quantitative source line at {key[0]}:{key[1]}")
            continue
        line, tokens = expected[key]
        if row["claim_text"] != line:
            errors.append(f"ledger row {row_number}: claim text differs for {key[0]}:{key[1]}")
        if row["claim_text_sha256"] != _digest(line):
            errors.append(f"ledger row {row_number}: stale source digest for {key[0]}:{key[1]}")
        ledger_tokens = [token for token in row["value"].split(";") if token]
        if ledger_tokens != tokens:
            errors.append(f"ledger row {row_number}: value tokens differ for {key[0]}:{key[1]}")
        for field in REQUIRED - {"document", "line", "claim_text_sha256", "value"}:
            if not row[field].strip():
                errors.append(f"ledger row {row_number}: empty {field}")
        if row["classification"] not in CLASSIFICATIONS:
            errors.append(f"ledger row {row_number}: invalid classification {row['classification']!r}")
        if row["match_result"] not in MATCH_RESULTS:
            errors.append(f"ledger row {row_number}: invalid match_result {row['match_result']!r}")
        if row["classification"] == "corrected_result":
            if row["match_result"] != "match" or "phase1_v2_corrected/" not in row["run_or_file"]:
                errors.append(f"ledger row {row_number}: corrected result lacks committed archive match")
            elif not (ROOT / row["run_or_file"]).is_file():
                errors.append(f"ledger row {row_number}: corrected source file is missing")
            if re.search(r"(?:\b[qp]\b|\"[qp]\")\s*(?:=|:)\s*0(?:\.0+)?(?![\d.])",
                         row["claim_text"], re.IGNORECASE):
                errors.append(f"ledger row {row_number}: corrected result reports p/q as zero")

    for key in sorted(set(expected) - set(seen)):
        errors.append(f"unledgered quantitative line: {key[0]}:{key[1]}")

    if audit_path is not None:
        errors.extend(_audit_paragraph_errors(audit_path))
        errors.extend(_audit_source_reference_errors(audit_path))
    return errors


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--ledger", type=Path, default=DEFAULT_LEDGER)
    parser.add_argument("--sources", type=Path, default=DEFAULT_SOURCES)
    parser.add_argument("--audit", type=Path,
                        default=ROOT / "docs" / "audit" / "phase1_audit_2026-07-19.md")
    args = parser.parse_args()
    errors = lint(args.ledger, args.sources, args.audit)
    if errors:
        print("\n".join(errors))
        return 1
    print("Phase-1 claim ledger and audit provenance tags: OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
