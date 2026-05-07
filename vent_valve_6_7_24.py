import numpy as np
import matplotlib.pyplot as plt

# Constants
# vol = 0.386  # gallons
vol = 89.166 #in^3
# R = 1545.35  # J/mol*K
R = 661.98 #in*lbf/lb*R
P_tank = 764.7  #psi
P_atm = 14.7  #psi
Cv = .14 # 0.14 Cv
t = 0
step = 0.01  # seconds
sonic = 1.895  # minimum required ratio for choked flow
G = 0.9669
T = 547.67  # rankine
T_std = 530  # rankine
P_std = 14.7  # psi
# P_std = 101352.9 #Pa
M = 28.01  # lb/lb*mol

# Initial mass calculation
mass = vol* P_tank * M / (R * T) #lb

# Function to check for choked flow
def choked(P_tank, P_atm):
    return P_tank > 2 * P_atm

# Lists to store time, flows, and pressures
tim = []
flows = []
p_tanks = []

# Simulation loop
while P_tank > P_atm:
    if choked(P_tank, P_atm):
        flow = (Cv * 816 * P_tank / np.sqrt(G * T))*(12**3/3600) #in^3/s

        # Convert flow to mass flow rate (lb/s)
        mass_flow = flow * (P_std / P_tank) * (T / T_std) * M * P_tank / (R * T)
    else:
        flow = Cv * 962 * np.sqrt((P_tank**2 - P_atm**2) / (G * T))

        # Convert flow to mass flow rate (lb/s)
        mass_flow = flow * (P_std / P_tank) * (T / T_std) * M * P_tank / (R * T)

    # Update mass and pressure
    mass -= mass_flow * step
    P_tank = ((mass / M) * R * T)/ vol #psi

    # Store data for plotting
    tim.append(t)
    flows.append(flow)
    p_tanks.append(P_tank)

    # Increment time
    t += step

# Plot results
plt.plot(tim, p_tanks)
plt.xlabel('Time (s)')
plt.ylabel('Tank Pressure (psi)')
plt.title('Tank Pressure vs. Time')
plt.show()


