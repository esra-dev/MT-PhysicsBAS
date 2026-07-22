import csv
import json
from pathlib import Path

from analysis import build_phase1_claim_ledger as ledger_builder
from analysis import phase1_claim_ledger_lint as ledger_lint


FIELDS = [
    "document", "line", "claim_text", "claim_text_sha256", "metric", "value", "run_or_file",
    "status", "match_result", "classification",
]


def _fixture(tmp_path: Path, source_line: str, *, value: str):
    source = tmp_path / "source.md"
    source.write_text(source_line + "\n", encoding="utf-8")
    sources = tmp_path / "sources.json"
    repo_source = source.relative_to(tmp_path).as_posix()
    sources.write_text(json.dumps({"sources": [repo_source]}), encoding="utf-8")
    ledger = tmp_path / "ledger.csv"
    with ledger.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerow({
            "document": repo_source,
            "line": 1,
            "claim_text": source_line,
            "claim_text_sha256": ledger_lint._digest(source_line),
            "metric": "test",
            "value": value,
            "run_or_file": "phase1_v2_corrected/test/result.csv",
            "status": "verified_current",
            "match_result": "match",
            "classification": "corrected_result",
        })
    return ledger, sources


def test_claim_ledger_accepts_exact_coverage(tmp_path, monkeypatch):
    monkeypatch.setattr(ledger_lint, "ROOT", tmp_path)
    evidence = tmp_path / "phase1_v2_corrected" / "test" / "result.csv"
    evidence.parent.mkdir(parents=True)
    evidence.write_text("result\n", encoding="utf-8")
    ledger, sources = _fixture(tmp_path, "effect +0.25 at n=20", value="+0.25;20")
    assert ledger_lint.lint(ledger, sources) == []


def test_claim_ledger_rejects_stale_or_missing_value_tokens(tmp_path, monkeypatch):
    monkeypatch.setattr(ledger_lint, "ROOT", tmp_path)
    evidence = tmp_path / "phase1_v2_corrected" / "test" / "result.csv"
    evidence.parent.mkdir(parents=True)
    evidence.write_text("result\n", encoding="utf-8")
    ledger, sources = _fixture(tmp_path, "effect +0.25 at n=20", value="+0.25")
    errors = ledger_lint.lint(ledger, sources)
    assert any("value tokens differ" in error for error in errors)


def test_audit_tag_lint_accepts_tagged_wrapped_blocks_and_table_header(tmp_path, monkeypatch):
    monkeypatch.setattr(ledger_lint, "ROOT", tmp_path)
    audit = tmp_path / "audit.md"
    audit.write_text(
        "# Heading\n\n"
        "[VERIFIED] A factual paragraph. Evidence: `src/X.java:2`.\nwith a wrapped continuation.\n\n"
        "| Claim | Source |\n|---|---|\n"
        "| [STATED] value | `results.csv:2` |\n\n"
        "- [INFERRED] a list item; source: `docs/a.md` §2\n  with a continuation\n",
        encoding="utf-8",
    )
    assert ledger_lint._audit_paragraph_errors(audit) == []


def test_audit_tag_lint_rejects_untagged_paragraph(tmp_path, monkeypatch):
    monkeypatch.setattr(ledger_lint, "ROOT", tmp_path)
    audit = tmp_path / "audit.md"
    audit.write_text("# Heading\n\nAn unsupported fact.\n", encoding="utf-8")
    assert any("lacks provenance tag" in error
               for error in ledger_lint._audit_paragraph_errors(audit))


def test_audit_tag_lint_rejects_unsourced_factual_block(tmp_path, monkeypatch):
    monkeypatch.setattr(ledger_lint, "ROOT", tmp_path)
    audit = tmp_path / "audit.md"
    audit.write_text("# Heading\n\n[VERIFIED] Unsupported fact.\n", encoding="utf-8")
    assert any("lacks a source pointer" in error
               for error in ledger_lint._audit_paragraph_errors(audit))


def test_audit_source_lint_checks_path_and_line_range(tmp_path, monkeypatch):
    monkeypatch.setattr(ledger_lint, "ROOT", tmp_path)
    source = tmp_path / "src" / "X.java"
    source.parent.mkdir(parents=True)
    source.write_text("one\ntwo\n", encoding="utf-8")
    audit = tmp_path / "audit.md"
    audit.write_text(
        "[VERIFIED] Good. Evidence: `src/X.java:1-2`.\n"
        "[VERIFIED] Bad. Evidence: `src/X.java:3`.\n",
        encoding="utf-8",
    )
    errors = ledger_lint._audit_source_reference_errors(audit)
    assert len(errors) == 1
    assert "exceeds 2" in errors[0]


def test_builder_emits_complete_human_readable_ledger(tmp_path, monkeypatch):
    monkeypatch.setattr(ledger_lint, "ROOT", tmp_path)
    monkeypatch.setattr(ledger_builder, "ROOT", tmp_path)
    source = tmp_path / "docs" / "phase1_results_v2.md"
    source.parent.mkdir(parents=True)
    source.write_text("auc_goal changed by +0.25 for n=20\n", encoding="utf-8")
    sources = tmp_path / "sources.json"
    sources.write_text(
        json.dumps({"sources": ["docs/phase1_results_v2.md"]}), encoding="utf-8"
    )
    output = tmp_path / "ledger.csv"
    evidence = tmp_path / "phase1_v2_corrected" / "analysis" / "registered"
    evidence.mkdir(parents=True)
    (evidence / "phase1_v2_registered_family.csv").write_text(
        "result\n", encoding="utf-8")
    assert ledger_builder.build(sources, output) == 1
    with output.open(encoding="utf-8", newline="") as handle:
        row = next(csv.DictReader(handle))
    assert row["claim_text"] == "auc_goal changed by +0.25 for n=20"
    assert row["value"] == "+0.25;20"
    assert row["classification"] == "corrected_result"
    assert ledger_lint.lint(output, sources) == []


def test_claim_ledger_rejects_zero_corrected_p_value(tmp_path, monkeypatch):
    monkeypatch.setattr(ledger_lint, "ROOT", tmp_path)
    evidence = tmp_path / "phase1_v2_corrected" / "test" / "result.csv"
    evidence.parent.mkdir(parents=True)
    evidence.write_text("result\n", encoding="utf-8")
    ledger, sources = _fixture(tmp_path, "corrected p=0 at n=20", value="0;20")
    errors = ledger_lint.lint(ledger, sources)
    assert any("reports p/q as zero" in error for error in errors)
