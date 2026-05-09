#!/usr/bin/env python3
"""Quick test of rocket flight simulation"""

import numpy as np

from src.environment import Environment
from src.rocket import Rocket
from src.rocketparts.motor import Motor
from src.rocketparts.parachute import Parachute, ApogeeParachute
from src.simulation.rocket.logger import RocketLogger
from src.simulation.rocket.simulation import RocketSimulation
from src.data.input.models import (
    get_coefficient_of_lift as splined_CL,
    get_splined_coefficient_of_drag as splined_CD,
)


# Wrap the bisplev-based aero lookups so they:
#   - clamp inputs to the data table's valid range (Mach 0-25, Alpha 0-4 deg)
#   - cast the 0-d numpy array result back to a plain float
# Spline funcs expect alpha in radians; they convert internally.
_ALPHA_MAX_RAD = np.deg2rad(4.0)
_MACH_MAX = 25.0


def cl_from_data(mach, alpha):
    m = max(0.0, min(float(mach), _MACH_MAX))
    a = max(0.0, min(abs(float(alpha)), _ALPHA_MAX_RAD))
    return float(splined_CL(m, a))


def cd_from_data(mach, alpha):
    m = max(0.0, min(float(mach), _MACH_MAX))
    a = max(0.0, min(abs(float(alpha)), _ALPHA_MAX_RAD))
    return float(splined_CD(m, a))

print("=" * 60)
print("5DOF ROCKET FLIGHT SIMULATION - TEST RUN")
print("=" * 60)
print()

print("Initializing simulation...")
env = Environment(time_increment=0.01, apply_wind=True)
motor = Motor()
drogue = ApogeeParachute(radius=0.3)
main = Parachute()
rocket = Rocket(environment=env, motor=motor, parachutes=[drogue, main])

# Hook up Mach/AoA-dependent CL and CD from the splined aerodynamicQualities.csv data
# (RASAero output). Without these, CL=0 (no lift, no aero torque) and CD=0.7 (constant).
rocket.set_CL_function(cl_from_data)
rocket.set_CD_function(cd_from_data)

# Tilt the launch 3 deg off vertical so there is a non-zero angle of attack to actually
# exercise the lift/torque path; otherwise pitch stays exactly 0 and CL stays 0.
# Rotation(around, down) — down is the polar angle from +z, around is azimuth.
rocket.rotation = type(rocket.rotation)(np.pi / 2, np.deg2rad(3.0))

logger = RocketLogger(rocket)
logger.splitting_arrays = True

sim = RocketSimulation(apply_angular_forces=True, environment=env, rocket=rocket, logger=logger)
motor.simulation = sim

print("Rocket initialized:")
print(f"  Total mass (rocket + motor): {rocket.total_mass:.2f} kg")
print(f"  Motor thrust at t=0 (from curve): {motor.thrust_data.iloc[0]['thrust']:.2f} N")
print(f"  Total impulse: {motor.total_impulse:.0f} N*s    burn time: {motor.burn_time:.2f} s")
print(f"  Time increment: {env.time_increment} s")
print(f"  Wind: Enabled")
print(f"  CL/CD: splined from aerodynamicQualities.csv (Mach 0-25, AoA 0-4 deg)")
print(f"  Launch tilt: 3 deg from vertical")
print(f"  CL at (Mach=1.0, AoA=2 deg): {cl_from_data(1.0, np.deg2rad(2)):.4f}")
print(f"  CD at (Mach=1.0, AoA=0 deg): {cd_from_data(1.0, 0.0):.4f}")
print()
print("Running simulation...")
print()

try:
    sim.run_simulation()
    print()
    print("=" * 60)
    print("SUCCESS: Simulation completed!")
    print("=" * 60)
    print(f"Total simulation time: {sim.time:.2f} seconds")
    print(f"Total frames: {sim.frames}")
    print(f"Output file: {logger.full_path}")
    print()

except Exception as e:
    print()
    print("=" * 60)
    print("ERROR during simulation:")
    print("=" * 60)
    print(str(e))
    import traceback
    traceback.print_exc()
