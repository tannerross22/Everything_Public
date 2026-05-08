import numpy as np
import matplotlib.pyplot as plt

# -----------------------------
# USER INPUTS
# -----------------------------

print("=== Vehicle Properties ===")
weight = float(input("Vehicle weight (lbf): "))

print("\n=== Velocity Targets ===")
V_deploy = float(input("Drogue deployment velocity (ft/s): "))
V_impact = float(input("Target impact velocity (ft/s): "))

print("\n=== Drogue Parachute Inputs ===")
rho_drogue = float(input("Air density at drogue altitude (slug/ft^3): "))
Cd_drogue = float(input("Drogue drag coefficient Cd: "))
drogue_areas = input(
    "Enter drogue areas to iterate (ft^2, comma-separated): "
)
drogue_areas = [float(a) for a in drogue_areas.split(",")]

print("\n=== Main Parachute Inputs ===")
rho_main = float(input("Air density at main altitude (slug/ft^3): "))
Cd_main = float(input("Main chute drag coefficient Cd: "))

# -----------------------------
# SOLVE FOR MAIN CHUTE AREA
# -----------------------------

S_main = (2 * weight) / (rho_main * Cd_main * V_impact**2)

print(f"\nSolved main parachute area: {S_main:.2f} ft^2")

# -----------------------------
# VELOCITY RANGES
# -----------------------------

V_drogue = np.linspace(V_deploy, V_impact, 300)
V_main = np.linspace(V_impact, V_deploy * 0.4, 300)

# -----------------------------
# FORCE MODEL
# -----------------------------

def drag_force(rho, Cd, S, V):
    return 0.5 * rho * Cd * S * V**2

# -----------------------------
# PLOTTING
# -----------------------------

plt.figure()

# Drogue curves
for S_d in drogue_areas:
    F_d = drag_force(rho_drogue, Cd_drogue, S_d, V_drogue)
    plt.plot(V_drogue, F_d, label=f"Drogue S = {S_d:.1f} ft²")

# Main curve (solved area)
F_main = drag_force(rho_main, Cd_main, S_main, V_main)
plt.plot(V_main, F_main, "--", linewidth=2,
         label=f"Main chute (S = {S_main:.1f} ft²)")

# -----------------------------
# FORMATTING
# -----------------------------

plt.xlabel("Velocity (ft/s)")
plt.ylabel("Drag / Opening Force (lbf)")
plt.title("Opening Force vs Velocity (Solved Main Area)")
plt.grid(True)
plt.legend()
plt.show()