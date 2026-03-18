# MT-Esra: Illuminance Controller Agent

A simplified multi-agent system for controlling illuminance in a lab environment using rule-based logic.

## Overview

This project implements an intelligent agent that controls the lighting in two workstations (Zone 1 and Zone 2) to achieve target illuminance levels. Unlike the original Assignment-11 project which uses Q-learning, this version uses **rule-based control** for simplicity and predictability.

## Features

- **Rule-based control**: Simple, predictable logic for adjusting illuminance
- **Two workstations**: Independent control of Zone 1 and Zone 2
- **Multiple actuators**: Controls both ceiling lights and window blinds
- **Environment switching**: Easy switch between simulated and real lab environments
- **WoT integration**: Uses W3C Web of Things Thing Descriptions for device interaction

## Control Logic

The agent uses the following rule-based strategy:

### To Increase Illuminance:
1. If blinds are down and sunshine is available, raise the blinds first
2. If blinds are already up or no sunshine, turn on the ceiling lights

### To Decrease Illuminance:
1. If lights are on, turn them off first
2. If lights are already off and blinds are up, lower the blinds

## Illuminance Levels

The system discretizes continuous lux values into 4 ranks:

| Rank | Lux Range | Description |
|------|-----------|-------------|
| 0 | < 50 | Very dark |
| 1 | 50-100 | Dim |
| 2 | 100-300 | Medium |
| 3 | >= 300 | Bright |

## Configuration

### Target Illuminance Levels

Edit `task_requirements([Z1Target, Z2Target])` in the agent file:
```prolog
task_requirements([2, 3]).  // Zone 1: Rank 2, Zone 2: Rank 3
```

### Environment Selection

In `src/agt/illuminance_controller_agent.asl`, change the environment URL in the `@start` plan:

```prolog
// For SIMULATED environment:
LabURL = SimulatedURL;

// For REAL environment:
// LabURL = RealURL;
```

## Project Structure

```
MT-Esra/
├── build.gradle                    # Gradle build configuration
├── task.jcm                        # JaCaMo project configuration
├── gradlew / gradlew.bat          # Gradle wrapper scripts
├── gradle/                         # Gradle wrapper files
├── src/
│   ├── agt/
│   │   └── illuminance_controller_agent.asl  # Agent behavior
│   └── env/
│       └── tools/
│           ├── LabEnvironment.java           # Lab interaction artifact
│           └── LabStateReader.java           # State reading artifact
└── README.md
```

## Running the Project

### Prerequisites
- Java 11 or higher
- Internet connection (to access WoT Thing Description)

### Build and Run

```bash
# Windows
gradlew.bat task

# Linux/Mac
./gradlew task
```

## URLs

- **Simulated Lab**: `https://raw.githubusercontent.com/Interactions-HSG/example-tds/was/tds/interactions-lab.ttl`
- **Real Lab**: `https://raw.githubusercontent.com/Interactions-HSG/example-tds/was/tds/interactions-lab-real.ttl`

## Technical Details

### Agent Artifacts

1. **LabEnvironment**: CArtAgO artifact for interacting with the lab via WoT Thing Description
   - `readState()`: Read current state of all sensors and actuators
   - `setZ1Light(boolean)`: Control Zone 1 ceiling light
   - `setZ2Light(boolean)`: Control Zone 2 ceiling light
   - `setZ1Blinds(boolean)`: Control Zone 1 blinds
   - `setZ2Blinds(boolean)`: Control Zone 2 blinds

2. **LabStateReader**: Alternative artifact for reading state from REST API (optional)

### State Format

The lab state is represented as a 7-element vector:
```
[Z1Level, Z2Level, Z1Light, Z2Light, Z1Blinds, Z2Blinds, Sunshine]
```

- `ZxLevel`: Illuminance rank (0-3)
- `ZxLight`: Light status (true=on, false=off)
- `ZxBlinds`: Blinds status (true=up/open, false=down/closed)
- `Sunshine`: External sunshine rank (0-3)

