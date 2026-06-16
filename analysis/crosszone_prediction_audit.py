#!/usr/bin/env python3
"""
crosszone_prediction_audit.py
=============================

Tiny, dependency-free audit that turns the lab3 "magnitude-blind KG prior"
argument into a hard number.

Background
----------
In lab3 the knowledge graph (src/resources/building_3_complex.ttl, section 7)
declares *cross-zone* spill arcs:

    CeilingLight_Z1  brick:feeds  LightSensor_Z2      (+50 lux bleed)
    CeilingLight_Z2  brick:feeds  LightSensor_Z1      (+50 lux bleed)
    Blind_Z1         brick:feeds  LightSensor_Z2      (+0.25*Sun bleed)
    Blind_Z2         brick:feeds  LightSensor_Z1      (+0.25*Sun bleed)

StereotypeReasoner.getActionPrediction() converts every arc into a
*direction-only* prediction: activating an actuator is predicted to push the
*other* zone's illuminance in the SAME direction as its own zone
(`dir = wotValue ? +1 : -1`) with NO magnitude. But the simulator quantises
illuminance into 4 ranks (discretize bounds [50,100,300]), and the cross-zone
bleed (<=+50 lux for lamps, 0.25*Sun for blinds) is almost always sub-rank: it
does NOT move the neighbour's rank. So the prior systematically *over-claims* a
cross-zone rank change reality does not produce.

This script measures how often the KG cross-zone prediction sign disagrees
with the actual neighbour rank change, two ways:

  (A) STRUCTURAL (primary, recommended): exhaustively enumerate the full lab3
      transition space from the deterministic physics equations + the exact
      `discretize` rank function. Unbiased by which states a policy happens to
      visit; this is the clean number for the thesis.

  (B) EMPIRICAL (secondary): replay the persisted per-step bench logs
      (bench_step_log_<mode>.csv). NOTE: these are *converged-policy
      evaluation* steps, dominated by at-goal holding where almost no actuation
      changes any rank, so BOTH primary and cross-zone mismatch saturate near
      100%. Reported only as a cross-check, not the headline instrument.

Physics (building_3_complex.ttl header, port 1894):
  Z1 = 25 + (Z1Light?400:0) + (Z2Light?50:0)
          + (Z1Blinds?0.50*Sun:0) + (Z2Blinds?0.25*Sun:0) + (Spotlight?150:0)
  Z2 = 25 + (Z2Light?400:0) + (Z1Light?50:0)
          + (Z2Blinds?0.50*Sun:0) + (Z1Blinds?0.25*Sun:0) + (Spotlight?150:0)
  Sun in {0,100,400,900} (sampled once per episode and pinned).

Usage
-----
    python analysis/crosszone_prediction_audit.py            # structural + logs
    python analysis/crosszone_prediction_audit.py --structural-only
    python analysis/crosszone_prediction_audit.py --secondary-zero  # model Part-A fix
"""

import csv
import os
import sys
from collections import defaultdict
from itertools import product

# --- lab3 ground truth ------------------------------------------------------
LIGHT_BOUNDS = (50.0, 100.0, 300.0)   # lab_profiles.asl lab3 light_bounds
SUN_VALUES = (0, 100, 400, 900)       # building_3_complex.ttl sampling set

# actuator base name -> the OTHER zone its spill feeds (1-based).
CROSS_ZONE_FEED = {"Z1Light": 2, "Z2Light": 1, "Z1Blinds": 2, "Z2Blinds": 1}
PRIMARY_ZONE = {"Z1Light": 1, "Z2Light": 2, "Z1Blinds": 1, "Z2Blinds": 2}
# Spotlight is a SHARED actuator (primary on both zones), not a spill arc, so it
# is excluded from the cross-zone test by construction.

ACTUATORS = ["Z1Light", "Z2Light", "Z1Blinds", "Z2Blinds", "Spotlight"]


def discretize(value):
    """Exact replica of LabEnvironment.discretize for lab3 bounds."""
    if value < LIGHT_BOUNDS[0]:
        return 0
    if value < LIGHT_BOUNDS[1]:
        return 1
    if value < LIGHT_BOUNDS[2]:
        return 2
    return 3


def levels(cfg):
    """cfg = dict of actuator bits + 'Sun'. Returns (Z1lux, Z2lux)."""
    s = cfg["Sun"]
    z1 = (25 + (400 if cfg["Z1Light"] else 0) + (50 if cfg["Z2Light"] else 0)
          + (0.50 * s if cfg["Z1Blinds"] else 0)
          + (0.25 * s if cfg["Z2Blinds"] else 0)
          + (150 if cfg["Spotlight"] else 0))
    z2 = (25 + (400 if cfg["Z2Light"] else 0) + (50 if cfg["Z1Light"] else 0)
          + (0.50 * s if cfg["Z2Blinds"] else 0)
          + (0.25 * s if cfg["Z1Blinds"] else 0)
          + (150 if cfg["Spotlight"] else 0))
    return z1, z2


def sign(x):
    return (x > 0) - (x < 0)


def pct(d):
    return 100.0 * d["miss"] / d["n"] if d["n"] else float("nan")


# ---------------------------------------------------------------------------
# (A) Structural enumeration
# ---------------------------------------------------------------------------
def structural_audit(secondary_zero=False):
    primary = defaultdict(lambda: {"n": 0, "miss": 0})
    cross = defaultdict(lambda: {"n": 0, "miss": 0})
    for bits in product([0, 1], repeat=len(ACTUATORS)):
        base = dict(zip(ACTUATORS, bits))
        for sun in SUN_VALUES:
            base["Sun"] = sun
            for act in CROSS_ZONE_FEED:
                if base[act] == 1:
                    continue  # only score the off->on toggle (on->off is mirror)
                off = dict(base)
                on = dict(base, **{act: 1})
                ro = (discretize(levels(off)[0]), discretize(levels(off)[1]))
                rn = (discretize(levels(on)[0]), discretize(levels(on)[1]))
                predicted = +1  # activation -> KG predicts +1 on affected slots
                pz = PRIMARY_ZONE[act] - 1
                primary[act]["n"] += 1
                if sign(rn[pz] - ro[pz]) != predicted:
                    primary[act]["miss"] += 1
                # CROSS-ZONE arc. With --secondary-zero we model the Part-A fix:
                # the ws:WeakOpticalCoupling arc emits 0 (no rank claim), so it
                # is NEVER scored as a claim (the adaptive-trust calibration in
                # QLearner.calculateQ skips predSign==0). Without the flag we
                # score the legacy +1 over-claim.
                if not secondary_zero:
                    cz = CROSS_ZONE_FEED[act] - 1
                    cross[act]["n"] += 1
                    if sign(rn[cz] - ro[cz]) != predicted:
                        cross[act]["miss"] += 1
    return primary, cross


def report_structural(secondary_zero=False):
    primary, cross = structural_audit(secondary_zero=secondary_zero)
    p_tot = {"n": sum(d["n"] for d in primary.values()),
             "miss": sum(d["miss"] for d in primary.values())}
    c_tot = {"n": sum(d["n"] for d in cross.values()),
             "miss": sum(d["miss"] for d in cross.values())}
    lamp = {"n": cross["Z1Light"]["n"] + cross["Z2Light"]["n"],
            "miss": cross["Z1Light"]["miss"] + cross["Z2Light"]["miss"]}
    blind = {"n": cross["Z1Blinds"]["n"] + cross["Z2Blinds"]["n"],
             "miss": cross["Z1Blinds"]["miss"] + cross["Z2Blinds"]["miss"]}

    print("=" * 70)
    print("(A) STRUCTURAL AUDIT - exhaustive over the lab3 transition space")
    print("    (deterministic physics x discretize bounds [50,100,300];")
    print("     all 32 actuator configs x 4 sun levels, off->on toggles)")
    print("-" * 70)
    print("SAME-ZONE (primary) prediction realised?")
    for act in CROSS_ZONE_FEED:
        d = primary[act]
        print(f"  {act:9s} -> Z{PRIMARY_ZONE[act]} (self): "
              f"WRONG {d['miss']:3d}/{d['n']:3d} = {pct(d):5.1f}%")
    print(f"  {'POOLED':9s}            : WRONG {p_tot['miss']:3d}/{p_tot['n']:3d}"
          f" = {pct(p_tot):5.1f}%")
    print()
    print("CROSS-ZONE (spill) prediction realised?  [KG predicts +1 on nbr]")
    if secondary_zero:
        print("  (Part-A fix active: ws:WeakOpticalCoupling arcs emit NO rank")
        print("   claim -> 0 cross-zone claims scored, so cannot be 'wrong')")
    else:
        for act in CROSS_ZONE_FEED:
            d = cross[act]
            print(f"  {act:9s} -> Z{CROSS_ZONE_FEED[act]} (nbr) : "
                  f"WRONG {d['miss']:3d}/{d['n']:3d} = {pct(d):5.1f}%")
        print(f"  lamp spill (+50 lux)   : WRONG {lamp['miss']:3d}/{lamp['n']:3d}"
              f" = {pct(lamp):5.1f}%")
        print(f"  blind spill (0.25*Sun) : WRONG {blind['miss']:3d}/{blind['n']:3d}"
              f" = {pct(blind):5.1f}%")
        print(f"  {'POOLED':9s}            : WRONG {c_tot['miss']:3d}/{c_tot['n']:3d}"
              f" = {pct(c_tot):5.1f}%")
    print("-" * 70)
    if secondary_zero:
        _, base_cross = structural_audit(secondary_zero=False)
        bc = {"n": sum(d["n"] for d in base_cross.values()),
              "miss": sum(d["miss"] for d in base_cross.values())}
        print("MODE --secondary-zero: models the Part-A fix (WeakOpticalCoupling")
        print("     arcs make no rank prediction).")
        print(f"HEADLINE: cross-zone now makes 0 rank claims (legacy reasoner was")
        print(f"          WRONG {pct(bc):.1f}% of the time), so it can no longer")
        print("          deflate the adaptive-trust calibration for the action.")
    else:
        print(f"HEADLINE: cross-zone prediction is WRONG {pct(c_tot):.1f}% of the "
              f"time vs {pct(p_tot):.1f}% for same-zone.")
    print("=" * 70)


# ---------------------------------------------------------------------------
# (B) Empirical replay of bench step logs (cross-check only)
# ---------------------------------------------------------------------------
def parse_action(label):
    label = label.replace("http://example.org/was#", "")
    if not label.startswith("Set") or "=" not in label:
        return None, None
    name, val = label[3:].split("=", 1)
    if name not in PRIMARY_ZONE:
        return None, None
    return name, (1 if val.strip().lower() == "true" else -1)


def rank_col(row, col):
    v = row.get(col, "")
    return int(v) if v not in ("", None) else None


def empirical_audit(path):
    primary = {"n": 0, "miss": 0}
    cross = {"n": 0, "miss": 0}
    with open(path, newline="") as fh:
        for row in csv.DictReader(fh):
            base, direction = parse_action(row["ActionLabel"])
            if base is None:
                continue
            pz, cz = PRIMARY_ZONE[base], CROSS_ZONE_FEED[base]
            pb, pa = rank_col(row, f"Z{pz}Before"), rank_col(row, f"Z{pz}After")
            cb, ca = rank_col(row, f"Z{cz}Before"), rank_col(row, f"Z{cz}After")
            if pb is not None and pa is not None:
                primary["n"] += 1
                if sign(direction) != sign(pa - pb):
                    primary["miss"] += 1
            if cb is not None and ca is not None:
                cross["n"] += 1
                if sign(direction) != sign(ca - cb):
                    cross["miss"] += 1
    return primary, cross


def report_empirical(files):
    gp = {"n": 0, "miss": 0}
    gc = {"n": 0, "miss": 0}
    any_found = False
    print()
    print("=" * 70)
    print("(B) EMPIRICAL CROSS-CHECK - persisted bench step logs")
    print("    CAVEAT: converged-policy evaluation (mostly at-goal holds), so")
    print("    primary mismatch also saturates; not the headline instrument.")
    print("-" * 70)
    for f in files:
        if not os.path.exists(f):
            continue
        any_found = True
        p, c = empirical_audit(f)
        gp["n"] += p["n"]; gp["miss"] += p["miss"]
        gc["n"] += c["n"]; gc["miss"] += c["miss"]
        print(f"  {os.path.basename(f):30s} "
              f"primary {pct(p):5.1f}% ({p['miss']}/{p['n']})  |  "
              f"cross {pct(c):5.1f}% ({c['miss']}/{c['n']})")
    if any_found:
        print(f"  {'POOLED':30s} "
              f"primary {pct(gp):5.1f}% ({gp['miss']}/{gp['n']})  |  "
              f"cross {pct(gc):5.1f}% ({gc['miss']}/{gc['n']})")
    else:
        print("  (no bench_step_log_*.csv found)")
    print("=" * 70)


def main(argv):
    secondary_zero = "--secondary-zero" in argv
    report_structural(secondary_zero=secondary_zero)
    if "--structural-only" not in argv:
        report_empirical([
            "bench_step_log_ql_true.csv",
            "bench_step_log_ql_false.csv",
        ])
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
