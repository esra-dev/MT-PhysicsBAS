"""Phase-3 protocol-v2 energy contract at the analysis boundary.

The corrected exploit schema carries tick_energy (deterministic per-attempt
accumulator delta over simulator ticks) and relabels the withdrawn cumulative
wall-clock read as energy_cost_wallclock_legacy. The aggregator must sum
tick_energy as the energy descriptive and keep the legacy column as a
diagnostic only (with a read-fallback for old archives' energy_cost name).
"""
from pathlib import Path

from analysis import phase3_dynamics

V2_HEADER = ("profile,mode,goal_id,zone,target_rank,deadline_sec,chosen_label,"
             "believed_delay_sec,learned_delay_sec,actual_delay_sec,"
             "tick_energy,tick_span,energy_cost_wallclock_legacy,energy_meter,met")


def _write(root: Path, rep: int, name: str, header: str, rows: list[str]) -> None:
    rep_dir = root / f"rep{rep}"
    rep_dir.mkdir(parents=True, exist_ok=True)
    (rep_dir / name).write_text("\n".join([header, *rows]) + "\n", encoding="utf-8")


def test_v2_schema_sums_tick_energy_and_keeps_legacy_separate(tmp_path):
    _write(tmp_path, 1, "timebounded_results_true_lab2_slow.csv", V2_HEADER, [
        "lab2_slow,ql_true,g1,1,3,15.00,SetZ1Light=true,0.00,0.00,5.00,3.00,1,120.00,tick-v1,1",
        "lab2_slow,ql_true,g2,1,3,90.00,SetZ1Blinds=true,60.00,60.10,60.00,0.00,12,150.00,tick-v1,1",
    ])
    out = phase3_dynamics.collect_compliance(tmp_path, "true", "lab2_slow", 60.0)
    assert out["n_replicas"] == 1
    assert out["total_tick_energy"] == [3.0]
    assert out["total_energy_wallclock_legacy"] == [270.0]
    assert out["overall_compliance"] == [1.0]


def test_legacy_archive_column_feeds_only_the_diagnostic(tmp_path):
    legacy_header = ("profile,mode,goal_id,zone,target_rank,deadline_sec,chosen_label,"
                     "believed_delay_sec,learned_delay_sec,actual_delay_sec,energy_cost,met")
    _write(tmp_path, 1, "timebounded_results_false_lab2_slow.csv", legacy_header, [
        "lab2_slow,ql_false,g1,1,3,15.00,SetZ1Light=true,0.00,0.00,5.00,42.00,1",
    ])
    out = phase3_dynamics.collect_compliance(tmp_path, "false", "lab2_slow", 60.0)
    assert out["total_tick_energy"] == [0.0]
    assert out["total_energy_wallclock_legacy"] == [42.0]
