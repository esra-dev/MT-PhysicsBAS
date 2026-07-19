"""Test A — §5.4.1 residual-init-Q toggling micro-mechanism audit.

Registered pre-data in THESIS_STATE_REPORT Addendum 2026-07-18c §1 (commit
02ed6c1). Implements the registered gates (G1-G3, minimum data), scope gate
S1, and predictions P1-P3 exactly as written there; no free parameters beyond
that registration. Deterministic: fixed MC seed 20260718, 100 000 draws,
stdlib only.

Data (run of record 29639767776, lab3, seeds 1-10, both arms), committed under
phase1_postinv/run_29639767776_toggling_audit/inputs/ (retrieved from CI
artifact 8428536694, sha256 4029c693..., = `results` branch publish commit
077541b content for this run):

  results_seed<n>/lab3/<mode>/bench_step_log_<mode>.csv      rich step log
  results_seed<n>/lab3/<mode>/benchmark_results_<mode>.csv   G1 reference
  results_seed<n>/lab3/<mode>/qtable_final_stereotypes_<arm>_lab3.csv
                                                (+_zone1/_zone2/_visits.csv)

Initial-table inputs (G3/P2) are the headless regenerations at archive head
e631877 under regen_init/regen_A and regen_B (InitDumpHarness.java in
harness/; run.seed=101 vs 202), plus the state-slot registry dump
state_layout.json. The regenerated combined table is additionally
content-identical (LF-normalised) to the run's own archived
qtable_initial_stereotypes_true_lab3.csv on the results branch.

Definitions (registration §1):
  D1 cycling event  — any actuator state change between consecutive recorded
                      steps, from the second recorded step of an episode on
                      (instrument semantics, BenchmarkLogger.countReversals).
  D2 toggle event   — a D1 event returning the flipped actuator to a value it
                      already held earlier in the same episode (snapshots are
                      the post-action ActuatorState columns of the episode).
  D3 greedy toggle  — D2 with StuckFired=0 and WasMasked=0 on the step row.
  D4 toggle pair    — (encoded state, executed action) of a D3 event; state
                      reconstructed from zone ranks before + SunshineRank +
                      the PREVIOUS step's ActuatorState through the exact
                      encodeState slot layout; deduplicated within a seed,
                      pooled across seeds (one realization per seed).

Output: phase1_postinv/run_29639767776_toggling_audit/out/
  audit_results.json, SUMMARY.md, toggle_events_<mode>.csv,
  toggle_pairs_ql_true.csv, g1_reconciliation.csv, g2_failures.csv
"""

import csv
import hashlib
import json
import random
import statistics
from collections import defaultdict
from pathlib import Path

ROOT   = Path(__file__).resolve().parent.parent
AUDIT  = ROOT / "phase1_postinv" / "run_29639767776_toggling_audit"
INPUTS = AUDIT / "inputs"
REGEN  = AUDIT / "regen_init"
OUT    = AUDIT / "out"

SEEDS      = list(range(1, 11))
MODES      = {"ql_true": "true", "ql_false": "false"}
N_ACTIONS  = 11
TIE_EPS    = 1e-9
MC_DRAWS   = 100_000
MC_SEED    = 20260718
P1_MAX_MEDIAN_VISITS = 5      # "a handful", §5.4.1
P2_MARGIN  = 0.20
GATE_FRAC  = 0.95
MIN_PAIRS  = 20

# State-slot layout for lab3 (regen_init/regen_A/state_layout.json, dumped by
# the harness from the e631877 slot registry; combined table verified
# content-identical to the run's own archived initial dump):
#   slots [Z1Level, Z2Level, Z1Light, Z2Light, Z1Blinds, Z2Blinds, Spotlight,
#   sunshine], domain [4,4,2,2,2,2,2,4] -> strides [512,128,64,32,16,8,4,1].
STRIDES        = [512, 128, 64, 32, 16, 8, 4, 1]
ACTUATOR_SLOT  = {"Z1Light": 2, "Z2Light": 3, "Z1Blinds": 4,
                  "Z2Blinds": 5, "Spotlight": 6}


# ---------------------------------------------------------------- loaders --

def load_layout():
    with open(REGEN / "regen_A" / "state_layout.json", encoding="utf-8") as f:
        return json.load(f)


def action_maps(layout):
    """-> (label list by index, {(wotActionType, bool_value): index})"""
    labels = [None] * N_ACTIONS
    by_wot = {}
    for a in layout["actions"]:
        labels[a["index"]] = a["label"]
        if a["wotActionType"]:
            by_wot[(a["wotActionType"], a["wotValue"])] = a["index"]
        else:
            by_wot[("DO_NOTHING", False)] = a["index"]
    return labels, by_wot


def map_action_label(label, by_wot):
    """Step-log ActionLabel -> action index, or None if unmappable."""
    if label == "DO_NOTHING":
        return by_wot[("DO_NOTHING", False)]
    if "=" not in label:
        return None
    uri, _, val = label.rpartition("=")
    if val not in ("true", "false"):
        return None
    return by_wot.get((uri, val == "true"))


def read_qtable(path):
    """qtable CSV -> {state_idx: [float per action]} (absent row = all zero)."""
    table = {}
    with open(path, newline="", encoding="utf-8") as f:
        r = csv.reader(f)
        next(r)
        for line in r:
            if not line:
                continue
            table[int(line[0])] = [float(x) for x in line[1:]]
    return table


def read_visits(path):
    table = {}
    with open(path, newline="", encoding="utf-8") as f:
        r = csv.reader(f)
        next(r)
        for line in r:
            if not line:
                continue
            table[int(line[0])] = [int(x) for x in line[1:]]
    return table


def parse_actuators(s):
    """'Z1Blinds=false;Spotlight=true' -> {name: bool}"""
    out = {}
    for part in s.split(";"):
        if "=" not in part:
            continue
        k, _, v = part.partition("=")
        out[k] = (v == "true")
    return out


def read_step_log(path):
    """-> {(scenario, run): [row dicts sorted by step]}"""
    episodes = defaultdict(list)
    with open(path, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            episodes[(int(row["ScenarioId"]), int(row["RunId"]))].append({
                "step":  int(row["Step"]),
                "z1":    int(row["Z1Before"]),
                "z2":    int(row["Z2Before"]),
                "label": row["ActionLabel"],
                "masked": row["WasMasked"] == "1",
                "sun":   int(row["SunshineRank"]),
                "actu":  parse_actuators(row["ActuatorState"]),
                "stuck": row["StuckFired"] == "1",
            })
    for ep in episodes.values():
        ep.sort(key=lambda r: r["step"])
    return dict(episodes)


def read_bench_results(path):
    """-> {(scenario, run): recorded ActuatorCyclingCount}"""
    out = {}
    with open(path, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            out[(int(row["ScenarioId"]), int(row["RunId"]))] = \
                int(row["ActuatorCyclingCount"])
    return out


# ---------------------------------------------------------- reconstruction --

def encode_state(z1, z2, sun, actu):
    sv = [z1, z2,
          int(actu.get("Z1Light", False)),
          int(actu.get("Z2Light", False)),
          int(actu.get("Z1Blinds", False)),
          int(actu.get("Z2Blinds", False)),
          int(actu.get("Spotlight", False)),
          sun]
    return sum(v * s for v, s in zip(sv, STRIDES))


def flips_between(prev, curr):
    """countReversals semantics: keys of prev present in curr whose value
    differs. -> [(name, new_value)]"""
    return [(k, curr[k]) for k, pv in prev.items()
            if k in curr and curr[k] != pv]


def argmax_set(row):
    m = max(row)
    return {a for a, q in enumerate(row) if q >= m - TIE_EPS}


def mc_pvalue(chances, observed, seed):
    """One-sided MC p under per-state Bernoulli(chance_s) null; add-one rule
    p = (1 + #{draw >= observed}) / (draws + 1)."""
    rng = random.Random(seed)
    ge = 0
    for _ in range(MC_DRAWS):
        x = 0
        for p in chances:
            if rng.random() < p:
                x += 1
        if x >= observed:
            ge += 1
    return (ge + 1) / (MC_DRAWS + 1)


def sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


# ------------------------------------------------------------------- audit --

def main():
    OUT.mkdir(exist_ok=True)
    layout = load_layout()
    labels, by_wot = action_maps(layout)
    res = {"registration": "THESIS_STATE_REPORT.md Addendum 2026-07-18c §1",
           "run": 29639767776, "lab": "lab3", "seeds": SEEDS}

    # ---- G3: regeneration determinism -------------------------------------
    g3_files = ["qtable_initial_stereotypes_true_lab3.csv",
                "qtable_initial_stereotypes_true_lab3_zone1.csv",
                "qtable_initial_stereotypes_true_lab3_zone2.csv"]
    g3 = {f: {"regen_A": sha256(REGEN / "regen_A" / f),
              "regen_B": sha256(REGEN / "regen_B" / f)} for f in g3_files}
    g3_pass = all(v["regen_A"] == v["regen_B"] for v in g3.values())
    res["G3"] = {"pass": g3_pass, "hashes": g3}

    init_q = read_qtable(REGEN / "regen_A" / g3_files[0])
    res["init_table_rows"] = len(init_q)

    # ---- per-seed data ------------------------------------------------------
    logs, bench, frozen, visits = {}, {}, {}, {}
    for mode, arm in MODES.items():
        for seed in SEEDS:
            d = INPUTS / f"results_seed{seed}" / "lab3" / mode
            logs[(mode, seed)]   = read_step_log(d / f"bench_step_log_{mode}.csv")
            bench[(mode, seed)]  = read_bench_results(d / f"benchmark_results_{mode}.csv")
            frozen[(mode, seed)] = read_qtable(
                d / f"qtable_final_stereotypes_{arm}_lab3.csv")
            visits[(mode, seed)] = read_visits(
                d / f"qtable_final_stereotypes_{arm}_lab3_visits.csv")

    # ---- G1: instrument reconciliation (per arm, pooled over seeds) --------
    g1 = {}
    g1_rows = []
    for mode in MODES:
        match = total = 0
        for seed in SEEDS:
            computed = defaultdict(int)
            for key, ep in logs[(mode, seed)].items():
                for i in range(1, len(ep)):
                    computed[key] += len(flips_between(ep[i - 1]["actu"],
                                                       ep[i]["actu"]))
            for key, recorded in bench[(mode, seed)].items():
                got = computed.get(key, 0)
                ok = (got == recorded)
                total += 1
                match += ok
                g1_rows.append([mode, seed, key[0], key[1], recorded, got,
                                int(ok)])
        g1[mode] = {"episodes": total, "exact": match,
                    "frac": match / total if total else 0.0}
    g1_pass = all(v["frac"] >= GATE_FRAC for v in g1.values())
    res["G1"] = {"pass": g1_pass, **g1}
    with open(OUT / "g1_reconciliation.csv", "w", newline="",
              encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["mode", "seed", "scenario", "run", "recorded_cycling",
                    "computed_cycling", "exact_match"])
        w.writerows(g1_rows)

    zone_cache = {}

    def zone_sum_row(mode, seed, state):
        arm = MODES[mode]
        if (mode, seed) not in zone_cache:
            d = INPUTS / f"results_seed{seed}" / "lab3" / mode
            z1 = read_qtable(d / f"qtable_final_stereotypes_{arm}_lab3_zone1.csv")
            z2 = read_qtable(d / f"qtable_final_stereotypes_{arm}_lab3_zone2.csv")
            zone_cache[(mode, seed)] = (z1, z2)
        z1, z2 = zone_cache[(mode, seed)]
        r1 = z1.get(state, [0.0] * N_ACTIONS)
        r2 = z2.get(state, [0.0] * N_ACTIONS)
        return [a + b for a, b in zip(r1, r2)]

    # ---- events, G2, pairs --------------------------------------------------
    g2 = {m: {"qualifying": 0, "pass": 0, "unmappable": 0} for m in MODES}
    g2_failures = []
    events = {m: [] for m in MODES}          # all D1 flip events, annotated
    pairs_by_seed = defaultdict(set)         # KG arm: seed -> {(s, a)}
    nontoggle_by_seed = defaultdict(set)     # KG arm descriptive control set
    toggle_episodes = set()                  # (seed, scenario, run) w/ D3 pair

    for mode in MODES:
        for seed in SEEDS:
            for (scen, run), ep in logs[(mode, seed)].items():
                for i in range(1, len(ep)):
                    row, prev = ep[i], ep[i - 1]
                    a_idx = map_action_label(row["label"], by_wot)
                    state = encode_state(row["z1"], row["z2"], row["sun"],
                                         prev["actu"])
                    # G2 accounting
                    if not row["stuck"] and not row["masked"]:
                        g2[mode]["qualifying"] += 1
                        if a_idx is None:
                            g2[mode]["unmappable"] += 1
                        else:
                            q = frozen[(mode, seed)].get(
                                state, [0.0] * N_ACTIONS)
                            if q[a_idx] >= max(q) - TIE_EPS:
                                g2[mode]["pass"] += 1
                            else:
                                # Diagnostic only: the bench selects on the sum
                                # of the loaded per-zone tables; each zone CSV
                                # is independently rounded to 2 decimals, so a
                                # <= 0.01 gap to the combined-CSV row max can
                                # still be an argmax under the actual loaded
                                # values.
                                zsum = zone_sum_row(mode, seed, state)
                                znote = int(zsum[a_idx] >= max(zsum) - TIE_EPS)
                                g2_failures.append(
                                    [mode, seed, scen, run, row["step"], state,
                                     row["label"], a_idx, f"{q[a_idx]:.2f}",
                                     f"{max(q):.2f}", znote])
                    # D1 / D2 / D3 events
                    for act_name, new_val in flips_between(prev["actu"],
                                                           row["actu"]):
                        held_before = any(ep[j]["actu"].get(act_name) == new_val
                                          for j in range(0, i - 1))
                        is_toggle = held_before
                        is_greedy = not row["stuck"] and not row["masked"]
                        events[mode].append({
                            "seed": seed, "scenario": scen, "run": run,
                            "step": row["step"], "actuator": act_name,
                            "to": new_val, "toggle": is_toggle,
                            "stuck": row["stuck"], "masked": row["masked"],
                            "state": state, "label": row["label"],
                            "action": a_idx})
                        if (mode == "ql_true" and is_toggle and is_greedy
                                and a_idx is not None):
                            pairs_by_seed[seed].add((state, a_idx))
                            toggle_episodes.add((seed, scen, run))

    # KG-arm descriptive non-toggle executed pairs of the toggle episodes
    for (seed, scen, run) in toggle_episodes:
        ep = logs[("ql_true", seed)][(scen, run)]
        toggle_steps = {e["step"] for e in events["ql_true"]
                        if e["seed"] == seed and e["scenario"] == scen
                        and e["run"] == run and e["toggle"]}
        for i in range(1, len(ep)):
            row, prev = ep[i], ep[i - 1]
            if row["step"] in toggle_steps or row["stuck"] or row["masked"]:
                continue
            a_idx = map_action_label(row["label"], by_wot)
            if a_idx is None:
                continue
            state = encode_state(row["z1"], row["z2"], row["sun"],
                                 prev["actu"])
            nontoggle_by_seed[seed].add((state, a_idx))

    for mode in MODES:
        n, ok = g2[mode]["qualifying"], g2[mode]["pass"]
        g2[mode]["frac"] = ok / n if n else 0.0
    g2_pooled_n = sum(g2[m]["qualifying"] for m in MODES)
    g2_pooled_ok = sum(g2[m]["pass"] for m in MODES)
    g2_frac = g2_pooled_ok / g2_pooled_n if g2_pooled_n else 0.0
    g2_pass = g2_frac >= GATE_FRAC
    res["G2"] = {"pass": g2_pass, "pooled_frac": g2_frac,
                 "pooled_qualifying": g2_pooled_n, "pooled_ok": g2_pooled_ok,
                 **{m: g2[m] for m in MODES}}
    with open(OUT / "g2_failures.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["mode", "seed", "scenario", "run", "step", "state",
                    "action_label", "action_idx", "q_executed", "q_rowmax",
                    "argmax_under_zone_sum"])
        w.writerows(g2_failures)

    for mode in MODES:
        with open(OUT / f"toggle_events_{mode}.csv", "w", newline="",
                  encoding="utf-8") as f:
            w = csv.writer(f)
            w.writerow(["seed", "scenario", "run", "step", "actuator",
                        "to_value", "is_toggle", "stuck_fired", "was_masked",
                        "state_idx", "action_label", "action_idx"])
            for e in events[mode]:
                w.writerow([e["seed"], e["scenario"], e["run"], e["step"],
                            e["actuator"], int(e["to"]), int(e["toggle"]),
                            int(e["stuck"]), int(e["masked"]), e["state"],
                            e["label"], e["action"]])

    # ---- event tallies / S1 / secondary ------------------------------------
    tallies = {}
    for mode in MODES:
        ev = events[mode]
        d1 = len(ev)
        d2 = sum(e["toggle"] for e in ev)
        d3 = sum(e["toggle"] and not e["stuck"] and not e["masked"]
                 for e in ev)
        stuck_split = {"stuck": sum(e["toggle"] and e["stuck"] for e in ev),
                       "greedy": d3}
        tallies[mode] = {"D1_flips": d1, "D2_toggles": d2,
                         "D3_greedy_toggles": d3,
                         "toggle_stuck_split": stuck_split}
    res["event_tallies"] = tallies
    d2t = tallies["ql_true"]["D2_toggles"]
    s1_frac = tallies["ql_true"]["D3_greedy_toggles"] / d2t if d2t else 0.0
    s1_pass = s1_frac > 0.5
    res["S1"] = {"pass": s1_pass, "greedy_frac_of_toggles": s1_frac}
    d1_delta = tallies["ql_true"]["D1_flips"] - tallies["ql_false"]["D1_flips"]
    d2_delta = tallies["ql_true"]["D2_toggles"] - tallies["ql_false"]["D2_toggles"]
    res["descriptive_cycling_delta"] = {
        "D1_flip_delta_true_minus_false": d1_delta,
        "D2_toggle_delta_true_minus_false": d2_delta,
        "toggle_share_of_delta": d2_delta / d1_delta if d1_delta else None}

    # ---- pooled pairs / minimum data ---------------------------------------
    realizations = [(seed, s, a) for seed in SEEDS
                    for (s, a) in sorted(pairs_by_seed.get(seed, ()))]
    n_pairs = len(realizations)
    res["pooled_unique_greedy_toggle_pairs"] = n_pairs
    res["minimum_data"] = {"pass": n_pairs >= MIN_PAIRS, "n": n_pairs,
                           "required": MIN_PAIRS}

    # ---- P1: rarely visited -------------------------------------------------
    pair_visits = []
    for seed, s, a in realizations:
        v = visits[("ql_true", seed)].get(s, [0] * N_ACTIONS)[a]
        pair_visits.append(v)
    p1_median = statistics.median(pair_visits) if pair_visits else None
    p1_pass = p1_median is not None and p1_median <= P1_MAX_MEDIAN_VISITS
    nt_visits = [visits[("ql_true", seed)].get(s, [0] * N_ACTIONS)[a]
                 for seed in SEEDS
                 for (s, a) in sorted(nontoggle_by_seed.get(seed, ()))]
    res["P1"] = {"pass": p1_pass, "median_visits": p1_median,
                 "threshold": P1_MAX_MEDIAN_VISITS,
                 "visits": pair_visits,
                 "descriptive_nontoggle_median":
                     statistics.median(nt_visits) if nt_visits else None,
                 "descriptive_nontoggle_n": len(nt_visits)}

    # ---- P2: init alignment -------------------------------------------------
    members, chances = [], []
    for seed, s, a in realizations:
        row = init_q.get(s, [0.0] * N_ACTIONS)
        aset = argmax_set(row)
        members.append(a in aset)
        chances.append(len(aset) / N_ACTIONS)
    obs = sum(members)
    p2_rate = obs / n_pairs if n_pairs else 0.0
    p2_chance = statistics.mean(chances) if chances else 0.0
    p2_p = mc_pvalue(chances, obs, MC_SEED) if n_pairs else None
    p2_pass = (n_pairs > 0 and p2_rate >= p2_chance + P2_MARGIN
               and p2_p is not None and p2_p < 0.05)
    res["P2"] = {"pass": p2_pass, "rate": p2_rate, "successes": obs,
                 "n": n_pairs, "tie_adjusted_chance": p2_chance,
                 "required_rate": p2_chance + P2_MARGIN, "mc_p": p2_p,
                 "mc_draws": MC_DRAWS, "mc_seed": MC_SEED}

    # ---- P3: tabula-rasa control -------------------------------------------
    ctrl_states = sorted({(seed, s) for seed, s, _ in realizations})
    excluded = 0
    ctrl_succ, ctrl_chances = [], []
    for seed, s in ctrl_states:
        qf = frozen[("ql_false", seed)].get(s, [0.0] * N_ACTIONS)
        if max(qf) - min(qf) <= TIE_EPS:      # no learned preference
            excluded += 1
            continue
        init_set = argmax_set(init_q.get(s, [0.0] * N_ACTIONS))
        ctrl_succ.append(bool(argmax_set(qf) & init_set))
        ctrl_chances.append(len(init_set) / N_ACTIONS)
    decidable = len(ctrl_succ)
    p3_indet = (len(ctrl_states) == 0 or excluded > 0.5 * len(ctrl_states)
                or decidable < 20)
    if decidable:
        c_obs = sum(ctrl_succ)
        p3_rate = c_obs / decidable
        p3_chance = statistics.mean(ctrl_chances)
        p3_p = mc_pvalue(ctrl_chances, c_obs, MC_SEED)
    else:
        c_obs, p3_rate, p3_chance, p3_p = 0, None, None, None
    control_aligns = (not p3_indet and p3_rate is not None
                      and p3_rate >= p3_chance + P2_MARGIN and p3_p < 0.05)
    p3_pass = (not p3_indet) and (not control_aligns)
    res["P3"] = {"pass": p3_pass, "indeterminate": p3_indet,
                 "control_aligns": control_aligns, "states": len(ctrl_states),
                 "excluded_no_preference": excluded, "decidable": decidable,
                 "rate": p3_rate, "successes": c_obs,
                 "tie_adjusted_chance": p3_chance, "mc_p": p3_p}

    # ---- pair table ---------------------------------------------------------
    with open(OUT / "toggle_pairs_ql_true.csv", "w", newline="",
              encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["seed", "state_idx", "action_idx", "action_label",
                    "train_visits", "init_argmax_member", "chance_s"])
        for (seed, s, a), v, m, c in zip(realizations, pair_visits, members,
                                         chances):
            w.writerow([seed, s, a, labels[a], v, int(m), f"{c:.4f}"])

    # ---- decision rule (pre-committed) -------------------------------------
    gates_ok = g1_pass and g2_pass and g3_pass and n_pairs >= MIN_PAIRS
    if not gates_ok:
        decision = ("INDETERMINATE (insufficient toggling to instrument)"
                    if (g1_pass and g2_pass and g3_pass) else "INVALID")
    elif not s1_pass or not p1_pass or not p2_pass or control_aligns:
        decision = "DROPPED"
    elif p3_indet:
        decision = "CONFIRMED (qualified)"
    else:
        decision = "CONFIRMED"
    res["decision"] = decision

    with open(OUT / "audit_results.json", "w", encoding="utf-8") as f:
        json.dump(res, f, indent=2)

    # ---- summary ------------------------------------------------------------
    lines = ["# Test A — toggling micro-mechanism audit (registered "
             "2026-07-18c §1)", "",
             f"**Decision: {decision}**", "",
             "| item | value | pass |", "|---|---|---|",
             f"| G1 instrument reconciliation | ql_true "
             f"{g1['ql_true']['exact']}/{g1['ql_true']['episodes']} "
             f"({g1['ql_true']['frac']:.4f}), ql_false "
             f"{g1['ql_false']['exact']}/{g1['ql_false']['episodes']} "
             f"({g1['ql_false']['frac']:.4f}) | {g1_pass} |",
             f"| G2 encoding/selection consistency | pooled "
             f"{g2_pooled_ok}/{g2_pooled_n} ({g2_frac:.4f}); unmappable "
             f"{sum(g2[m]['unmappable'] for m in MODES)} | {g2_pass} |",
             f"| G3 init determinism | bit-identical A/B: {g3_pass} | "
             f"{g3_pass} |",
             f"| minimum data (>= {MIN_PAIRS} pairs) | {n_pairs} pooled "
             f"unique KG-arm greedy toggle pairs | {n_pairs >= MIN_PAIRS} |",
             f"| S1 greedy share of toggles | {s1_frac:.4f} "
             f"(D3 {tallies['ql_true']['D3_greedy_toggles']} / D2 "
             f"{tallies['ql_true']['D2_toggles']}) | {s1_pass} |",
             f"| P1 median toggle-pair visits | {p1_median} (<= "
             f"{P1_MAX_MEDIAN_VISITS}); non-toggle descriptive "
             f"{res['P1']['descriptive_nontoggle_median']} "
             f"(n={res['P1']['descriptive_nontoggle_n']}) | {p1_pass} |",
             f"| P2 init alignment | rate {p2_rate:.4f} vs chance "
             f"{p2_chance:.4f}+{P2_MARGIN} = {p2_chance + P2_MARGIN:.4f}, "
             f"MC p = {p2_p} | {p2_pass} |",
             f"| P3 tabula-rasa control | rate {p3_rate} vs chance "
             f"{p3_chance}, p = {p3_p}; excluded {excluded}/"
             f"{len(ctrl_states)}, decidable {decidable}; indeterminate = "
             f"{p3_indet}; control_aligns = {control_aligns} | {p3_pass} |",
             "",
             f"Event tallies: {json.dumps(tallies)}", "",
             f"Cycling-delta decomposition (descriptive): {json.dumps(res['descriptive_cycling_delta'])}", ""]
    (OUT / "SUMMARY.md").write_text("\n".join(lines), encoding="utf-8")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
