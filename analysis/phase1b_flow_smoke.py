#!/usr/bin/env python3
"""Exercise all seven Phase-1b Node-RED flows over their live HTTP APIs.

The companion ``scripts/Run-Phase1bFlowSmoke.ps1`` starts isolated Node-RED
instances. This probe then verifies /health, /reset, /setState, /action, and
/status and checks one deterministic physics path per lab. Its JSON output is
the retained, machine-readable smoke record.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import platform
import subprocess
import time
import urllib.error
import urllib.request
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class Checkpoint:
    action: dict[str, Any]
    expected_status: dict[str, Any]


@dataclass(frozen=True)
class FlowSpec:
    profile: str
    port: int
    flow: str
    set_state: dict[str, Any]
    initial_status: dict[str, Any]
    checkpoints: tuple[Checkpoint, ...]


RELATIVE_SPECS = tuple(
    FlowSpec(
        profile=profile,
        port=port,
        flow=f"simulator/simulator_flow_{profile}.json",
        set_state={"Z1Level": 25, "Z1Light": False, "Sunshine": 0},
        initial_status={"Z1Light": False, "Z1Level": 25},
        checkpoints=(
            Checkpoint({"Z1Light": True},
                       {"Z1Light": True, "Z1Level": 425}),
        ),
    )
    for profile, port in (
        ("labrel0", 1904),
        ("labrel4", 1905),
        ("labrel8", 1906),
        ("labrel16", 1907),
        ("labrel8s", 1908),
    )
)

SPECS = RELATIVE_SPECS + (
    FlowSpec(
        profile="labband",
        port=1912,
        flow="simulator/simulator_flow_labband.json",
        set_state={
            "Z1Level": 25,
            "StrongLamp": False,
            "WeakLamp": False,
            "Z1Blinds": False,
            "Awning": False,
            "Sunshine": 0,
        },
        initial_status={
            "StrongLamp": False,
            "WeakLamp": False,
            "Z1Blinds": False,
            "Awning": False,
            "Z1Level": 25,
        },
        checkpoints=(
            Checkpoint({"WeakLamp": True},
                       {"WeakLamp": True, "Z1Level": 175}),
        ),
    ),
    FlowSpec(
        profile="lab4chain3",
        port=1913,
        flow="simulator/simulator_flow_lab4chain3.json",
        set_state={
            "Z1Level": 25,
            "Z1Light": False,
            "PlugZ1": False,
            "Breaker": False,
            "AuxA": False,
            "AuxB": False,
            "Sunshine": 0,
        },
        initial_status={
            "Z1Light": False,
            "PlugZ1": False,
            "Breaker": False,
            "Z1Level": 25,
        },
        checkpoints=(
            Checkpoint({"Z1Light": True},
                       {"Z1Light": True, "Z1Level": 25}),
            Checkpoint({"PlugZ1": True},
                       {"PlugZ1": True, "Z1Level": 25}),
            Checkpoint({"Breaker": True},
                       {"Breaker": True, "Z1Level": 425}),
        ),
    ),
)


def _request_json(url: str, method: str = "GET",
                  body: dict[str, Any] | None = None,
                  timeout: float = 3.0) -> tuple[int, dict[str, Any]]:
    data = None if body is None else json.dumps(body).encode("utf-8")
    request = urllib.request.Request(
        url, data=data, method=method,
        headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            payload = json.loads(response.read().decode("utf-8"))
            return response.status, payload
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"{method} {url} -> HTTP {exc.code}: {detail}") from exc


def _matches(actual: dict[str, Any], expected: dict[str, Any]) -> bool:
    for key, value in expected.items():
        if key not in actual:
            return False
        observed = actual[key]
        if isinstance(value, (int, float)) and not isinstance(value, bool):
            if not isinstance(observed, (int, float)) or abs(observed - value) > 1e-9:
                return False
        elif observed != value:
            return False
    return True


def _wait_json(url: str, expected: dict[str, Any] | None = None,
               timeout: float = 60.0) -> tuple[int, dict[str, Any]]:
    deadline = time.monotonic() + timeout
    last_error: Exception | None = None
    last_payload: dict[str, Any] | None = None
    while time.monotonic() < deadline:
        try:
            status, payload = _request_json(url)
            last_payload = payload
            if status == 200 and (expected is None or _matches(payload, expected)):
                return status, payload
        except (OSError, RuntimeError, json.JSONDecodeError) as exc:
            last_error = exc
        time.sleep(0.1)
    detail = f"last payload={last_payload}" if last_payload is not None \
        else f"last error={last_error}"
    raise RuntimeError(f"timed out waiting for {url}: {detail}")


def _post_ok(base: str, endpoint: str,
             body: dict[str, Any] | None = None) -> dict[str, Any]:
    status, payload = _request_json(
        f"{base}{endpoint}", method="POST", body=body or {})
    if status != 200:
        raise RuntimeError(f"POST {endpoint} returned HTTP {status}")
    return payload


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _git_text(root: Path, *args: str) -> str:
    try:
        return subprocess.check_output(
            ["git", *args], cwd=root, text=True,
            stderr=subprocess.DEVNULL).strip()
    except (OSError, subprocess.CalledProcessError):
        return ""


def smoke(root: Path, node_red_version: str = "") -> dict[str, Any]:
    records: list[dict[str, Any]] = []
    for spec in SPECS:
        base = f"http://127.0.0.1:{spec.port}"
        flow_path = root / spec.flow
        health_code, health = _wait_json(f"{base}/health")
        if health.get("status") != "ok":
            raise RuntimeError(f"{spec.profile}: unhealthy payload {health}")
        advertised = health.get("endpoints", {})
        if not all(advertised.get(name) is True
                   for name in ("status", "action", "reset", "setState")):
            raise RuntimeError(
                f"{spec.profile}: incomplete endpoint advertisement {advertised}")

        reset = _post_ok(base, "/was/rl/reset")
        if reset.get("reset") is not True:
            raise RuntimeError(f"{spec.profile}: invalid reset response {reset}")
        set_state = _post_ok(base, "/was/rl/setState", spec.set_state)
        if set_state.get("status") != "ok":
            raise RuntimeError(
                f"{spec.profile}: invalid setState response {set_state}")
        _, initial = _wait_json(
            f"{base}/was/rl/status", spec.initial_status, timeout=5.0)

        checkpoints: list[dict[str, Any]] = []
        for checkpoint in spec.checkpoints:
            action = _post_ok(base, "/was/rl/action", checkpoint.action)
            if action.get("status") != "ok":
                raise RuntimeError(
                    f"{spec.profile}: invalid action response {action}")
            _, observed = _wait_json(
                f"{base}/was/rl/status",
                checkpoint.expected_status, timeout=5.0)
            checkpoints.append({
                "action": checkpoint.action,
                "expected_status": checkpoint.expected_status,
                "observed_status": {
                    key: observed[key] for key in checkpoint.expected_status
                },
            })

        records.append({
            "profile": spec.profile,
            "port": spec.port,
            "flow": spec.flow,
            "flow_sha256": _sha256(flow_path),
            "health_http_status": health_code,
            "health_tab": health.get("tab"),
            "endpoints": advertised,
            "reset_response": reset,
            "set_state_response": set_state,
            "initial_observed_status": {
                key: initial[key] for key in spec.initial_status
            },
            "checkpoints": checkpoints,
            "status": "passed",
        })

    tracked_status = _git_text(root, "status", "--porcelain",
                               "--untracked-files=no")
    return {
        "schema": "phase1b-live-flow-smoke-v1",
        "run_utc": datetime.now(timezone.utc).isoformat(),
        "git_head": _git_text(root, "rev-parse", "HEAD"),
        "tracked_worktree_clean": tracked_status == "",
        "node_red_version": node_red_version,
        "python_version": platform.python_version(),
        "platform": platform.platform(),
        "profiles_expected": len(SPECS),
        "profiles_passed": len(records),
        "endpoint_contract": [
            "/health",
            "/was/rl/reset",
            "/was/rl/setState",
            "/was/rl/action",
            "/was/rl/status",
        ],
        "records": records,
        "status": "passed",
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(__file__).parents[1])
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--node-red-version", default="")
    args = parser.parse_args(argv)

    root = args.root.resolve()
    output = args.output if args.output.is_absolute() else root / args.output
    output.parent.mkdir(parents=True, exist_ok=True)
    try:
        evidence = smoke(root, node_red_version=args.node_red_version)
    except Exception as exc:
        evidence = {
            "schema": "phase1b-live-flow-smoke-v1",
            "run_utc": datetime.now(timezone.utc).isoformat(),
            "git_head": _git_text(root, "rev-parse", "HEAD"),
            "status": "failed",
            "error": str(exc),
        }
        output.write_text(
            json.dumps(evidence, indent=2, sort_keys=True) + "\n",
            encoding="utf-8", newline="\n")
        print(f"Phase-1b live flow smoke FAILED: {exc}")
        return 1

    output.write_text(
        json.dumps(evidence, indent=2, sort_keys=True) + "\n",
        encoding="utf-8", newline="\n")
    print(
        f"Phase-1b live flow smoke PASSED: "
        f"{evidence['profiles_passed']}/{evidence['profiles_expected']} flows; "
        f"evidence={output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
