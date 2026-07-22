from pathlib import Path

import pytest

from analysis import reproduce_phase1_v2 as reproduce


def _write(path: Path, value: str) -> None:
    path.write_text(f"metric,value\nauc_goal,{value}\n", encoding="utf-8")


def test_canonical_csv_ignores_cross_platform_float_repr_noise(tmp_path):
    expected = tmp_path / "expected.csv"
    actual = tmp_path / "actual.csv"
    _write(expected, "4.419999999999999")
    _write(actual, "4.42")
    reproduce._compare(expected, actual)


def test_canonical_csv_rejects_scientifically_different_number(tmp_path):
    expected = tmp_path / "expected.csv"
    actual = tmp_path / "actual.csv"
    _write(expected, "0.0037")
    _write(actual, "0.0038")
    with pytest.raises(ValueError, match="canonical byte comparison failed"):
        reproduce._compare(expected, actual)
