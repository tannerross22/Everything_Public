---
title: 5DOF Rocket Flight Simulation
category: Engineering Projects
status: Active
last_updated: 2026-05-12
tags: [hybrid rocket, flight dynamics, Monte Carlo, optimization, simulation]
related_files:
  - ../Valero%20Standards/API_571_Damage_Mechanisms.md
---

# 5DOF Rocket Flight Simulation

## Overview

A comprehensive Python-based hybrid rocket flight simulation system developed for Brazoswood's Goddard Program. Models 5 degrees of freedom (position + rotation) for accurate flight trajectory prediction. Used for design optimization, pre-flight analysis, and post-flight data comparison. Historical record: 5/5 successful flights with apogee reaching 43,000 feet in 2022.

## Project Purpose

The simulation serves three main functions:
1. **Design Optimization** — Parametric studies to determine optimal motor performance, tank design, grain geometry, burn time
2. **Pre-Flight Analysis** — Monte Carlo simulations accounting for wind, mass uncertainty, aerodynamic variations
3. **Post-Flight Analysis** — Comparing actual flight data (telemetry) against predicted trajectories to validate models

## Architecture

### Core Components

| Component | Purpose | Key Classes |
|-----------|---------|-------------|
| **Motor** | Combustion modeling and thrust curve generation | `Motor`, `CustomMotor` |
| **Rocket** | Aerodynamics, mass/CG calculations, physics integration | `Rocket` (handles fins, body, nosecone) |
| **Parachute** | Descent simulation, deployment logic | `Parachute`, `ApogeeParachute` |
| **Environment** | Atmospheric conditions, wind, time stepping | `Environment` |
| **Simulation** | Physics loop (force/torque → acceleration → state update) | `RocketSimulation` |
| **Logger** | Data collection and event tracking | `RocketLogger` |

### Project Structure

```
rocket-simulation-master/
├── src/                    # Core simulation library
│   ├── rocketparts/       # Motor, parachute, component models
│   └── ...
├── example/               # Analysis and execution scripts
│   ├── simulations/       # Basic flight simulations
│   ├── analysis/          # Monte Carlo, parametric studies
│   │   ├── ParametricAnalysis/    # Optimization studies
│   │   ├── MonteCarloFlightData/  # Uncertainty quantification
│   │   └── OpenRocketAnalysis/    # Integration with OpenRocket
│   ├── design/            # Rocket & motor design calculations
│   ├── data/              # Environmental inputs, flight telemetry
│   └── constants.py       # Shared parameters
├── doc/                   # Documentation
│   ├── calculations.md    # Equations and derivations
│   ├── design_notes.md    # Programming conventions
│   └── example.md         # Usage examples
└── README.md
```

## Technical Details

### Flight Simulation Loop

1. **Initialize**: Create `Rocket`, `Motor`, `Environment`, `Parachute` objects
2. **Set References**: Link objects so each knows about its dependencies
3. **Run Loop** (each timestep):
   - Calculate forces: aerodynamic drag, gravity, thrust
   - Calculate torques: aerodynamic moments, CG offset
   - Update state: velocity, position, rotation, angular velocity
   - Log data
   - Check parachute deployment events
4. **Output**: CSV file with position, velocity, rotation, acceleration traces

### Key Physics Models

- **Aerodynamics**: Barrowman method for fin lift/drag + body drag tables
- **Mass/CG**: Dynamic lookup tables based on fuel consumption (mass burning)
- **Motor**: Thrust curve from burning solid/hybrid grain (CEA for combustion thermodynamics)
- **Wind**: Constant or altitude-dependent wind profiles
- **Parachute**: Instant deployment or altitude/velocity triggered

### Entry Point Example

```python
from environment import Environment
from src.rocketparts.motor import Motor
from rocket import Rocket
from src.rocketparts.parachute import ApogeeParachute, Parachute
from logger import RocketLogger 
from simulation import RocketSimulation

# Setup
env = Environment({"time_increment": 0.1})
motor = Motor()
drogue = ApogeeParachute({"radius": 0.2})
main = Parachute()
rocket = Rocket(environment=env, motor=motor, parachutes=[drogue, main])

logger = RocketLogger(rocket, ['position', 'velocity', 'acceleration', 'rotation', 'angular_velocity', 'angular_acceleration'])
sim = RocketSimulation(environment=env, rocket=rocket, logger=logger)

# Run
sim.run_simulation()
```

## Analysis Capabilities

### Parametric Studies (in `ParametricAnalysis/`)

- **Grain Geometry** — Length, diameter, regression rate effects
- **Nozzle Design** — Expansion ratio optimization
- **Tank Design** — Oxygen tank dimensions and mass impact
- **Parachute Selection** — Descent rate vs. drift
- **Atmospheric Conditions** — Sensitivity to temperature, pressure, wind

### Monte Carlo Uncertainty Quantification

- **Flight Monte Carlo** — Runs N simulations with randomized initial conditions
- **Motor Monte Carlo** — Variation in thrust curve, burn time
- **Wind Monte Carlo** — Multiple wind profiles
- **Optical Analysis** — Camera-based tracking vs. telemetry comparison

Outputs: Statistical distributions of apogee, max velocity, landing location, etc.

### Data Integration

- **OpenRocket Comparison** — Can import OR drag data and compare predictions
- **Telemetry Correlation** — Compares actual flight (Telemetrum, StratoLogger) with simulation
- **Third-Party Validation** — RaSAero, RockSim comparison data available

## Design Conventions

- **Naming**: Functions use prefixes for clarity:
  - `get_*` — Returns a computed value
  - `set_*` — Configures a property
  - `calculate_*` — Performs computation with side effects
  - `determine_*` — Optimization functions
  - `find_*` — Helper/search functions
  
- **Presets**: Objects support preset configurations (save/load via config dicts)
- **File Naming**: Executable files start with capital letter (e.g., `SimulateRocket.py`)
- **Separation of Concerns**: 
  - `lib/` — Reusable code independent of rockets/motors
  - `src/` — Core simulation classes
  - `example/` — Analysis scripts and entry points

## Visualization & Output

- **Matplotlib Graphs**: Altitude vs. time, velocity profiles, apogee distribution
- **CSV Export**: Full trajectory data for post-processing
- **Blender Integration**: `ToBlender.py` exports 3D flight path (runs inside Blender)

## Known Limitations & TODOs

- Code designed as reference/portfolio, not production library
- Some files have outdated comments; design_notes.md needs refresh
- Testing framework incomplete
- Presets/saving functionality partially implemented
- Would benefit from unified rocket simulation base class (for OpenRocket wrapper)

## Recent Work / Status

Last major work (2022): Flight model validated against 43,000 ft test flight. All core components functional. Ready for new design cycles or model improvements.

**Outstanding items:**
- Full test coverage for main entry points
- Refactor logger variable naming scheme
- Complete preset/save functionality
- Merge pending git branches with major improvements

## How to Use This File

When working on 5DOF improvements or analysis:
1. Check this file for architecture overview and component relationships
2. Refer to `doc/` folder in the repo for detailed equations and design notes
3. Use example analysis scripts as templates for new studies
4. See `example/constants.py` for shared configuration

Each update to this project should refresh the "last_updated" date and the "Current Status / Known Issues" section.
