"""Structural guard for the runner allow-lists.

Two dispatches have failed pre-data because a profile or run-mode existed in
config/run_config.json but was missing from a PowerShell allow-list (the
-RunMode ValidateSet or $KnownProfiles). This test makes that class of miss a
local/CI failure instead of a wasted workflow dispatch: every run-mode profile
defined in run_config.json must appear in BOTH runners' ValidateSet, and every
dispatchable lab profile must appear in $KnownProfiles.
"""
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def _read(path):
    return (ROOT / path).read_text(encoding="utf-8-sig")


def _run_mode_validate_set(text, script_name):
    match = re.search(
        r"\[ValidateSet\(([^)]*)\)\]\s*\r?\n\s*\[string\]\$RunMode", text)
    assert match, f"{script_name}: could not locate the -RunMode ValidateSet"
    return set(re.findall(r'"([^"]+)"', match.group(1)))


def _known_profiles(text, script_name):
    match = re.search(r"\$KnownProfiles\s*=\s*@\(([^)]*)\)", text, re.DOTALL)
    assert match, f"{script_name}: could not locate $KnownProfiles"
    return set(re.findall(r'"([^"]+)"', match.group(1)))


def _config():
    return json.loads(_read("config/run_config.json"))


def test_every_config_run_mode_is_in_both_validate_sets():
    config_modes = set(_config()["profiles"])
    for script in ("run_full_project.ps1", "run_full_project_parallel.ps1"):
        allowed = _run_mode_validate_set(_read(script), script)
        missing = sorted(config_modes - allowed)
        assert not missing, (
            f"{script}: run modes defined in config/run_config.json but missing "
            f"from the -RunMode ValidateSet: {missing}")


def test_every_dispatchable_profile_is_in_known_profiles():
    cfg = _config()
    dispatchable = set(cfg.get("profiles_to_run", []))
    dispatchable |= set(cfg["phase4"]["phase4_profiles"])
    dispatchable |= set(cfg["phase2"]["parent_profile"].values())
    known = _known_profiles(_read("run_full_project.ps1"), "run_full_project.ps1")
    missing = sorted(dispatchable - known)
    assert not missing, (
        "run_full_project.ps1: profiles referenced by run_config.json but "
        f"missing from $KnownProfiles: {missing}")


def test_every_trainable_profile_resolves_a_scenario_file():
    """The 2026-07-22 Phase-2 dispatches failed pre-data because a variant
    parent profile (labmon2_infoonly) had no name-derived scenario file. Every
    profile a protocol-v2 training cell can run must resolve to an existing
    train_scenarios JSON, via its own name or the train_scenarios_alias map."""
    cfg = _config()
    alias = cfg.get("train_scenarios_alias", {})
    trainable = set(cfg.get("profiles_to_run", []))
    trainable |= set(cfg["phase4"]["phase4_profiles"])
    trainable |= set(cfg["phase2"]["parent_profile"].values())
    missing = []
    for profile in sorted(trainable):
        base = alias.get(profile, profile)
        if not (ROOT / "benchmark" / f"train_scenarios_{base}.json").is_file():
            missing.append(f"{profile} -> train_scenarios_{base}.json")
    assert not missing, (
        "profiles without a resolvable protocol-v2 scenario file "
        f"(add benchmark file or train_scenarios_alias entry): {missing}")
