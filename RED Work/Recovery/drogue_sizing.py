import numpy as np
import matplotlib.pyplot as plt

# -----------------------------
# VEHICLE INPUTS
# -----------------------------

print("=== Vehicle ===")
W = float(input("Vehicle weight W (lbf): "))

print("\n=== Velocities ===")
V_drogue_deploy = float(input("Drogue deployment velocity (ft/s): "))
V_impact = float(input("Target impact velocity (ft/s): "))

# -----------------------------
# DROGUE CONSTANTS
# -----------------------------

print("\n=== Drogue Parachute Constants ===")
rho_d = float(input("Air density at drogue altitude (slug/ft^3): "))
Cd_d = float(input("Drogue Cd: "))
X1_d = float(input("Drogue X1: "))
Cx_d = float(input("Drogue Cx: "))

# -----------------------------
# MAIN CONSTANTS
# -----------------------------

print("\n=== Main Parachute Constants ===")
rho_m = float(input("Air density at main altitude (slug/ft^3): "))
Cd_m = float(input("Main Cd: "))
X1_m = float(input("Main X1: "))
Cx_m = float(input("Main Cx: "))

# -----------------------------
# DROGUE AREA SWEEP
# -----------------------------

print("\n=== Drogue Area Sweep ===")
S_d_min = float(input("Min drogue area (ft^2): "))
S_d_max = float(input("Max drogue area (ft^2): "))
N = int(input("Number of points: "))

S_d = np.linspace(S_d_min, S_d_max, N)

# -----------------------------
# SOLVE MAIN CHUTE AREA (FIXED)
# -----------------------------

S_m = (2 * W) / (rho_m * Cd_m * X1_m * Cx_m * V_impact**2)

print(f"\nSolved main parachute area: {S_m:.2f} ft^2")

# -----------------------------
# ITERATION
# -----------------------------

F_drogue = []
F_main = []
V_main_deploy = []

for Sd in S_d:
    # Drogue opening force at deployment
    q_d = 0.5 * rho_d * V_drogue_deploy**2
    Fd = Cd_d * Sd * X1_d * Cx_d * q_d

    # Terminal velocity under drogue (main deployment velocity)
    Vmd = np.sqrt(
        (2 * W) / (rho_d * Cd_d * Sd * X1_d * Cx_d)
    )

    # Dynamic pressure at main deployment
    q_m = 0.5 * rho_m * Vmd**2

    # Main opening force
    Fm = Cd_m * S_m * X1_m * Cx_m * q_m

    F_drogue.append(Fd)
    F_main.append(Fm)
    V_main_deploy.append(Vmd)

# -----------------------------
# PLOTTING
# -----------------------------

plt.figure(figsize=(8,5))

plt.plot(S_d, F_drogue, label="Drogue Opening Force")
plt.plot(S_d, F_main, "--", label="Main Opening Force")

plt.xlabel("Drogue Area (ft²)")
plt.ylabel("Force (lbf)")
plt.title("Opening Force vs Drogue Size (User Force Model)")
plt.grid(True)
plt.legend()
plt.show()