# 5DOF Rocket Flight Simulation - Setup & Workflow Guide

## Installation

### Prerequisites
- Python 3.11+ (verified with Python 3.11.3)
- pip (Python package manager)

### Install Dependencies

```bash
cd rocket-simulation-master
pip install -r requirements.txt
```

All required packages are now installed:
- **numpy** (1.24+): Numerical computing
- **pandas** (2.0+): Data analysis and CSV handling
- **scipy** (1.11+): Scientific computing (interpolation, stats, curve fitting)
- **matplotlib** (3.8+): Visualization and plotting
- **lmfit** (1.2+): Polynomial model fitting and curve fitting
- **pygame** (2.5+): 2D animation/visualization
- **jpype1** (1.5+): Java integration for OpenRocket (optional)

## Project Structure

```
rocket-simulation-master/
├── lib/                    # General-purpose libraries (decoupled from rockets)
│   ├── simulation.py       # Core RocketSimulation class
│   ├── logging/            # Data logging and tracking
│   ├── visualization.py    # Plot and display utilities
│   └── data.py             # General data handling
├── src/                    # Core simulation code
│   ├── environment.py      # Environment (wind, atmosphere, time steps)
│   ├── rocket.py           # Main Rocket class
│   ├── rocketparts/        # Components (motor, parachute, fins, etc.)
│   └── data/               # Data generation and models
├── example/                # Ready-to-run examples
│   ├── simulations/        # Example simulation scripts
│   ├── analysis/           # Analysis and Monte Carlo tools
│   └── visualization/      # Plotting and animation examples
└── test/                   # Unit tests
```

## Simulation Workflow

### 1. Basic Flight Simulation

The typical workflow for running a rocket flight simulation:

```python
from src.environment import Environment
from src.rocketparts.motor import Motor
from src.rocket import Rocket
from src.rocketparts.parachute import ApogeeParachute, Parachute
from lib.logging.logger import RocketLogger
from lib.simulation import RocketSimulation

# Step 1: Create environment (time step, atmospheric conditions, wind)
env = Environment(time_increment=0.01, apply_wind=True)

# Step 2: Define motor (thrust profile)
motor = Motor()

# Step 3: Define parachutes
drogue_parachute = ApogeeParachute(radius=0.3)
main_parachute = Parachute()

# Step 4: Create rocket with all components
rocket = Rocket(environment=env, motor=motor, parachutes=[drogue_parachute, main_parachute])

# Step 5: Initialize logger to track flight data
logger = RocketLogger(rocket)
logger.splitting_arrays = True

# Step 6: Create simulation engine
sim = RocketSimulation(
    apply_angular_forces=True,
    environment=env, 
    rocket=rocket, 
    logger=logger
)
motor.simulation = sim

# Step 7: Run the simulation
sim.run_simulation()

# Step 8: Access results via logger
# Results are saved to CSV and can be analyzed
```

### 2. Running Example Simulations

From the `example/simulations/` directory:

```bash
# Basic rocket flight
python simulaterocket.py

# Motor-only simulation
python simulatemotor.py

# Simplified rotation test
python SimplifiedRotationSimulation.py
```

**Note**: These scripts may have relative import issues. To fix, either:
1. Run from the project root and update imports to use `src.`
2. Add the project root to PYTHONPATH: `set PYTHONPATH=%cd%`

### 3. Monte Carlo Analysis

For sensitivity and uncertainty analysis:

```bash
cd example/analysis/
python FullMonteCarlo.py          # Run multiple flight simulations
python WindMonteCarlo.py          # Analyze wind sensitivity
python OpticalAnalysisMotorMonteCarlo.py  # Motor performance analysis
```

### 4. Visualization

After simulation:

```python
from example.visualization.sim_analysis.FlightOpticalAnalysis import display_optical_analysis

# Assuming sim is a completed RocketSimulation
display_optical_analysis(sim.logger.full_path)
```

## Output & Results

### CSV Files
Flight logs are saved as CSV files containing:
- **position** (x, y, z): Rocket position over time
- **velocity** (vx, vy, vz): Rocket velocity
- **acceleration** (ax, ay, az): Rocket acceleration
- **rotation**: Pitch and yaw angles
- **angular_velocity**: Rotation rates
- **angular_acceleration**: Rotation accelerations
- **motor_thrust**: Thrust output over time
- **parachute_deployment**: Parachute events

### Analysis & Plotting
Use matplotlib-based visualization tools in `example/visualization/`:
- Flight optical analysis (trajectory, altitude, velocity)
- Stability analysis
- Motor performance graphs
- Wind impact comparison
- Third-party simulation comparison (OpenRocket, RASAero)

## Key Classes

### Environment
Controls simulation environment (time step, wind, atmospheric conditions)

### Rocket
Main rocket object handling:
- Aerodynamics calculations
- Center of gravity tracking
- Motor and parachute integration
- Force and torque calculations

### Motor
Motor thrust profile and combustion simulation

### RocketSimulation
Main simulation loop that integrates forces and solves differential equations

### RocketLogger
Tracks and records simulation data to CSV

## Advanced Features

### 1. Custom Motor Models
- Use `CustomMotor` for manual thrust curve definition
- Pre-defined motors available via `Motor` class

### 2. Parametric Analysis
Sensitivity studies for:
- Grain geometry
- Dry mass optimization
- Burn time effects
- C-star efficiency
- Oxidizer temperature

### 3. Genetic Algorithms
Optimize rocket design parameters using:
- `GeneticSelectionForParachutes.py`
- `GeneticSelectionForGoddardProblem.py`

### 4. OpenRocket Integration
For users who want to compare with OpenRocket simulations:
- Requires Java and OpenRocket JAR file
- Set `OR_JAR_PATH` environment variable
- See `example/analysis/OpenRocketAnalysis/`

## Troubleshooting

### Import Errors
If you get `ModuleNotFoundError`, ensure:
1. You're in the `rocket-simulation-master` directory
2. PYTHONPATH includes the project root: `set PYTHONPATH=.`
3. All `__init__.py` files exist in lib/, src/, and subdirectories

### Missing Dependencies
```bash
pip install -r requirements.txt
```

### OpenRocket Integration Errors
jpype1 integration is optional. If you don't use OpenRocket:
- You can safely ignore jpype errors
- Or remove jpype1 from requirements.txt

## Documentation

- **README.md**: Project overview and philosophy
- **doc/calculations.md**: Detailed physics and math implementation
- **doc/design_notes.md**: Architecture and design decisions
- **doc/example.md**: Example organization

## Notes

- This code was written as reference material for future Brazoswood Goddard teams
- It's not a library replacement for OpenRocket, but a complement
- The code is research/education-focused, not production-hardened
- Comments describe "why" not "what" - class and function names are self-documenting
