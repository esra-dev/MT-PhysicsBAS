"""One-shot builder for the committed Phase-1b registered tables.

Stages the eight validated seed-half archives into four mode roots (reusing
reproduce_phase1b's discovery/validation/staging) and runs the frozen
phase1b_report builder into phase1b_corrected/analysis/registered/.
After this, analysis/reproduce_phase1b.py must byte-reproduce these tables.
"""
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "analysis"))

from reproduce_phase1b import _discover, _stage_mode_root, REPORT_SCRIPT  # noqa: E402
from validate_phase1b_archive import validate  # noqa: E402

campaign = ROOT / "phase1b_corrected"
archives = _discover(campaign)
for mode, halves in sorted(archives.items()):
    for archive in halves:
        errors = validate(archive, stage="confirmatory")
        if errors:
            raise SystemExit(f"{mode} {archive} failed validation:\n" + "\n".join(errors))
print("all archives validate (confirmatory)")

with tempfile.TemporaryDirectory(prefix="phase1b-build-") as temp:
    roots = Path(temp) / "modes"
    for mode, halves in sorted(archives.items()):
        for archive in halves:
            _stage_mode_root(archive, roots / mode)
    out = campaign / "analysis" / "registered"
    out.mkdir(parents=True, exist_ok=True)
    subprocess.run([sys.executable, str(REPORT_SCRIPT),
                    "--roots", str(roots), "--out", str(out)], check=True)
print("registered tables written to", out)
