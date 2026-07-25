"""Generate the exhaustive reachability certificates for every Phase-1b
scenario (Stage 1 gate).

For each profile in phase1b_models.PROFILES and each benchmark scenario,
builds the deterministic transition model, runs the exhaustive checker at the
frozen horizon (20 steps), and writes a self-hashed JSON certificate under
config/reachability_certificates/<profile>/scenario_<id>.json plus an index
CSV with every certificate hash and pass/fail verdict.

A failed or ambiguous certificate BLOCKS the campaign: the script exits 1 and
the registration cites the index hash, so registration cannot proceed past a
red result. Run:

    python analysis/generate_phase1b_certificates.py [--repo-root <dir>]
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from transition_checker import (  # noqa: E402
    check_scenario, result_to_certificate, certificate_passes)
import phase1b_models as models  # noqa: E402


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo-root", default=os.path.abspath(
        os.path.join(os.path.dirname(__file__), "..")))
    ap.add_argument("--out", default=None,
                    help="default: <repo-root>/config/reachability_certificates")
    args = ap.parse_args()
    out_root = args.out or os.path.join(args.repo_root, "config",
                                        "reachability_certificates")

    index_rows = []
    failures = []
    for profile in models.PROFILES:
        out_dir = os.path.join(out_root, profile)
        os.makedirs(out_dir, exist_ok=True)
        for sid, model, mech, intended_len in models.models_for_profile(
                profile, args.repo_root):
            result = check_scenario(model, horizon=models.HORIZON,
                                    intended_mechanism=mech,
                                    intended_shortest_length=intended_len)
            cert = result_to_certificate(result, {
                "profile": profile,
                "scenario_id": sid,
                "horizon": models.HORIZON,
                "physics": "phase1b_models.py frozen formulas",
            })
            ok, reason = certificate_passes(cert)
            path = os.path.join(out_dir, "scenario_%d.json" % sid)
            with open(path, "w", encoding="utf-8", newline="\n") as fh:
                json.dump(cert, fh, indent=2, sort_keys=True)
                fh.write("\n")
            index_rows.append((profile, sid, cert["certificate_sha256"],
                               "PASS" if ok else "FAIL", reason,
                               result.shortest_path_length,
                               result.shortest_sequence_count,
                               result.reachable_state_count))
            if not ok:
                failures.append((profile, sid, reason))

    index_path = os.path.join(out_root, "INDEX.csv")
    lines = ["profile,scenario_id,certificate_sha256,verdict,reason,"
             "shortest_len,shortest_count,reachable_states"]
    for row in index_rows:
        lines.append(",".join(str(x).replace(",", ";") for x in row))
    body = "\n".join(lines) + "\n"
    with open(index_path, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(body)
    index_sha = hashlib.sha256(body.encode("utf-8")).hexdigest()
    print("certificates: %d written; index sha256 = %s"
          % (len(index_rows), index_sha))
    if failures:
        for f in failures:
            print("FAIL: %s scenario %s — %s" % f)
        print("CAMPAIGN BLOCKED: %d failing certificate(s)." % len(failures))
        return 1
    print("all certificates PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
