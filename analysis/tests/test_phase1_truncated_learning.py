import csv

import pytest

from analysis import phase1_truncated_learning as ptl


def _metrics(goals, scenarios):
    return ptl.EpisodeMetrics(tuple(goals), tuple(scenarios))


def test_prefix_auc_accepts_near_balanced_cyclic_scenario_prefix():
    metrics = _metrics([1, 0, 1, 1, 0, 0], ["a", "b", "a", "b", "a", "b"])
    assert ptl.prefix_auc(metrics, 4, 2) == pytest.approx(0.75)
    assert ptl.prefix_auc(metrics, 3, 2) == pytest.approx(2 / 3)


def test_prefix_auc_rejects_noncyclic_scenario_imbalance():
    metrics = _metrics([1, 1, 0, 0], ["a", "a", "a", "b"])
    with pytest.raises(ValueError, match="near-balanced"):
        ptl.prefix_auc(metrics, 4, 2)


def test_trailing_training_goal_rate_uses_requested_prefix_window():
    metrics = _metrics([0, 0, 1, 0, 1, 1], ["a"] * 6)
    assert ptl.trailing_training_goal_rate(metrics, 5, 3) == pytest.approx(2 / 3)
    with pytest.raises(ValueError, match="window"):
        ptl.trailing_training_goal_rate(metrics, 2, 3)


def test_read_episode_metrics_rejects_noncontiguous_episodes(tmp_path):
    path = tmp_path / "metrics.csv"
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(["Episode", "GoalReached", "ScenarioId"])
        writer.writerow([0, 1, 1])
        writer.writerow([2, 0, 2])
    with pytest.raises(ValueError, match="contiguous"):
        ptl.read_episode_metrics(path, 2)


def test_read_episode_metrics_accepts_footer_after_fixed_horizon(tmp_path):
    path = tmp_path / "metrics.csv"
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(["Episode", "GoalReached", "ScenarioId"])
        writer.writerow([0, 1, 1])
        writer.writerow([1, 0, 2])
        writer.writerow(["# Summary"])
        writer.writerow(["FirstGoalEpisode", 0])
    result = ptl.read_episode_metrics(path, 2)
    assert result.goals == (1, 0)


def test_derived_contrast_is_paired_difference_in_differences():
    spec = {
        "budgets": [10],
        "endpoints": [{"name": "prefix_auc_goal"}],
        "profiles": {"lab": {}},
        "derived_contrast": {
            "name": "kg_minus_redundancy",
            "left": "kg_vs_baseline",
            "right": "redundancy_vs_baseline",
        },
    }
    rows = []
    for seed in ptl.EXPECTED_SEEDS:
        rows.extend([
            {"profile": "lab", "contrast": "kg_vs_baseline", "endpoint": "prefix_auc_goal", "budget": 10,
             "seed": seed, "left_value": 0.8, "right_value": 0.5,
             "paired_difference": 0.3},
            {"profile": "lab", "contrast": "redundancy_vs_baseline", "endpoint": "prefix_auc_goal", "budget": 10,
             "seed": seed, "left_value": 0.7, "right_value": 0.5,
             "paired_difference": 0.2},
        ])
    combined = ptl.add_derived_rows(spec, rows)
    derived = [row for row in combined if row["contrast"] == "kg_minus_redundancy"]
    assert len(derived) == 20
    assert all(row["paired_difference"] == pytest.approx(0.1) for row in derived)


def test_summary_applies_historical_reference_only_to_kg_contrast():
    spec = {
        "bootstrap": {"iterations": 100, "base_seed": 7},
        "historical_auc_reference": {"value": 0.0111},
    }
    rows = []
    for contrast in ("kg_vs_baseline", "redundancy_vs_baseline"):
        for seed in ptl.EXPECTED_SEEDS:
            rows.append({
                "profile": "lab", "contrast": contrast, "endpoint": "prefix_auc_goal", "budget": 150,
                "seed": seed, "left_value": 0.7, "right_value": 0.68,
                "paired_difference": 0.02,
            })
    for seed in ptl.EXPECTED_SEEDS:
        rows.append({
            "profile": "lab", "contrast": "kg_vs_baseline",
            "endpoint": "trailing_training_goal_rate", "budget": 150,
            "seed": seed, "left_value": 0.9, "right_value": 0.85,
            "paired_difference": 0.05,
        })
    summaries = ptl.summarize_rows(spec, rows)
    kg = next(
        row for row in summaries
        if row["contrast"] == "kg_vs_baseline"
        and row["endpoint"] == "prefix_auc_goal"
    )
    redundancy = next(
        row for row in summaries if row["contrast"] == "redundancy_vs_baseline"
    )
    trailing = next(
        row for row in summaries
        if row["endpoint"] == "trailing_training_goal_rate"
    )
    assert kg["mean_crosses_historical_reference"] is True
    assert kg["mean_cumulative_excess_goals"] == pytest.approx(3.0)
    assert redundancy["historical_auc_reference"] is None
    assert redundancy["mean_crosses_historical_reference"] is None
    assert trailing["historical_auc_reference"] is None
    assert trailing["mean_cumulative_excess_goals"] is None


def test_assessment_does_not_call_nonmonotone_curve_monotone():
    spec = {"training_horizon": 3000}
    summaries = []
    for budget, mean in [(150, 0.02), (300, 0.01), (750, 0.015), (3000, 0.005)]:
        summaries.append({
            "profile": "lab", "contrast": "kg_vs_baseline", "endpoint": "prefix_auc_goal", "budget": budget,
            "mean_paired_difference": mean,
            "bootstrap_ci_low_descriptive": 0.001,
            "mean_crosses_historical_reference": mean >= 0.0111,
        })
    result = ptl.assess_profiles(spec, summaries)[0]
    assert result["mean_curve_monotone_nonincreasing"] is False
    assert result["short_budgets_crossing_historical_reference"] == "150;750"
    assert result["screening_label"] == (
        "plausible_short_budget_signal_above_historical_anchor"
    )
