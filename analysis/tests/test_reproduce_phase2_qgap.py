from __future__ import annotations

import hashlib
from pathlib import Path

import pytest

from analysis import reproduce_phase2_qgap as reproduce


NON_INVENTORY_OUTPUTS = tuple(
    name
    for name in reproduce.CANONICAL_OUTPUTS
    if name != reproduce.INVENTORY_NAME
)


def _content(name: str) -> bytes:
    if name.endswith(".png"):
        return b"\x89PNG\r\n\x1a\nsynthetic-image-" + name.encode("ascii")
    if name.endswith(".json"):
        return b'{"kind":"synthetic","real_q_data":false}\n'
    if name.endswith(".md"):
        return b"# Synthetic retrospective result\n"
    return f"kind,value\nsynthetic,{name}\n".encode("utf-8")


def _write_inventory(
    root: Path,
    *,
    paths: tuple[str, ...] = NON_INVENTORY_OUTPUTS,
    digest_override: dict[str, str] | None = None,
) -> None:
    overrides = digest_override or {}
    lines = ["path,bytes,sha256\n"]
    for name in sorted(paths):
        path = root / name
        digest = overrides.get(name, hashlib.sha256(path.read_bytes()).hexdigest())
        lines.append(f"{name},{path.stat().st_size},{digest}\n")
    (root / reproduce.INVENTORY_NAME).write_bytes(
        "".join(lines).encode("utf-8"))


def _write_output_tree(
    root: Path,
    *,
    overrides: dict[str, bytes] | None = None,
    omitted: set[str] | None = None,
    extra: dict[str, bytes] | None = None,
) -> None:
    root.mkdir(parents=True, exist_ok=True)
    changed = overrides or {}
    skipped = omitted or set()
    for name in NON_INVENTORY_OUTPUTS:
        if name not in skipped:
            (root / name).write_bytes(changed.get(name, _content(name)))
    for name, content in (extra or {}).items():
        (root / name).write_bytes(content)
    if reproduce.INVENTORY_NAME not in skipped:
        inventory_paths = tuple(
            name for name in NON_INVENTORY_OUTPUTS if name not in skipped)
        _write_inventory(root, paths=inventory_paths)


def _inputs(tmp_path: Path) -> dict[str, Path]:
    repo = tmp_path / "repo"
    source = tmp_path / "immutable-source"
    expected = tmp_path / "committed-analysis"
    repo.mkdir()
    source.mkdir()
    spec = repo / "analysis" / "phase2_qgap_spec.json"
    spec.parent.mkdir()
    manifest = tmp_path / "immutable-source-manifest.json"
    spec.write_text('{"synthetic":true}\n', encoding="utf-8")
    manifest.write_text('{"synthetic":true}\n', encoding="utf-8")
    _write_output_tree(expected)
    return {
        "repo_root": repo,
        "source_root": source,
        "spec_path": spec,
        "source_manifest_path": manifest,
        "expected_dir": expected,
    }


@pytest.fixture
def bypass_git_ancestry(monkeypatch):
    monkeypatch.setattr(
        reproduce,
        "_require_freeze_ancestry",
        lambda repo_root: "1" * 40,
    )
    monkeypatch.setattr(
        reproduce,
        "_require_clean_implementation",
        lambda repo_root: None,
    )


def test_reproduce_uses_explicit_inputs_fresh_temp_and_exact_bytes(
    tmp_path, bypass_git_ancestry
):
    inputs = _inputs(tmp_path)
    received: dict[str, object] = {}

    def fake_runner(**kwargs):
        received.update(kwargs)
        _write_output_tree(kwargs["out_dir"])
        return tuple(
            kwargs["out_dir"] / name for name in reproduce.CANONICAL_OUTPUTS)

    outputs = reproduce.reproduce(**inputs, runner=fake_runner)

    assert outputs == reproduce.CANONICAL_OUTPUTS
    assert received["repo_root"] == inputs["repo_root"].resolve()
    assert received["source_root"] == inputs["source_root"].resolve()
    assert received["spec_path"] == inputs["spec_path"].resolve()
    assert (
        received["source_manifest_path"]
        == inputs["source_manifest_path"].resolve()
    )
    assert received["zip_root"] is None
    assert received["require_zips"] is True
    rebuilt = received["out_dir"]
    assert isinstance(rebuilt, Path)
    assert rebuilt != inputs["expected_dir"]
    assert not rebuilt.exists(), "TemporaryDirectory must be removed after comparison"


def test_reproduce_does_not_float_canonicalize_csv(
    tmp_path, bypass_git_ancestry
):
    inputs = _inputs(tmp_path)
    target = "qgap_seed_rows.csv"
    expected_content = b"metric,value\nburden,1.0\n"
    (inputs["expected_dir"] / target).write_bytes(expected_content)
    _write_inventory(inputs["expected_dir"])

    def fake_runner(**kwargs):
        _write_output_tree(
            kwargs["out_dir"],
            overrides={target: b"metric,value\nburden,1.00\n"},
        )

    with pytest.raises(
        reproduce.ReproductionError,
        match="byte-for-byte output comparison failed.*qgap_seed_rows.csv",
    ):
        reproduce.reproduce(**inputs, runner=fake_runner)


@pytest.mark.parametrize("tree", ["committed", "rebuilt"])
@pytest.mark.parametrize("defect", ["missing", "extra"])
def test_reproduce_rejects_missing_or_extra_canonical_outputs(
    tmp_path, bypass_git_ancestry, tree, defect
):
    inputs = _inputs(tmp_path)
    target = "detectability_audit.png"

    if tree == "committed":
        if defect == "missing":
            (inputs["expected_dir"] / target).unlink()
        else:
            (inputs["expected_dir"] / "unregistered.txt").write_bytes(b"extra")

    def fake_runner(**kwargs):
        if tree == "rebuilt" and defect == "missing":
            _write_output_tree(kwargs["out_dir"], omitted={target})
        elif tree == "rebuilt":
            _write_output_tree(
                kwargs["out_dir"], extra={"unregistered.txt": b"extra"})
        else:
            _write_output_tree(kwargs["out_dir"])

    with pytest.raises(
        reproduce.ReproductionError,
        match=rf"{tree} canonical outputs mismatch",
    ):
        reproduce.reproduce(**inputs, runner=fake_runner)


def test_inventory_must_cover_every_other_output_and_exclude_itself(tmp_path):
    root = tmp_path / "analysis"
    _write_output_tree(root)
    _write_inventory(
        root,
        paths=tuple(
            name
            for name in NON_INVENTORY_OUTPUTS
            if name != "qgap_cell_summary.csv"
        )
        + (reproduce.INVENTORY_NAME,),
    )

    with pytest.raises(
        reproduce.ReproductionError,
        match=r"inventory coverage mismatch.*qgap_cell_summary.csv.*SHA256SUMS.csv",
    ):
        reproduce._verify_inventory(root, "synthetic")


def test_inventory_recomputes_sha256_independently(tmp_path):
    root = tmp_path / "analysis"
    _write_output_tree(root)
    _write_inventory(
        root,
        digest_override={"ordering_assessment.csv": "0" * 64},
    )

    with pytest.raises(
        reproduce.ReproductionError,
        match="inventory SHA-256 mismatch for ordering_assessment.csv",
    ):
        reproduce._verify_inventory(root, "synthetic")


def test_inventory_rejects_noncanonical_order_and_crlf(tmp_path):
    root = tmp_path / "analysis"
    _write_output_tree(root)
    inventory = root / reproduce.INVENTORY_NAME
    rows = inventory.read_text(encoding="utf-8").splitlines()
    inventory.write_bytes(("\r\n".join([rows[0], *reversed(rows[1:])]) + "\r\n")
                          .encode("utf-8"))

    with pytest.raises(
        reproduce.ReproductionError,
        match="must use LF line endings",
    ):
        reproduce._verify_inventory(root, "synthetic")


def test_freeze_ancestry_rejects_unrelated_current_commit(
    tmp_path, monkeypatch
):
    current = "a" * 40

    def fake_resolve(repo_root, revision):
        return reproduce.FREEZE_COMMIT if revision == reproduce.FREEZE_COMMIT else current

    monkeypatch.setattr(reproduce, "_resolve_commit", fake_resolve)
    monkeypatch.setattr(reproduce, "_is_ancestor", lambda *args: False)

    with pytest.raises(
        reproduce.ReproductionError,
        match=rf"{current} does not descend from frozen protocol commit",
    ):
        reproduce._require_freeze_ancestry(tmp_path)


def test_freeze_ancestry_accepts_descendant_current_commit(
    tmp_path, monkeypatch
):
    current = "b" * 40

    def fake_resolve(repo_root, revision):
        return reproduce.FREEZE_COMMIT if revision == reproduce.FREEZE_COMMIT else current

    calls: list[tuple[Path, str, str]] = []

    def fake_is_ancestor(repo_root, ancestor, descendant):
        calls.append((repo_root, ancestor, descendant))
        return True

    monkeypatch.setattr(reproduce, "_resolve_commit", fake_resolve)
    monkeypatch.setattr(reproduce, "_is_ancestor", fake_is_ancestor)

    assert reproduce._require_freeze_ancestry(tmp_path) == current
    assert calls == [(tmp_path, reproduce.FREEZE_COMMIT, current)]


def test_clean_implementation_guard_rejects_dirty_frozen_code(
    tmp_path, monkeypatch
):
    for relative in reproduce.IMPLEMENTATION_PATHS:
        path = tmp_path / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("synthetic committed implementation\n", encoding="utf-8")

    monkeypatch.setattr(
        reproduce,
        "__file__",
        str(tmp_path / "analysis" / "reproduce_phase2_qgap.py"),
    )
    monkeypatch.setattr(reproduce, "_head_contains", lambda *args: True)
    monkeypatch.setattr(
        reproduce,
        "_implementation_status",
        lambda repo_root: (
            b" M analysis/phase2_qgap_core.py\0"
            b"?? analysis/phase2_qgap_retrospective.py\0"
        ),
    )

    with pytest.raises(
        reproduce.ReproductionError,
        match=r"implementation inputs differ from HEAD.*phase2_qgap_core.py",
    ):
        reproduce._require_clean_implementation(tmp_path)


def test_clean_implementation_guard_rejects_external_reproducer(tmp_path):
    expected = tmp_path / "analysis" / "reproduce_phase2_qgap.py"
    expected.parent.mkdir(parents=True)
    expected.write_text("synthetic committed reproducer\n", encoding="utf-8")

    with pytest.raises(
        reproduce.ReproductionError,
        match="executing reproducer is not the implementation under explicit repo_root",
    ):
        reproduce._require_clean_implementation(tmp_path)
