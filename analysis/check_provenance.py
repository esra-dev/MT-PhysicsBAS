#!/usr/bin/env python3
"""Phase-1 provenance golden check (stdlib only, exit 1 on violation).

Guards the three provenance rules of the 2026-07-19 Phase-1 audit, so that
superseded numbers cannot silently re-enter the record:

  (a) STALE SPILL PHYSICS - lab3's cross-zone spill was retuned on 2026-07-08
      (original +50 lux / 0.25*Sun -> bumped +150 lux / 0.40*Sun -> current
      +100 lux / 0.30*Sun). In current-truth documents, any mention of a
      superseded magnitude pair must sit in a context that marks it as
      historical. (150/0.40 is additionally allowed in lab3_slow/_slow
      contexts - that IS the slow lab's current physics.)

  (b) PRE-INVERSION RUN IDS - the Phase-1 runs that predate the action-space
      inversion of 2026-07-10 (ACTION_SPACE_INVERSION.md) may be cited in
      current-truth documents only where the surrounding block, or the
      enclosing section heading, marks them as pre-inversion / superseded.
      Historical per-run documents are exempted by a mandatory PROVENANCE
      banner in their first lines.

  (c) CROSS_ZONE_BONUS DISCLOSURE - wherever Phase-1 lab3 results are
      presented, the text must state the arm's `cross_zone_bonus`
      (THESIS_STATE_REPORT.md section 5.5 rule). Enforced as a per-scope
      "must contain" requirement, incl. the dashboard data provenance.

Run:  python analysis/check_provenance.py
"""
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

# ---------------------------------------------------------------------------
# Registry
# ---------------------------------------------------------------------------

# Phase-1 runs executed BEFORE the action-space inversion (2026-07-10).
PHASE1_PRE_INVERSION_RUNS = {
    "27336756264",  # arm-C headline (superseded by 29639767776)
    "27344626272",  # arm-A baseline control
    "27342571251",  # ib5 sensitivity
    "27347962788",  # arm-B pbrs_only (FAILED dispatch)
    "28929859927",  # arm-B pbrs_only re-dispatch
    "27440842780",  # xzone as-is control        (original physics 50/0.25)
    "27461188614",  # xzone bumped, seeds 1-10   (bumped physics 150/0.40)
    "27462446044",  # xzone bumped, seeds 11-20  (bumped physics 150/0.40)
    "27464846574",  # xzone untargeted ablation  (bumped physics 150/0.40)
    "28941204656",  # xzone-mid, current physics but pre-inversion instrument
}

# Phase-1 post-inversion runs of record (allowed anywhere).
PHASE1_POST_INVERSION_RUNS = {
    "29105464710",  # arm D (sensitivity record)
    "29639767776",  # arm C - headline of record
    "29641043465",  # E-sweep
    "29641899071",  # E-sweep
}

PHASE1_HEADLINE_RUN = "29639767776"
# Golden value: lab2 auc_goal delta of the post-inversion headline run.
PHASE1_LAB2_AUC_GOAL_PREFIX = "0.0167889"

# Documents that state current truth: every pre-inversion ID / stale magnitude
# needs a nearby historical marker.
CURRENT_DOCS = [
    "docs/_audit/THESIS_STATE_REPORT.md",
    "docs/thesis_chapter_phase2.md",
]

# Historical per-run / draft documents: must open with a provenance banner
# (then their in-body IDs and magnitudes are read as historical).
HISTORICAL_DOCS = [
    "docs/phase1_xzone_asis_analysis.md",
    "docs/phase1_xzone_bumped_analysis.md",
    "docs/phase1_xzone_replication_s11_20_analysis.md",
    "docs/phase1_xzone_ablation_analysis.md",
    "docs/kg_crosszone_coupling_fix.md",
    "docs/paper_results_section.md",
    "docs/phases_compilation.tex",
]

MARKER_RE = re.compile(r"(?i)pre-inversion|superseded|\bstale\b|\bretired\b")
STALE_HISTORY_RE = re.compile(
    r"(?i)original|bumped|superseded|pre-inversion|retuned|history|\bstale\b|\bwere\b"
)
SLOW_LAB_RE = re.compile(r"(?i)lab3_slow|building_3_slow|_slow\b|slow lab")
BANNER_RE = re.compile(r"(?i)provenance")
HEADING_RE = re.compile(r"^(#{1,4} |\\(sub)*section\{|% ----)")

# Superseded lab3 spill magnitudes. 150/0.40 forms carry a _slow escape.
STALE_PATTERNS = [
    (re.compile(r"50\s*/\s*0\.25"), False),
    (re.compile(r"0\.25\s*[·*]\s*[Ss]un"), False),
    (re.compile(r"\+50\s*lux"), False),
    (re.compile(r"lamp bleed \+?50\b"), False),
    (re.compile(r"150\s*/\s*0\.40"), True),
    (re.compile(r"0\.40\s*[·*]\s*[Ss]un"), True),
    (re.compile(r"lamp bleed \+?150\b"), True),
]

RUN_ID_RE = re.compile(r"\b2[0-9]{10}\b")

violations = []


def report(path, lineno, cls, msg):
    violations.append(f"{path}:{lineno}: [{cls}] {msg}")


def block_bounds(lines, i):
    """Enclosing contiguous non-blank block of line i (0-based), padded by 2."""
    lo = i
    while lo > 0 and lines[lo - 1].strip():
        lo -= 1
    hi = i
    while hi < len(lines) - 1 and lines[hi + 1].strip():
        hi += 1
    return max(0, lo - 2), min(len(lines) - 1, hi + 2)


def nearest_heading(lines, i):
    for j in range(i, -1, -1):
        if HEADING_RE.match(lines[j]):
            return lines[j]
    return ""


def context_has(lines, i, regex):
    lo, hi = block_bounds(lines, i)
    if any(regex.search(lines[j]) for j in range(lo, hi + 1)):
        return True
    return bool(regex.search(nearest_heading(lines, i)))


def check_current_doc(rel):
    path = ROOT / rel
    lines = path.read_text(encoding="utf-8").splitlines()
    for i, line in enumerate(lines):
        for rid in RUN_ID_RE.findall(line):
            if rid in PHASE1_PRE_INVERSION_RUNS and not context_has(lines, i, MARKER_RE):
                report(rel, i + 1, "b",
                       f"pre-inversion Phase-1 run {rid} cited without a "
                       "pre-inversion/superseded marker in its block or heading")
        for pat, slow_ok in STALE_PATTERNS:
            if pat.search(line):
                if slow_ok and context_has(lines, i, SLOW_LAB_RE):
                    continue
                if not context_has(lines, i, STALE_HISTORY_RE):
                    report(rel, i + 1, "a",
                           f"superseded lab3 spill magnitude ({pat.pattern}) "
                           "without a historical marker in its block or heading")
    return lines


def check_historical_doc(rel):
    path = ROOT / rel
    # .md banners sit right under the title; the .tex banner sits after the
    # LaTeX preamble (~line 50), hence the 80-line window.
    head = path.read_text(encoding="utf-8").splitlines()[:80]
    if not (any(BANNER_RE.search(l) for l in head)
            and any(re.search(r"(?i)pre-inversion", l) for l in head)):
        report(rel, 1, "b",
               "historical Phase-1 document lacks the PROVENANCE banner "
               "(pre-inversion / superseded-physics) in its first 80 lines")


def section_span(lines, heading_prefix):
    start = None
    level = None
    for i, l in enumerate(lines):
        if l.startswith(heading_prefix):
            start = i
            level = len(l) - len(l.lstrip("#"))
            break
    if start is None:
        return None
    for j in range(start + 1, len(lines)):
        m = re.match(r"^(#{1,6}) ", lines[j])
        if m and len(m.group(1)) <= level:
            return lines[start:j]
    return lines[start:]


def check_disclosures(state_lines):
    rel = CURRENT_DOCS[0]
    # (c) exec-summary lab3 row
    row = [(i, l) for i, l in enumerate(state_lines) if l.startswith("| 1 — lab3")]
    if not row:
        report(rel, 1, "c", "executive-summary lab3 row not found")
    elif "cross_zone_bonus" not in row[0][1]:
        report(rel, row[0][0] + 1, "c",
               "executive-summary lab3 row lacks the cross_zone_bonus disclosure")
    # (c) section-level requirements
    for prefix, needle, label in [
        ("### 5.2 ", "cross_zone_bonus = 0", "section 5.2 (headline results)"),
        ("### 10.3 ", "cross_zone_bonus", "section 10.3 (standing adversarial results)"),
    ]:
        span = section_span(state_lines, prefix)
        if span is None:
            report(rel, 1, "c", f"{label} heading not found")
        elif not any(needle in l for l in span):
            report(rel, 1, "c", f"{label} lacks the `{needle}` disclosure")
    # (c) Phase-2 chapter invokes the Phase-1 lab3 tax -> must disclose
    chap = (ROOT / CURRENT_DOCS[1]).read_text(encoding="utf-8")
    if "cross_zone_bonus" not in chap:
        report(CURRENT_DOCS[1], 1, "c",
               "chapter invokes the Phase-1 lab3 result without a "
               "cross_zone_bonus disclosure")


def check_dashboard():
    # phase1.json must be the post-inversion headline with provenance metadata
    rel = "dashboard/public/data/phase1.json"
    try:
        d = json.loads((ROOT / rel).read_text(encoding="utf-8"))
    except FileNotFoundError:
        report(rel, 1, "b", "missing (run dashboard/scripts/prepare_data.py)")
        return
    prov = d.get("_provenance", {})
    if prov.get("run_id") != PHASE1_HEADLINE_RUN:
        report(rel, 1, "b",
               f"_provenance.run_id is {prov.get('run_id')!r}, expected the "
               f"post-inversion headline {PHASE1_HEADLINE_RUN}")
    if "cross_zone_bonus" not in prov:
        report(rel, 1, "c", "_provenance lacks the cross_zone_bonus field")
    rows = [r for r in d.get("learning_speed", [])
            if r.get("profile") == "lab2" and r.get("metric") == "auc_goal"]
    if not rows or not str(rows[0].get("mean_diff_true_minus_false", "")) \
            .startswith(PHASE1_LAB2_AUC_GOAL_PREFIX):
        report(rel, 1, "b",
               "lab2 auc_goal delta does not match the post-inversion headline "
               f"run (expected prefix {PHASE1_LAB2_AUC_GOAL_PREFIX}); phase1.json "
               "appears to be built from a superseded source")
    # trace JSONs must self-describe as pre-inversion demo material
    for rel2 in ("dashboard/public/data/training.json",
                 "dashboard/public/data/replay_lab3.json"):
        try:
            t = json.loads((ROOT / rel2).read_text(encoding="utf-8"))
        except FileNotFoundError:
            report(rel2, 1, "b", "missing (run dashboard/scripts/prepare_data.py)")
            continue
        blob = json.dumps(t.get("_provenance", {}))
        if "pre-inversion" not in blob:
            report(rel2, 1, "b",
                   "_provenance does not mark the demo traces as pre-inversion")
    # sandbox physics must encode the current lab3 magnitudes
    rel3 = "dashboard/src/lib/physics.js"
    txt = (ROOT / rel3).read_text(encoding="utf-8")
    m = re.search(r"lab3:\s*\{(.*?)\n  lab4:", txt, re.S)
    lab3 = m.group(1) if m else ""
    if not lab3:
        report(rel3, 1, "a", "could not locate the lab3 block")
    else:
        if "0.3 * sun" not in lab3 or "(Z2Light?100)" not in lab3:
            report(rel3, 1, "a",
                   "lab3 sandbox does not encode the current spill physics "
                   "(+100 lux / 0.30*Sun)")
        if "0.25 * sun" in lab3 or "(Z2Light?50)" in lab3:
            report(rel3, 1, "a",
                   "lab3 sandbox still encodes the superseded original spill "
                   "physics (+50 lux / 0.25*Sun)")
    # Phase-1 page must disclose the arm's cross_zone_bonus
    rel4 = "dashboard/src/pages/Phase1.jsx"
    if "cross_zone_bonus" not in (ROOT / rel4).read_text(encoding="utf-8"):
        report(rel4, 1, "c",
               "Phase-1 page presents lab3 results without a cross_zone_bonus "
               "disclosure")


def main():
    state_lines = None
    for rel in CURRENT_DOCS:
        lines = check_current_doc(rel)
        if state_lines is None:
            state_lines = lines
    for rel in HISTORICAL_DOCS:
        check_historical_doc(rel)
    check_disclosures(state_lines)
    check_dashboard()
    if violations:
        print(f"PROVENANCE CHECK FAILED - {len(violations)} violation(s):")
        for v in violations:
            print("  " + v)
        return 1
    print("provenance check OK "
          f"({len(CURRENT_DOCS) + len(HISTORICAL_DOCS)} docs + dashboard data)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
