"""Contract: every `-P<key>=` the runner emits must be forwarded by Gradle.

Audit AUD-001 (round 1): `run_full_project.ps1` passed the three Phase-1b
extended knobs as Gradle project properties, but `build.gradle` only turns an
allow-listed set of names (`_httpKeys`) into JVM system properties, and
`StereotypeReasoner` reads system properties with 0.0 defaults. The archived
"extended" runs therefore executed effective frozen KG. This test fails
locally and in CI whenever a runner-emitted property name is missing from the
allow-list, and it pins the effective-value evidence chain: the reasoner must
log the knob values under a fixed marker, and the runner must parse that
marker and record it in TRAINING_OK.json.
"""

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def _read(rel):
    return (ROOT / rel).read_text(encoding="utf-8-sig")


def _http_keys():
    text = _read("build.gradle")
    match = re.search(r"def _httpKeys = \[(.*?)\]", text, re.DOTALL)
    assert match, "build.gradle: could not locate the _httpKeys allow-list"
    body = re.sub(r"//[^\n]*", "", match.group(1))
    return set(re.findall(r"'([^']+)'", body))


def _runner_property_names():
    text = _read("run_full_project.ps1")
    return set(re.findall(r'\$HttpArgs \+= "-P([A-Za-z0-9_.]+)=', text))


def test_every_runner_property_is_in_the_gradle_allow_list():
    missing = sorted(_runner_property_names() - _http_keys())
    assert not missing, (
        "run_full_project.ps1 emits Gradle properties that build.gradle never "
        f"forwards to the JVM (silent treatment non-delivery): {missing}")


def test_phase1b_extended_knobs_are_forwarded():
    keys = _http_keys()
    for name in ("stereo.irrelevantDvPrior", "stereo.bandMirrorInit",
                 "stereo.bandMirrorPrior"):
        assert name in keys, f"{name} missing from build.gradle _httpKeys"


def test_reasoner_reports_effective_knobs_and_runner_records_them():
    java = _read("src/env/tools/StereotypeReasoner.java")
    assert 'EFFECTIVE_PROPS_MARKER = "STEREO_EFFECTIVE_PROPS"' in java
    for name in ("stereo.irrelevantDvPrior", "stereo.bandMirrorInit",
                 "stereo.bandMirrorPrior"):
        assert f'\\"{name}\\":' in java, f"effectivePropsJson() does not report {name}"
    runner = _read("run_full_project.ps1")
    assert "STEREO_EFFECTIVE_PROPS" in runner
    assert "stereo_effective_props = $effectiveStereoProps" in runner
    assert "stereo_requested_props = $RequestedStereoProps" in runner
    # The gate must run BEFORE the manifest is written (manifest after gate).
    assert runner.index("Get-EffectiveStereoProps -LogPath") < runner.index(
        "stereo_effective_props = $effectiveStereoProps")


def test_extended_mode_requests_exactly_the_registered_values():
    import json
    cfg = json.loads(_read("config/run_config.json"))
    overrides = cfg["profiles"]["phase1b_v2_extended"]["learning_overrides"]
    assert overrides["stereo_irrelevant_dv_prior"] == 2.0
    assert overrides["stereo_band_mirror_init"] == 5.0
    assert overrides["stereo_band_mirror_prior"] == 2.0
    frozen = cfg["profiles"]["phase1b_v2_kg_frozen"].get("learning_overrides", {})
    for key in ("stereo_irrelevant_dv_prior", "stereo_band_mirror_init",
                "stereo_band_mirror_prior"):
        assert key not in frozen, f"frozen mode must never set {key}"
