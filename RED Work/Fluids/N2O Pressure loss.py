import numpy as np
import matplotlib.pyplot as plt
from CoolProp.CoolProp import PropsSI

# -------------------
# PIPE + FLOW PARAMETERS
# -------------------
fluid = "NitrousOxide"  # thermodynamics
visc_fluid = "CO2"  # viscosity model
D = 0.011938  # pipe diameter (m)
L = 7  # pipe length (m)
N = 200  # number of segments
dx = L / N
A = np.pi * D ** 2 / 4

eps = 0.0003  # pipe roughness (m)
m_dot = 2  # mass flow (kg/s)

# -------------------
# INLET CONDITIONS
# -------------------
T0 = 300.0  # K
P0 = PropsSI("P", "T", T0, "Q", 0, fluid)  # saturated liquid
h0 = PropsSI("H", "T", T0, "Q", 0, fluid)  # J/kg

# -------------------
# INITIALIZE ARRAYS
# -------------------
x = np.linspace(0, L, N + 1)
P = np.zeros(N + 1)
rho_m = np.zeros(N + 1)
v = np.zeros(N + 1)
x_quality = np.zeros(N + 1)

P[0] = P0


# -------------------
# FUNCTION TO COMPUTE FRICTION FACTOR (Swamee–Jain)
# -------------------
def friction_factor(Re, D, eps):
    if Re == 0:
        return 0
    return 0.25 / (np.log10(eps / (3.7 * D) + 5.74 / Re ** 0.9)) ** 2


# -------------------
# MAIN MARCHING LOOP
# -------------------
for i in range(N):
    # --- Saturated properties at current pressure ---
    try:
        h_f = PropsSI("H", "P", P[i], "Q", 0, fluid)
        h_g = PropsSI("H", "P", P[i], "Q", 1, fluid)
        rho_l = PropsSI("D", "P", P[i], "Q", 0, fluid)
        rho_v = PropsSI("D", "P", P[i], "Q", 1, fluid)
    except:
        # If outside PropsSI range, fallback
        h_f = h0
        h_g = h0
        rho_l = 1000.0
        rho_v = 1.0

    # --- Compute quality (HEM) ---
    if h0 <= h_f:
        x_q = 0.0
    else:
        x_q = (h0 - h_f) / (h_g - h_f)
        x_q = min(max(x_q, 0.0), 1.0)

    x_quality[i] = x_q

    # --- Mixture density ---
    rho_m[i] = 1 / (x_q / rho_v + (1 - x_q) / rho_l)

    # --- Velocity ---
    v[i] = m_dot / (rho_m[i] * A)

    # --- Dynamic viscosity (CO2) ---
    mu_l = PropsSI("V", "P", P[i], "Q", 0, visc_fluid)
    mu_v = PropsSI("V", "P", P[i], "Q", 1, visc_fluid)
    mu_m = (1 - x_q) * mu_l + x_q * mu_v

    # --- Reynolds number ---
    Re = rho_m[i] * v[i] * D / mu_m

    # --- Friction factor ---
    f = friction_factor(Re, D, eps)

    # --- Pressure drop (Darcy–Weisbach) ---
    dP = f * dx / D * 0.5 * rho_m[i] * v[i] ** 2

    # --- March pressure ---
    P[i + 1] = max(P[i] - dP, PropsSI("P", "T", T0, "Q", 0, fluid))  # clamp to saturated liquid

# Last segment quality & density
x_quality[-1] = x_quality[-2]
rho_m[-1] = rho_m[-2]
v[-1] = v[-2]

print(v)
# -------------------
# PLOTTING
# -------------------
plt.figure(figsize=(8, 5))
plt.plot(x, x_quality / 1e6, 'b-', label='Pressure (MPa)')
plt.xlabel("Distance along pipe (m)")
plt.ylabel("Pressure (MPa)")
plt.title("Pressure vs Pipe Distance (HEM with CO2 viscosity)")
plt.grid(True)
plt.legend()
plt.show()
