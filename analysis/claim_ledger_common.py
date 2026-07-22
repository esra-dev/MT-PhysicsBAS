#!/usr/bin/env python3
"""Shared claim-ledger machinery for the corrected Phase-2/3/4 documents.

A deliberate COPY of the Phase-1 ledger pattern
(analysis/build_phase1_claim_ledger.py + analysis/phase1_claim_ledger_lint.py).
Copied, not imported or refactored: the Phase-1 builder and lint stay
byte-frozen so the committed Phase-1 ledger keeps rebuilding byte-identically.

Contract (identical to Phase 1): every source line containing a number gets
exactly one ledger row carrying the verbatim text, a SHA-256 digest, the
numeric tokens, an evidence pointer, and a classification. The lint fails on
any missing, stale, duplicated, or unledgered line, and requires every
corrected-result row to cite an existing committed file under the campaign
archive prefix. A shared document may appear in several phases' manifests;
each phase adjudicates its own lines and marks the rest `other_phase`.
"""

from __future__ import annotations

import csv
import hashlib
import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
NUMBER = re.compile(r"(?<![A-Za-z_])[-+]?\d+(?:\.\d+)?(?:[eE][-+]?\d+)?")
FIELDS = [
    "document", "line", "claim_text", "claim_text_sha256", "metric", "value",
    "run_or_file", "status", "match_result", "classification",
]
CLASSIFICATIONS = {"corrected_result", "historical_protocol_affected",
                   "non_result", "other_phase"}
MATCH_RESULTS = {"match", "superseded_protocol_affected", "non_result", "other_phase"}


def digest(line: str) -> str:
    return hashlib.sha256(line.encode("utf-8")).hexdigest()


def quantitative_lines(source_names: list[str]) -> dict[tuple[str, int], tuple[str, list[str]]]:
    found: dict[tuple[str, int], tuple[str, list[str]]] = {}
    for name in source_names:
        path = ROOT / name
        if not path.is_file():
            raise ValueError(f"Claim-ledger source is missing: {name}")
        for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
            tokens = NUMBER.findall(line)
            if tokens:
                found[(name, number)] = (line, tokens)
    return found


def headings(lines: list[str]) -> list[str]:
    current = ""
    result: list[str] = []
    for line in lines:
        if line.lstrip().startswith("#"):
            current = line.strip().lower()
        result.append(current)
    return result


def build(sources_path: Path, output: Path, classify) -> int:
    """classify(doc, lineno, line, heading) -> (classification, evidence, status, match_result)."""
    source_names = json.loads(sources_path.read_text(encoding="utf-8"))["sources"]
    rows: list[dict[str, str | int]] = []
    for name in source_names:
        lines = (ROOT / name).read_text(encoding="utf-8").splitlines()
        line_headings = headings(lines)
        for index, line in enumerate(lines):
            tokens = NUMBER.findall(line)
            if not tokens:
                continue
            classification, evidence, status, match_result = classify(
                name, index + 1, line, line_headings[index])
            rows.append({
                "document": name,
                "line": index + 1,
                "claim_text": line,
                "claim_text_sha256": digest(line),
                "metric": "quantitative statement or design constant",
                "value": ";".join(tokens),
                "run_or_file": evidence,
                "status": status,
                "match_result": match_result,
                "classification": classification,
            })
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDS, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)
    return len(rows)


def lint(ledger_path: Path, sources_path: Path, corrected_prefix: str) -> list[str]:
    errors: list[str] = []
    source_names = json.loads(sources_path.read_text(encoding="utf-8"))["sources"]
    expected = quantitative_lines(source_names)

    with ledger_path.open(encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        if not reader.fieldnames or not set(FIELDS).issubset(reader.fieldnames):
            missing = sorted(set(FIELDS) - set(reader.fieldnames or []))
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
        if row["claim_text_sha256"] != digest(line):
            errors.append(f"ledger row {row_number}: stale source digest for {key[0]}:{key[1]}")
        ledger_tokens = [token for token in row["value"].split(";") if token]
        if ledger_tokens != tokens:
            errors.append(f"ledger row {row_number}: value tokens differ for {key[0]}:{key[1]}")
        if row["classification"] not in CLASSIFICATIONS:
            errors.append(f"ledger row {row_number}: invalid classification {row['classification']!r}")
        if row["match_result"] not in MATCH_RESULTS:
            errors.append(f"ledger row {row_number}: invalid match_result {row['match_result']!r}")
        if row["classification"] == "corrected_result":
            if row["match_result"] != "match" or corrected_prefix not in row["run_or_file"]:
                errors.append(f"ledger row {row_number}: corrected result lacks committed archive match")
            elif not (ROOT / row["run_or_file"]).is_file():
                errors.append(f"ledger row {row_number}: corrected source file is missing")
            if re.search(r"(?:\b[qp]\b|\"[qp]\")\s*(?:=|:)\s*0(?:\.0+)?(?![\d.])",
                         row["claim_text"], re.IGNORECASE):
                errors.append(f"ledger row {row_number}: corrected result reports p/q as zero")

    for key in sorted(set(expected) - set(seen)):
        errors.append(f"unledgered quantitative line: {key[0]}:{key[1]}")
    return errors
