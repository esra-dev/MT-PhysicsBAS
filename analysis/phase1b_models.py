"""Deterministic transition models for the Phase-1b labs (Stage 1).

Binds the frozen Phase-1b physics to the generic exhaustive checker in
``transition_checker.py``. One model instance = one profile + one scenario
(initial state + pinned exogenous sun). The intended-route metadata is
derived from THEORY (counting the missing goal-route elements), not from the
checker's own search, so the certificate's shortcut detection stays a real
cross-check for the ladder and chain labs. For labband, whose corrective
routes are intentionally plural, no single intended mechanism exists; its
certificates enumerate every shortest route for the registration record and
the intended-length field is left unset.

Physics (must match the committed simulator flows and scenario headers):
  labrel*/labrel8s : z1 = 25 + (lamp ? 400 : 0)                       (no sun)
  labband          : daylight = blind ? 0.50*sun : 0 ; awning => *0.25
                     z1 = 25 + strong*400 + weak*150 + daylight
  lab4chain3       : z1 = 25 + 400*(lamp && plug && breaker)          (no sun)

Rank bounds (lab family): [50, 100, 300].
"""

from __future__ import annotations

import json
import os
from typing import Dict, List, Optional, Sequence, Tuple

LIGHT_BOUNDS = (50.0, 100.0, 300.0)
HORIZON = 20  # max_steps_per_episode for every phase1b mode


def rank(lux: float, bounds: Sequence[float] = LIGHT_BOUNDS) -> int:
    if lux < bounds[0]:
        return 0
    if lux < bounds[1]:
        return 1
    if lux < bounds[2]:
        return 2
    return 3


# ---------------------------------------------------------------------------
# Decoy roster (must match building_10_labrel*.ttl; ladder-nested)
# ---------------------------------------------------------------------------
LABREL_DECOYS = [
    "Fan", "Humidifier", "Heater", "Speaker",
    "AirPurifier", "Dehumidifier", "Cooler", "WhiteNoiseUnit",
    "Ventilator", "Ionizer", "CO2Scrubber", "Radiator",
    "ExhaustFan", "AromaDiffuser", "Subwoofer", "HeatPump",
]


def _pairs(names: Sequence[str]) -> List[str]:
    out = []
    for n in names:
        out.append("Set%s|ON" % n)
        out.append("Set%s|OFF" % n)
    return out


class LabrelModel:
    """Stateless-decoy rungs: observed state = (rank, lamp)."""

    def __init__(self, k_decoys: int, lamp0: bool):
        self.k = k_decoys
        self._init = self._encode(lamp0)
        self._actions = (_pairs(["Z1Light"])
                         + _pairs(LABREL_DECOYS[:k_decoys])
                         + ["DO_NOTHING"])

    @staticmethod
    def _encode(lamp: bool) -> Tuple[int, int]:
        return (rank(25 + (400 if lamp else 0)), 1 if lamp else 0)

    def initial_state(self):
        return self._init

    def actions(self, state):
        return list(self._actions)

    def step(self, state, action):
        lamp = state[1] == 1
        if action == "SetZ1Light|ON":
            lamp = True
        elif action == "SetZ1Light|OFF":
            lamp = False
        # decoys and DO_NOTHING: observationally a self-loop
        return self._encode(lamp)

    def is_goal(self, state):
        return state[0] == 3


class Labrel8sModel:
    """Fragmented rung: decoy bits are observable state."""

    def __init__(self, lamp0: bool, decoys0: Optional[Sequence[bool]] = None):
        d = list(decoys0) if decoys0 is not None else [False] * 8
        assert len(d) == 8
        self._init = self._encode(lamp0, d)
        self._actions = (_pairs(["Z1Light"]) + _pairs(LABREL_DECOYS[:8])
                         + ["DO_NOTHING"])

    @staticmethod
    def _encode(lamp: bool, decoys: Sequence[bool]):
        return (rank(25 + (400 if lamp else 0)), 1 if lamp else 0,
                tuple(1 if x else 0 for x in decoys))

    def initial_state(self):
        return self._init

    def actions(self, state):
        return list(self._actions)

    def step(self, state, action):
        lamp = state[1] == 1
        decoys = [x == 1 for x in state[2]]
        if action == "SetZ1Light|ON":
            lamp = True
        elif action == "SetZ1Light|OFF":
            lamp = False
        else:
            for i, name in enumerate(LABREL_DECOYS[:8]):
                if action == "Set%s|ON" % name:
                    decoys[i] = True
                elif action == "Set%s|OFF" % name:
                    decoys[i] = False
        return self._encode(lamp, decoys)

    def is_goal(self, state):
        return state[0] == 3


class LabbandModel:
    """Exact-band lab: goal is rank == 2 (band 100-300 lux)."""

    ACTUATORS = ["StrongLamp", "WeakLamp", "Z1Blinds", "Awning"]

    def __init__(self, strong0, weak0, blind0, awning0, sun: float):
        self.sun = float(sun)
        self._init = self._encode(strong0, weak0, blind0, awning0)
        self._actions = _pairs(self.ACTUATORS) + ["DO_NOTHING"]

    def lux(self, strong, weak, blind, awning) -> float:
        daylight = 0.50 * self.sun if blind else 0.0
        if awning:
            daylight *= 0.25
        return 25 + (400 if strong else 0) + (150 if weak else 0) + daylight

    def _encode(self, s, w, b, a):
        return (rank(self.lux(s, w, b, a)),
                1 if s else 0, 1 if w else 0, 1 if b else 0, 1 if a else 0)

    def initial_state(self):
        return self._init

    def actions(self, state):
        return list(self._actions)

    def step(self, state, action):
        s, w, b, a = (state[1] == 1, state[2] == 1, state[3] == 1, state[4] == 1)
        for i, name in enumerate(self.ACTUATORS):
            if action == "Set%s|ON" % name:
                (s, w, b, a) = tuple(True if j == i else v
                                     for j, v in enumerate((s, w, b, a)))
            elif action == "Set%s|OFF" % name:
                (s, w, b, a) = tuple(False if j == i else v
                                     for j, v in enumerate((s, w, b, a)))
        return self._encode(s, w, b, a)

    def is_goal(self, state):
        return state[0] == 2


class Chain3Model:
    """Depth-3 dependency: lamp lights only when lamp && plug && breaker."""

    CHAIN = ["Z1Light", "PlugZ1", "Breaker"]
    DECOYS = ["AuxA", "AuxB"]

    def __init__(self, lamp0, plug0, breaker0, auxa0=False, auxb0=False):
        self._init = self._encode(lamp0, plug0, breaker0, auxa0, auxb0)
        self._actions = _pairs(self.CHAIN + ["AuxA", "AuxB"]) + ["DO_NOTHING"]

    @staticmethod
    def _encode(l, p, b, a1, a2):
        lit = l and p and b
        return (rank(25 + (400 if lit else 0)),
                1 if l else 0, 1 if p else 0, 1 if b else 0,
                1 if a1 else 0, 1 if a2 else 0)

    def initial_state(self):
        return self._init

    def actions(self, state):
        return list(self._actions)

    def step(self, state, action):
        bits = {"Z1Light": state[1] == 1, "PlugZ1": state[2] == 1,
                "Breaker": state[3] == 1, "AuxA": state[4] == 1,
                "AuxB": state[5] == 1}
        for name in bits:
            if action == "Set%s|ON" % name:
                bits[name] = True
            elif action == "Set%s|OFF" % name:
                bits[name] = False
        return self._encode(bits["Z1Light"], bits["PlugZ1"], bits["Breaker"],
                            bits["AuxA"], bits["AuxB"])

    def is_goal(self, state):
        return state[0] == 3


# ---------------------------------------------------------------------------
# Scenario loading + theory-derived intent
# ---------------------------------------------------------------------------

def _load_scenarios(path: str) -> List[dict]:
    with open(path, encoding="utf-8") as fh:
        rows = json.load(fh)
    return [r for r in rows if isinstance(r, dict) and "id" in r]


def models_for_profile(profile: str, repo_root: str):
    """Yield (scenario_id, model, intended_mechanism, intended_length)."""
    bench = os.path.join(repo_root, "benchmark")

    def b(v):
        return bool(v)

    if profile.startswith("labrel") and profile != "labrel8s":
        k = {"labrel0": 0, "labrel4": 4, "labrel8": 8, "labrel16": 16}[profile]
        for sc in _load_scenarios(os.path.join(bench, "scenarios_labrel.json")):
            lamp = b(sc["Z1Light"])
            mech = [] if lamp else ["SetZ1Light|ON"]
            yield sc["id"], LabrelModel(k, lamp), mech, len(mech)
    elif profile == "labrel8s":
        for sc in _load_scenarios(os.path.join(bench, "scenarios_labrel8s.json")):
            lamp = b(sc["Z1Light"])
            decoys = [b(sc.get(n, False)) for n in LABREL_DECOYS[:8]]
            mech = [] if lamp else ["SetZ1Light|ON"]
            yield sc["id"], Labrel8sModel(lamp, decoys), mech, len(mech)
    elif profile == "labband":
        for sc in _load_scenarios(os.path.join(bench, "scenarios_labband.json")):
            m = LabbandModel(b(sc["StrongLamp"]), b(sc["WeakLamp"]),
                             b(sc["Z1Blinds"]), b(sc["Awning"]), sc["Sunshine"])
            # Plural corrective routes by design: no single intended
            # mechanism; certificates enumerate all shortest routes instead.
            yield sc["id"], m, [], None
    elif profile == "lab4chain3":
        for sc in _load_scenarios(os.path.join(bench, "scenarios_lab4chain3.json")):
            l, p, brk = b(sc["Z1Light"]), b(sc["PlugZ1"]), b(sc["Breaker"])
            missing = [("SetZ1Light|ON", l), ("SetPlugZ1|ON", p), ("SetBreaker|ON", brk)]
            mech = [a for a, on in missing if not on]
            yield sc["id"], Chain3Model(l, p, brk, b(sc.get("AuxA", False)),
                                        b(sc.get("AuxB", False))), mech, len(mech)
    else:
        raise ValueError("unknown phase1b profile: %s" % profile)


PROFILES = ["labrel0", "labrel4", "labrel8", "labrel16", "labrel8s",
            "labband", "lab4chain3"]
