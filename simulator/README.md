# Simulator for MT-Esra Weakness Labs

## Overview

The simulator is built with [Node-RED](https://nodered.org/) and implements a REST API that the JaCaMo agents interact with. Seven flow files are provided — one 2-zone baseline lab and six 4-zone weakness labs, each injecting a different systematic ontology gap.

Each simulator exposes two HTTP endpoints:

- `GET  /was/rl/status`  — returns the full environment state as JSON
- `POST /was/rl/action`  — applies an actuator action and returns the cost

---

## Simulator Flows

| File | Port | Lab | Weakness | Description |
|------|------|-----|----------|-------------|
| `simulator_flow.json` | 1880 | Original 2-zone | none | Original simulated lab from course assignment |
| `simulator_flow_custom.json` | 1881 | Custom 2-zone | none | Custom lab with spotlight + radiators |
| `simulator_flow_custom2.json` | 1882 | 4-zone W1 | Missing-stereotype | CorridorLight bleeds +30 lux to all zones during hours 8–18, undeclared in ontology |
| `simulator_flow_custom3.json` | 1883 | 4-zone W2 | Context-dependent inversion | Blind_Z2 contribution inverts sign at Sunshine >= 500 lux |
| `simulator_flow_custom4.json` | 1884 | 4-zone W3 | Dynamics | Per-lamp ramp (3-tick rise), residual illuminance, hysteresis |
| `simulator_flow_custom5.json` | 1885 | 4-zone W4 | Shared resource | 7-unit power budget; lowest-priority lamp is silently dropped when over cap |
| `simulator_flow_custom6.json` | 1886 | 4-zone W5 | Dynamic topology | Partition23 connection toggles every 5 ticks, causing unpredictable zone coupling |
| `simulator_flow_custom7.json` | 1887 | 4-zone W6 | Multi-objective heat | Every ON lamp raises zone temperature +0.1 C/tick |

---

## Running a Single Simulator

### Prerequisites

- [Node-RED](https://nodered.org/) installed globally:
  ```
  npm install -g --unsafe-perm node-red
  ```

### Steps

1. Start Node-RED on the desired port, pointing at the flow file:

   ```bash
   # Custom 2-zone lab (port 1881) — used by the rule-based and Q-learning agents
   node-red --port 1881 simulator/simulator_flow_custom.json

   # Weakness lab W1 (port 1882) — used by profile custom2
   node-red --userDir .node-red-custom2 --port 1882 simulator/simulator_flow_custom2.json
   ```

2. Open the Node-RED editor at `http://127.0.0.1:<port>/` and click **Deploy** if the flow is not already deployed.

3. Verify the simulator is running by querying the status endpoint:

   ```bash
   curl http://127.0.0.1:1881/was/rl/status
   ```

   Example response (2-zone lab):

   ```json
   {
     "Z1Level": 396.4,
     "Z2Level": 473.2,
     "Z1Light": false,
     "Z2Light": true,
     "Z1Blinds": true,
     "Z2Blinds": false,
     "Spotlight": false,
     "Sunshine": 640.1,
     "TotalEnergyCost": 15,
     "EnergyCost": 0,
     "Hour": 1.5
   }
   ```

   Example response (4-zone lab, custom2+):

   ```json
   {
     "Z1Level": 75.0, "Z2Level": 75.0, "Z3Level": 75.0, "Z4Level": 75.0,
     "Z1Light": false, "Z2Light": false, "Z3Light": false, "Z4Light": false,
     "Z1Blinds": false, "Z2Blinds": false, "Z3Blinds": false, "Z4Blinds": false,
     "Spotlight": false, "SpotlightCD": false, "CorridorLight": false,
     "Z1Radiator": false, "Z2Radiator": false, "Z3Radiator": false, "Z4Radiator": false,
     "Z1Temp": 21.0, "Z2Temp": 21.0, "Z3Temp": 21.0, "Z4Temp": 21.0,
     "Sunshine": 150.0,
     "TotalEnergyCost": 0, "EnergyCost": 0, "Hour": 0.0
   }
   ```

4. To send an action, POST the actuator name and value as JSON:

   ```bash
   # Turn on Zone 1 ceiling light
   curl -X POST http://127.0.0.1:1881/was/rl/action \
        -H "Content-Type: application/json" \
        -d "{\"Z1Light\": true}"
   ```

   Response:
   ```json
   { "Z1Light": true, "cost": 100 }
   ```

---

## Running All Six Weakness Labs at Once

The `run_full_project.ps1` script starts all six weakness-lab simulators automatically, waits for each to respond on its port, then runs training and benchmark sweeps.

To start them manually from the project root:

```powershell
$flows = @(
  @{Port=1882; Flow="simulator_flow_custom2.json"},
  @{Port=1883; Flow="simulator_flow_custom3.json"},
  @{Port=1884; Flow="simulator_flow_custom4.json"},
  @{Port=1885; Flow="simulator_flow_custom5.json"},
  @{Port=1886; Flow="simulator_flow_custom6.json"},
  @{Port=1887; Flow="simulator_flow_custom7.json"}
)
foreach ($s in $flows) {
  Start-Process node-red -ArgumentList "--userDir .node-red-$($s.Port) --port $($s.Port) simulator/$($s.Flow)"
}
```

---

## Environment Tick Rate

The simulator uses an inject node that fires every `<tick>` seconds. The default is **0.05 s** in `dev` mode and **0.2 s** in `paper` mode (set by `run_full_project.ps1`). Each tick increments `Hour` and recomputes zone illuminance levels based on actuator states and sunshine.

The agent's `action_delay_ms` belief must be set higher than the tick interval plus network jitter to ensure actions take effect before the next state read.

---

## Weakness Patches

All six 4-zone weakness flows share the same base physics. Each injects exactly one patch into the "Update environment" function node. The patches are maintained in `generate_flows.ps1` and can be updated there before regenerating:

| Lab | Patch behaviour |
|-----|----------------|
| custom2 W1 | `CorridorLight` adds +30 lux to all zones when `Hour` is in 8..18 (not modelled in ontology) |
| custom3 W2 | When `Z2Blinds` is open and `Sunshine >= 500`, the Z2→Z1 bleed contribution is negated (sign inversion) |
| custom4 W3 | Ceiling lights ramp over 3 ticks, leave residual illuminance when turned off, and exhibit ON/OFF hysteresis |
| custom5 W4 | A 7-unit power cap is enforced; if exceeded, the lowest-priority actuator request is silently dropped |
| custom6 W5 | A `Partition23` flag toggles every 5 ticks, coupling/decoupling Zone 2 and Zone 3 |
| custom7 W6 | Each ON lamp raises its zone's temperature by +0.1 °C/tick; affects comfort metrics only |

---

## Regenerating the Weakness-Lab Flows

All six weakness-lab flow files are generated from `generate_flows.ps1`. Run this after modifying a weakness patch:

```powershell
powershell -ExecutionPolicy Bypass -File simulator/generate_flows.ps1
```

---

## Simulator State Fields

| Field | Type | Labs | Description |
|-------|------|------|-------------|
| `ZxLevel` | float | all | Zone x illuminance in lux (x = 1..2 or 1..4) |
| `ZxLight` | bool | all | Zone x ceiling light state |
| `ZxBlinds` | bool | all | Zone x blinds state (true = open) |
| `Spotlight` | bool | all | Spotlight state |
| `SpotlightCD` | bool | 4-zone | Spotlight cooldown active |
| `CorridorLight` | bool | 4-zone | Corridor light state |
| `ZxRadiator` | bool | 4-zone | Zone x radiator state |
| `ZxTemp` | float | 4-zone | Zone x temperature in Celsius |
| `Sunshine` | float | all | External sunshine in lux |
| `TotalEnergyCost` | int | all | Cumulative energy cost since last reset |
| `EnergyCost` | int | all | Energy cost of the last action |
| `Hour` | float | all | Simulated time of day (incremented each tick) |
