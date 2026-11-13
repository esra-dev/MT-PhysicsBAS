#!/usr/bin/env python3
"""Which `elem:` terms used by this project are declared in the published Elementary ontology?

The project writes Elementary terms under the prefix `elem:`. This script
lists every `elem:` local name used in the knowledge-graph files
(src/resources/*.ttl) and in the reasoner sources (src/env/tools/*.java) and
checks each against a downloaded copy of the published ontology file

    https://github.com/autonomous-buildings/elementary
    core-ontology/elementary.owl.ttl

The ontology file is read as plain text; nothing in it is executed and it is
not vendored into this repository. The CSV records its SHA-256 so the
comparison can be repeated against the same bytes.

    python analysis/elementary_term_conformance.py --ontology <elementary.owl.ttl> \
        [--ontology-commit <sha>] [--out docs/audit/elementary_term_conformance.csv]
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import re
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TERM = re.compile(r"\belem:([A-Za-z_]\w*)")
PREFIX = re.compile(r"@prefix\s+elem:\s*<([^>]+)>")
DECLARATION = re.compile(r"^:([A-Za-z_][\w\-]*)\s+rdf:type\s+([^;.\n]+)", re.M)
BASE = re.compile(r"^@prefix\s+:\s*<([^>]+)>", re.M)


def _count(paths: list[Path]) -> Counter[str]:
    counts: Counter[str] = Counter()
    for path in paths:
        counts.update(TERM.findall(path.read_text(encoding="utf-8", errors="replace")))
    return counts


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--ontology", type=Path, required=True)
    parser.add_argument("--ontology-commit", default="")
    parser.add_argument("--out", type=Path,
                        default=ROOT / "docs" / "audit" / "elementary_term_conformance.csv")
    args = parser.parse_args()

    raw = args.ontology.read_bytes()
    text = raw.decode("utf-8", errors="replace")
    declared = {name: kind.strip().rstrip(" ,") for name, kind in DECLARATION.findall(text)}
    by_lower = {name.lower(): name for name in declared}
    published_ns = (BASE.search(text) or [None, ""])[1]

    ttl_files = sorted((ROOT / "src" / "resources").glob("*.ttl"))
    java_files = sorted((ROOT / "src" / "env" / "tools").glob("*.java"))
    in_kg, in_code = _count(ttl_files), _count(java_files)
    project_ns = sorted({ns for path in ttl_files
                         for ns in PREFIX.findall(path.read_text(encoding="utf-8", errors="replace"))})

    rows = []
    for name in sorted(set(in_kg) | set(in_code)):
        if name in declared:
            status, published = "declared_in_published_file", declared[name]
        elif name.lower() in by_lower:
            status, published = "spelling_differs", by_lower[name.lower()]
        else:
            status, published = "not_in_published_file", ""
        rows.append({"elem_local_name": name, "uses_in_kg_files": in_kg.get(name, 0),
                     "uses_in_reasoner_sources": in_code.get(name, 0), "status": status,
                     "published_type_or_spelling": published})

    args.out.parent.mkdir(parents=True, exist_ok=True)
    with args.out.open("w", encoding="utf-8", newline="") as handle:
        handle.write(f"# published ontology: core-ontology/elementary.owl.ttl of "
                     f"github.com/autonomous-buildings/elementary, commit {args.ontology_commit or 'unknown'}\n")
        handle.write(f"# published file sha256: {hashlib.sha256(raw).hexdigest()}\n")
        handle.write(f"# published namespace: {published_ns}\n")
        handle.write(f"# project namespace(s) for elem: {'; '.join(project_ns)}\n")
        handle.write(f"# namespaces identical: {project_ns == [published_ns]}\n")
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()), lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)

    tally = Counter(row["status"] for row in rows)
    print(f"{len(rows)} elem: terms used; {dict(sorted(tally.items()))}")
    print(f"published namespace {published_ns} | project namespace(s) {project_ns}")
    print("not in the published file:",
          ", ".join(r["elem_local_name"] for r in rows if r["status"] != "declared_in_published_file"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
