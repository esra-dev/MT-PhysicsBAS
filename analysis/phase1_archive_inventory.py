#!/usr/bin/env python3
"""Create or verify a deterministic SHA-256 inventory for a Phase-1 archive."""

from __future__ import annotations

import argparse
import csv
import hashlib
from pathlib import Path


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def collect(root: Path, includes: list[str], output: Path) -> list[dict[str, object]]:
    root = root.resolve()
    excluded = output.resolve()
    files: set[Path] = set()
    for pattern in includes:
        for match in root.glob(pattern):
            if match.is_dir():
                files.update(path for path in match.rglob("*") if path.is_file())
            elif match.is_file():
                files.add(match)
    rows: list[dict[str, object]] = []
    for path in sorted(files, key=lambda item: item.relative_to(root).as_posix()):
        if path.resolve() == excluded:
            continue
        rows.append({
            "path": path.relative_to(root).as_posix(),
            "bytes": path.stat().st_size,
            "sha256": _sha256(path),
        })
    return rows


def write_inventory(root: Path, includes: list[str], output: Path) -> int:
    rows = collect(root, includes, output)
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=("path", "bytes", "sha256"))
        writer.writeheader()
        writer.writerows(rows)
    return len(rows)


def verify_inventory(root: Path, inventory: Path) -> list[str]:
    errors: list[str] = []
    with inventory.open(encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
    for row in rows:
        path = root / row["path"]
        if not path.is_file():
            errors.append(f"missing: {row['path']}")
            continue
        if path.stat().st_size != int(row["bytes"]):
            errors.append(f"size mismatch: {row['path']}")
        actual = _sha256(path)
        if actual != row["sha256"]:
            errors.append(f"SHA-256 mismatch: {row['path']}")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--out", type=Path)
    parser.add_argument("--include", action="append", default=[])
    parser.add_argument("--verify", type=Path)
    args = parser.parse_args()
    if args.verify:
        errors = verify_inventory(args.root, args.verify)
        if errors:
            for error in errors:
                print(error)
            return 1
        print(f"Verified {args.verify}")
        return 0
    if not args.out or not args.include:
        parser.error("creation requires --out and at least one --include")
    count = write_inventory(args.root, args.include, args.out)
    print(f"Wrote {count} SHA-256 rows to {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
