#!/usr/bin/env python3
"""Rebuild and byte-verify the frozen Phase-2b Q-gap retrospective.

Every input path is explicit.  The analysis is rebuilt in a fresh temporary
directory, its complete canonical output set is checked independently, and
all files are compared byte-for-byte with the committed result directory.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import re
import subprocess
import tempfile
from pathlib import Path
from typing import Callable, Sequence


FREEZE_COMMIT = "d75cdc836ee7d5dbac02b2497144a7933de99623"
INVENTORY_NAME = "SHA256SUMS.csv"
CANONICAL_OUTPUTS = (
    "source_manifest.json",
    "qgap_scenario_rows.csv",
    "qgap_seed_rows.csv",
    "qgap_cell_summary.csv",
    "detector_opportunity_rows.csv",
    "ordering_assessment.csv",
    "qgap_vs_recovery.png",
    "detectability_audit.png",
    "PHASE2_QGAP_RETROSPECTIVE_RESULTS.md",
    INVENTORY_NAME,
)
INVENTORY_COLUMNS = ("path", "bytes", "sha256")
SHA256_TEXT = re.compile(r"[0-9a-f]{64}")
IMPLEMENTATION_PATHS = (
    "analysis/phase2_qgap_retrospective.py",
    "analysis/phase2_qgap_core.py",
    "analysis/validate_phase2_qgap_inputs.py",
    "analysis/phase2_qgap_spec.json",
    "analysis/reproduce_phase2_qgap.py",
)

Runner = Callable[..., object]


class ReproductionError(ValueError):
    """The committed result cannot be reproduced under the frozen contract."""


def _resolve_directory(path: Path, label: str) -> Path:
    try:
        resolved = path.resolve(strict=True)
    except FileNotFoundError as exc:
        raise FileNotFoundError(f"{label} does not exist: {path}") from exc
    if not resolved.is_dir():
        raise NotADirectoryError(f"{label} is not a directory: {resolved}")
    return resolved


def _resolve_file(path: Path, label: str) -> Path:
    try:
        resolved = path.resolve(strict=True)
    except FileNotFoundError as exc:
        raise FileNotFoundError(f"{label} does not exist: {path}") from exc
    if not resolved.is_file():
        raise FileNotFoundError(f"{label} is not a regular file: {resolved}")
    return resolved


def _resolve_commit(repo_root: Path, revision: str) -> str:
    command = [
        "git",
        "-C",
        str(repo_root),
        "rev-parse",
        "--verify",
        f"{revision}^{{commit}}",
    ]
    result = subprocess.run(
        command,
        check=False,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    if result.returncode != 0:
        detail = result.stderr.strip() or result.stdout.strip()
        raise ReproductionError(
            f"cannot resolve Git commit {revision!r} in {repo_root}: {detail}")
    commit = result.stdout.strip().lower()
    if not re.fullmatch(r"[0-9a-f]{40}", commit):
        raise ReproductionError(
            f"Git returned a non-canonical commit ID for {revision!r}: {commit!r}")
    return commit


def _is_ancestor(repo_root: Path, ancestor: str, descendant: str) -> bool:
    result = subprocess.run(
        [
            "git",
            "-C",
            str(repo_root),
            "merge-base",
            "--is-ancestor",
            ancestor,
            descendant,
        ],
        check=False,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    if result.returncode == 0:
        return True
    if result.returncode == 1:
        return False
    detail = result.stderr.strip() or result.stdout.strip()
    raise ReproductionError(
        f"Git ancestry check failed in {repo_root}: {detail}")


def _require_freeze_ancestry(repo_root: Path) -> str:
    freeze = _resolve_commit(repo_root, FREEZE_COMMIT)
    current = _resolve_commit(repo_root, "HEAD")
    if freeze != FREEZE_COMMIT:
        raise ReproductionError(
            f"freeze commit resolved unexpectedly: {freeze} != {FREEZE_COMMIT}")
    if not _is_ancestor(repo_root, freeze, current):
        raise ReproductionError(
            f"current/result commit {current} does not descend from frozen "
            f"protocol commit {FREEZE_COMMIT}")
    return current


def _head_contains(repo_root: Path, relative_path: str) -> bool:
    result = subprocess.run(
        [
            "git",
            "-C",
            str(repo_root),
            "ls-tree",
            "-z",
            "HEAD",
            "--",
            relative_path,
        ],
        check=False,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    if result.returncode != 0:
        detail = result.stderr.decode("utf-8", errors="replace").strip()
        raise ReproductionError(
            f"cannot inspect HEAD implementation path {relative_path!r}: {detail}")
    entries = [entry for entry in result.stdout.split(b"\0") if entry]
    expected_suffix = b"\t" + relative_path.encode("utf-8")
    return any(b" blob " in entry and entry.endswith(expected_suffix)
               for entry in entries)


def _implementation_status(repo_root: Path) -> bytes:
    result = subprocess.run(
        [
            "git",
            "-C",
            str(repo_root),
            "status",
            "--porcelain=v1",
            "-z",
            "--untracked-files=all",
            "--",
            *IMPLEMENTATION_PATHS,
        ],
        check=False,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    if result.returncode != 0:
        detail = result.stderr.decode("utf-8", errors="replace").strip()
        raise ReproductionError(
            f"cannot inspect implementation cleanliness in {repo_root}: {detail}")
    return result.stdout


def _require_clean_implementation(repo_root: Path) -> None:
    loaded_reproducer = Path(__file__).resolve(strict=True)
    committed_reproducer = (
        repo_root / "analysis" / "reproduce_phase2_qgap.py"
    ).resolve(strict=True)
    if loaded_reproducer != committed_reproducer:
        raise ReproductionError(
            "executing reproducer is not the implementation under explicit "
            f"repo_root: {loaded_reproducer} != {committed_reproducer}")

    missing_from_head = [
        relative
        for relative in IMPLEMENTATION_PATHS
        if not _head_contains(repo_root, relative)
    ]
    missing_from_worktree = [
        relative
        for relative in IMPLEMENTATION_PATHS
        if not (repo_root / relative).is_file()
        or (repo_root / relative).is_symlink()
    ]
    if missing_from_head or missing_from_worktree:
        raise ReproductionError(
            "committed implementation is incomplete; "
            f"missing_from_HEAD={missing_from_head}, "
            f"missing_or_nonregular_in_worktree={missing_from_worktree}")

    status = _implementation_status(repo_root)
    if status:
        rendered = status.decode("utf-8", errors="backslashreplace").replace(
            "\0", " | ").strip(" |")
        raise ReproductionError(
            "implementation inputs differ from HEAD; commit or restore only "
            f"these frozen files before reproduction: {rendered}")


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _require_canonical_output_set(root: Path, label: str) -> None:
    required = set(CANONICAL_OUTPUTS)
    files: set[str] = set()
    invalid: list[str] = []
    for entry in root.iterdir():
        if entry.is_symlink() or not entry.is_file():
            invalid.append(entry.name)
        else:
            files.add(entry.name)
    missing = sorted(required - files)
    extra = sorted(files - required)
    if missing or extra or invalid:
        raise ReproductionError(
            f"{label} canonical outputs mismatch; missing={missing}, "
            f"extra={extra}, non_regular={sorted(invalid)}")


def _verify_inventory(root: Path, label: str) -> None:
    inventory = root / INVENTORY_NAME
    raw = inventory.read_bytes()
    if raw.startswith(b"\xef\xbb\xbf"):
        raise ReproductionError(f"{label} inventory must not contain a UTF-8 BOM")
    if b"\r" in raw or not raw.endswith(b"\n"):
        raise ReproductionError(
            f"{label} inventory must use LF line endings and end with LF")
    try:
        raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise ReproductionError(
            f"{label} inventory is not valid UTF-8") from exc

    with inventory.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        if tuple(reader.fieldnames or ()) != INVENTORY_COLUMNS:
            raise ReproductionError(
                f"{label} inventory columns must be {INVENTORY_COLUMNS}, "
                f"got {reader.fieldnames}")
        rows = list(reader)

    covered = set(CANONICAL_OUTPUTS) - {INVENTORY_NAME}
    paths: list[str] = []
    canonical_lines = ["path,bytes,sha256\n"]
    for row_number, row in enumerate(rows, start=2):
        if None in row or set(row) != set(INVENTORY_COLUMNS):
            raise ReproductionError(
                f"{label} inventory row {row_number} has an invalid column count")
        relative = row["path"]
        if (
            not relative
            or "\\" in relative
            or Path(relative).is_absolute()
            or Path(relative).as_posix() != relative
            or any(part in ("", ".", "..") for part in relative.split("/"))
        ):
            raise ReproductionError(
                f"{label} inventory row {row_number} has unsafe/non-POSIX path "
                f"{relative!r}")
        if relative in paths:
            raise ReproductionError(
                f"{label} inventory contains duplicate path {relative!r}")
        paths.append(relative)

        size_text = row["bytes"]
        if not size_text.isdigit() or str(int(size_text)) != size_text:
            raise ReproductionError(
                f"{label} inventory row {row_number} has non-canonical byte "
                f"count {size_text!r}")
        digest = row["sha256"]
        if not SHA256_TEXT.fullmatch(digest):
            raise ReproductionError(
                f"{label} inventory row {row_number} has invalid SHA-256 "
                f"{digest!r}")
        canonical_lines.append(f"{relative},{size_text},{digest}\n")

    if paths != sorted(paths):
        raise ReproductionError(
            f"{label} inventory paths are not lexicographically sorted")
    path_set = set(paths)
    missing = sorted(covered - path_set)
    extra = sorted(path_set - covered)
    if missing or extra:
        raise ReproductionError(
            f"{label} inventory coverage mismatch; missing={missing}, "
            f"extra={extra}; {INVENTORY_NAME} must be excluded")
    if raw != "".join(canonical_lines).encode("utf-8"):
        raise ReproductionError(
            f"{label} inventory is not canonical UTF-8/LF CSV")

    for relative, row in zip(paths, rows):
        path = root / relative
        if not path.is_file() or path.is_symlink():
            raise ReproductionError(
                f"{label} inventory target is not a regular file: {relative}")
        expected_size = int(row["bytes"])
        actual_size = path.stat().st_size
        if actual_size != expected_size:
            raise ReproductionError(
                f"{label} inventory size mismatch for {relative}: "
                f"{actual_size} != {expected_size}")
        actual_digest = _sha256(path)
        if actual_digest != row["sha256"]:
            raise ReproductionError(
                f"{label} inventory SHA-256 mismatch for {relative}: "
                f"{actual_digest} != {row['sha256']}")


def _files_equal(expected: Path, rebuilt: Path) -> bool:
    if expected.stat().st_size != rebuilt.stat().st_size:
        return False
    with expected.open("rb") as expected_handle, rebuilt.open("rb") as rebuilt_handle:
        while True:
            expected_chunk = expected_handle.read(1024 * 1024)
            rebuilt_chunk = rebuilt_handle.read(1024 * 1024)
            if expected_chunk != rebuilt_chunk:
                return False
            if not expected_chunk:
                return True


def _compare_all_outputs(expected_dir: Path, rebuilt_dir: Path) -> None:
    mismatches = [
        name
        for name in CANONICAL_OUTPUTS
        if not _files_equal(expected_dir / name, rebuilt_dir / name)
    ]
    if mismatches:
        raise ReproductionError(
            "byte-for-byte output comparison failed for: "
            + ", ".join(mismatches))


def _default_runner(**kwargs: object) -> object:
    try:
        from analysis import phase2_qgap_retrospective as analysis_runner
    except ImportError:
        import phase2_qgap_retrospective as analysis_runner  # type: ignore

    repo_root = Path(kwargs["repo_root"])
    expected_module = (
        repo_root / "analysis" / "phase2_qgap_retrospective.py"
    ).resolve(strict=True)
    loaded_module = Path(analysis_runner.__file__).resolve(strict=True)
    if loaded_module != expected_module:
        raise ReproductionError(
            "loaded analysis runner is not the one under explicit repo_root: "
            f"{loaded_module} != {expected_module}")
    return analysis_runner.run(**kwargs)


def reproduce(
    repo_root: Path,
    source_root: Path,
    spec_path: Path,
    source_manifest_path: Path,
    expected_dir: Path,
    *,
    zip_root: Path | None = None,
    require_zips: bool = True,
    runner: Runner | None = None,
) -> tuple[str, ...]:
    """Rebuild the analysis once and byte-compare all canonical outputs."""
    resolved_repo = _resolve_directory(repo_root, "repo_root")
    resolved_source = _resolve_directory(source_root, "source_root")
    resolved_spec = _resolve_file(spec_path, "spec")
    resolved_manifest = _resolve_file(
        source_manifest_path, "source_manifest")
    resolved_expected = _resolve_directory(expected_dir, "expected_dir")
    resolved_zip = (
        _resolve_directory(zip_root, "zip_root") if zip_root is not None else None
    )

    _require_freeze_ancestry(resolved_repo)
    _require_clean_implementation(resolved_repo)
    committed_spec = resolved_repo / "analysis" / "phase2_qgap_spec.json"
    if not _files_equal(committed_spec, resolved_spec):
        raise ReproductionError(
            "explicit spec does not byte-match the clean spec committed at HEAD")
    _require_canonical_output_set(resolved_expected, "committed")
    _verify_inventory(resolved_expected, "committed")

    analysis_runner = runner or _default_runner
    with tempfile.TemporaryDirectory(prefix="phase2-qgap-reproduce-") as temp:
        rebuilt_dir = Path(temp).resolve() / "analysis"
        rebuilt_dir.mkdir(parents=False, exist_ok=False)
        analysis_runner(
            repo_root=resolved_repo,
            source_root=resolved_source,
            spec_path=resolved_spec,
            source_manifest_path=resolved_manifest,
            out_dir=rebuilt_dir,
            zip_root=resolved_zip,
            require_zips=require_zips,
        )
        _require_canonical_output_set(rebuilt_dir, "rebuilt")
        _verify_inventory(rebuilt_dir, "rebuilt")
        _compare_all_outputs(resolved_expected, rebuilt_dir)

    return CANONICAL_OUTPUTS


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", required=True, type=Path)
    parser.add_argument("--source-root", required=True, type=Path)
    parser.add_argument("--spec", required=True, type=Path)
    parser.add_argument("--source-manifest", required=True, type=Path)
    parser.add_argument("--expected", required=True, type=Path)
    parser.add_argument("--zip-root", type=Path)
    parser.add_argument(
        "--no-require-zips",
        action="store_true",
        help="pass require_zips=False to the frozen analysis runner",
    )
    args = parser.parse_args(argv)
    outputs = reproduce(
        args.repo_root,
        args.source_root,
        args.spec,
        args.source_manifest,
        args.expected,
        zip_root=args.zip_root,
        require_zips=not args.no_require_zips,
    )
    print(
        f"Reproduced {len(outputs)} Phase-2b Q-gap outputs byte-for-byte "
        f"from a descendant of {FREEZE_COMMIT}.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
