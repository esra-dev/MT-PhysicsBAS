"""Knowledge-provenance contract checks (Phase 1b Stage 0).

Guards docs/KNOWLEDGE_PROVENANCE.md + config/knowledge_provenance.csv:
every operational-extension term actually used by the committed building TTLs
must be classified in the CSV, and the CSV itself must stay well-formed.
"""

import csv
import os
import re

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
CSV_PATH = os.path.join(ROOT, "config", "knowledge_provenance.csv")
RESOURCES = os.path.join(ROOT, "src", "resources")

VALID_LAYERS = {"1", "2", "3", "4", "5", "derived"}

# ws:/elem: predicates that carry knowledge semantics and therefore need a
# provenance row when they appear in any building TTL. Purely structural
# plumbing (WoT mappings, state-slot registry, labels, rank bounds duplicated
# from the ASL) is deliberately out of scope.
TRACKED_PREDICATES = [
    "ws:ivMinRank",
    "ws:energyCost",
    "ws:powerGates",
    "ws:behavioralDescriptionComplete",
    "ws:gateWoTStateSemanticType",
    "ws:gateMinValue",
    "ws:effectMagnitudeClass",
    "elem:increases",
    "elem:directProportion",
    "elem:inverseProportion",
]


def _rows():
    with open(CSV_PATH, encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def test_csv_is_well_formed_and_layers_valid():
    rows = _rows()
    assert rows, "provenance CSV must not be empty"
    seen = set()
    for r in rows:
        assert r["term"], "every row needs a term"
        assert r["term"] not in seen, "duplicate term: %s" % r["term"]
        seen.add(r["term"])
        assert r["layer"] in VALID_LAYERS, \
            "invalid layer %r for %s" % (r["layer"], r["term"])
        assert r["claim_wording"], "claim wording required for %s" % r["term"]


def test_phase1b_terms_are_classified():
    terms = {r["term"] for r in _rows()}
    for required in [
        "elem:directProportion", "elem:inverseProportion", "elem:increases",
        "ws:behavioralDescriptionComplete", "ws:gateWoTStateSemanticType",
        "ws:gateMinValue", "ws:ivMinRank", "ws:energyCost", "ws:powerGates",
        "relevance:EXPLICIT_RELEVANT", "relevance:EXPLICIT_OTHER_DV",
        "relevance:UNKNOWN", "ActionInfo.kgSilent",
    ]:
        assert required in terms, "provenance CSV missing %s" % required


def test_operational_terms_are_never_paper_aligned():
    rows = {r["term"]: r for r in _rows()}
    for term in ["ws:ivMinRank", "ws:energyCost", "ws:effectMagnitudeClass",
                 "ws:behavioralDescriptionComplete", "ws:gateWoTStateSemanticType",
                 "ws:gateMinValue"]:
        assert rows[term]["layer"] == "4", \
            "%s must stay an operational KG extension (layer 4)" % term
    assert rows["ws:powerGates"]["layer"] == "2", \
        "ws:powerGates is system topology (layer 2)"


def test_every_tracked_predicate_in_ttls_is_classified():
    terms = {r["term"] for r in _rows()}
    used = set()
    for name in sorted(os.listdir(RESOURCES)):
        if not name.endswith(".ttl"):
            continue
        with open(os.path.join(RESOURCES, name), encoding="utf-8") as fh:
            body = fh.read()
        # strip comments so prose mentions don't count as usage
        body = re.sub(r"#[^\n]*", "", body)
        for pred in TRACKED_PREDICATES:
            if re.search(r"(?<![\w:])" + re.escape(pred) + r"(?![\w])", body):
                used.add(pred)
    missing = sorted(used - terms)
    assert not missing, \
        "TTL-used knowledge terms missing from provenance CSV: %s" % missing
