# Knowledge-Provenance Contract (Phase 1b and later)

Status: NORMATIVE from branch `phase1b-labs-2026-07` onward.
Machine-readable companion: `config/knowledge_provenance.csv` (consumed by
`analysis/tests/test_knowledge_provenance.py`).

Every registered claim and every ontology term introduced from Phase 1b onward
MUST be assigned to exactly one of the five layers below. Registration
documents, thesis text, and results documents must use the layer's claim
wording when attributing a result to knowledge. A term missing from the CSV
may not be used in a registered campaign.

## Layers

| # | Layer | Examples | Claim wording |
|---|---|---|---|
| 1 | Paper-aligned component stereotype | component mechanism; manipulated/independent/dependent variables; connection points; direct/inverse qualitative proportionality (`elem:directProportion`, `elem:inverseProportion`) | "qualitative stereotype knowledge" |
| 2 | System/deployment topology | component instances, feeds, zone membership, power-gate arcs (`ws:powerGates`) | "topology-derived knowledge" |
| 3 | Instance/datasheet metadata | energy draw, installed capacity | "instance metadata" |
| 4 | Project-specific operational extension | rank bounds, `ws:ivMinRank`, `ws:energyCost`, `ws:behavioralDescriptionComplete`, any magnitude class (`ws:effectMagnitudeClass`) | "operational KG extension" |
| 5 | Learned enrichment | empirical effectiveness, delay, adaptive trust | "learned knowledge" |

## Binding rules

1. `ws:ivMinRank`, `ws:energyCost`, `ws:powerGates`, and any magnitude class
   must NOT be described as native terms from Ramanathan and Mayer
   (Cecconi et al. 2023 stereotype paper lineage). They are layer-2 or
   layer-4 terms.
2. `ws:ivMinRank` means exactly: *the minimum discretised IV rank at which the
   simulator produces an observable effect*. It must never be relabelled as
   "the rank at which the action can achieve the goal". A target-relative
   property, if ever needed, must be introduced as a separate term with its
   own CSV row and its own tests.
3. `elem:increases` in pre-Phase-1b TTLs is a legacy project shortcut. During
   direction discovery it is mapped to *positive qualitative direction*
   (equivalent to `elem:directProportion` for the affected DV). New TTLs use
   `elem:directProportion` / `elem:inverseProportion` directly.
4. Relevance classification (`EXPLICIT_RELEVANT`, `EXPLICIT_OTHER_DV`,
   `UNKNOWN`) is a derived classification computed from layer-1 stereotype
   content plus the layer-4 completeness marker
   `ws:behavioralDescriptionComplete`. Open-world rule: absence of the
   completeness marker yields `UNKNOWN`, never `EXPLICIT_OTHER_DV`.
   `ActionInfo.kgSilent` is a diagnostic only and is never evidence of
   irrelevance.
5. A registered claim about "what the KG contributed" must name the layer(s)
   whose terms the consuming channel actually read. Results produced by the
   extended arm (`phase1b_v2_extended`) must not be attributed to the frozen
   Phase-1 agent (`phase1b_v2_kg_frozen` / `phase1_v2_kg_only`).
6. Phase-1b direction and IV gates are action-level annotations, not a
   per-zone/per-DV map. All registered Phase-1b actions have a single relevant
   illuminance response with consistent direction/gates. Mixed multi-DV
   actions (for example, direct in one zone and inverse in another) are
   outside the implemented claim and require a new representation,
   certificates, registration, and campaign.

## Change control

- Adding a term: add the CSV row in the same commit that introduces the term
  to any TTL, query, or consumer. The provenance test fails otherwise.
- Reclassifying a term: requires an explicit dated note in this file's
  changelog below; silent edits to the CSV are a test failure (the CSV is
  hash-pinned per registration in the registration document).

## Changelog

- 2026-07-25: contract created for Phase 1b (branch `phase1b-labs-2026-07`).
- 2026-07-27: action-level direction/gate scope boundary made explicit after
  post-implementation audit; no code, archive, or result changed.
