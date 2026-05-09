import numpy as np

# -----------------------
# INPUTS
# -----------------------

Pc = 750 * 6894.76        # chamber pressure (psi → Pa)
gamma = 1.22              # ratio of specific heats (CEA output)
Tc = 3000                 # chamber temperature (K) (CEA output)
R = 355                   # gas constant (J/kg/K) (CEA output)
epsilon = 9.5               # expansion ratio from CEA

De = 3.75 * 0.0254        # exit diameter (in → m)

# -----------------------
# GEOMETRY
# -----------------------

Ae = np.pi * (De/2)**2

At = Ae / epsilon

Dt = np.sqrt((4*At)/np.pi)

# -----------------------
# CHOKED FLOW MASS FLOW
# -----------------------

flow_term = np.sqrt(gamma/(R*Tc))

choke_term = (2/(gamma+1))**((gamma+1)/(2*(gamma-1)))

mdot = At * Pc * flow_term * choke_term

# -----------------------
# OUTPUTS
# -----------------------

print("Exit Area (m^2):", Ae)
print("Throat Area (m^2):", At)
print("Throat Diameter (in):", Dt / 0.0254)
print("Mass Flow Rate (kg/s):", mdot)