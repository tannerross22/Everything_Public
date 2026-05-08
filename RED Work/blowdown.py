import numpy as np
import matplotlib.pyplot as plt

# True for Gauge or False for Absolute
unit_bool = True

# Initial Pressure in Tank/Volume
P0 = 3000  # PSIA/PSIG

# Final Pressure in Tank/Volume
PF = 700  # PSIA/PSIG

# Ambient Pressure (venting to pressure of...)
PA = 0  # PSIA/PSIG

# Volume of Tank/Volume
V = 1403  # in^3

# Temperature in Tank
T = 80  # degF

# Discharge Coefficient of Orifice
Cd = 0.65  # Unitless

# Diameter of Orifice
D = 0.461  # in

# N2 = Nitrogen
# O2 = Oxygen
# GP = Propane
GAS = 'N2'

"""
def sonic(gamma, T, R, P0, Cd, A):
    g = 32.2; # Gravitational Acceleration (ft/s^2)
    return Cd*A*P0 * np.sqrt( (gamma*g)/(T*R) * np.power(2/(gamma+1), (gamma+1)/(gamma-1)) )

def subsonic(gamma, T, R, P0, p_ratio, Cd, A):
    g = 32.2; # Gravitational Acceleration (ft/s^2)
    p_ratio = PF/P0; # Pressure Ratio
    return Cd*A*P0 * np.sqrt( (gamma*g)/(T*R) * 2/(gamma-1) * np.power(p_ratio, 1/gamma) * ( np.power(p_ratio, 1/gamma) - p_ratio ) )
"""


def sonic(gamma, T, R, P0, Cd, A):
    g = 32.2 # Gravitational Acceleration (ft/s^2)
    return Cd*A*np.sqrt(((P0**2*g)/R*T)*gamma*np.power((2/(gamma+2)),((gamma+1)/(gamma-1))))


def subsonic(gamma, T, R, P0, p_ratio, Cd, A):
    g = 32.2  # Gravitational Acceleration (ft/s^2)
    p_ratio = PF/P0  # Pressure Ratio
    return (Cd*A*P0/np.sqrt(T))*np.sqrt((2*g*gamma)/(((gamma-1)*R)*(p_ratio**(2/gamma)-p_ratio**((gamma+1)/gamma))))


# To add a new gas, add a new key to this dictionary
# The first entry in each list is the molar mass of the gas
# The second entry in each list is the specific heat ratio of the gas
GAS_PROPERTIES = {'N2': [28.0134, 1.40],
                  'O2': [31.9988, 1.40],
                  'GP': [44.0970, 1.13]}

R_UNIVERSAL = 1545.34896  # Universal Gas Constant (lbf * ft / degR * lb-mol)
molar_mass = GAS_PROPERTIES[GAS][0]  # Molar mass (lbm/lb-mol)
gamma = GAS_PROPERTIES[GAS][1]  # Specific Heat Ratio

R = R_UNIVERSAL / molar_mass  # Specific Gas Constant (lbf * ft / degR * lbm)

# Pressure Unit Conversion (PSI -> PSF)
if unit_bool:  # PSIG -> PSIA
    P0 += 14.7
    PF += 14.7
    PA += 14.7
# PSIA -> PSFA
P0 *= 144
PF *= 144
PA *= 144

# Temperature
T += 460

# Volume
V /= np.power(12, 3)

# Area
A = np.pi * (D / 24) ** 2  # ft^2

# Time Variables for Iteration
TIMESTEP = 0.0001  # Step size for iteration (s)
time = 0.0001  # Initial time (s)

# Starting Properties
rho = P0 / (R * T)  # Gas Density (lbm/ft^3)
mass = rho * V  # Mass (lbm)
m_dot = 0
p_ratio = PF/P0
# Variables for Graphing
pressures = [P0 / 144]
masses = [mass]
times = [time]
mdots = [m_dot]
pratios = [p_ratio]
rhos = [rho]

while P0 > PF:

    p_crit = np.power(2 / (gamma + 1), gamma / (gamma - 1))  # Critical Pressure Ratio
    p_ratio = PF / P0  # Pressure Ratio

    # Mass Flow Rate (lbm/s)
    if p_ratio <= p_crit:
        m_dot = sonic(gamma, T, R, P0, Cd, A)  # Mass Flow Rate in lbm/s
    else:
        m_dot = subsonic(gamma, T, R, P0, p_ratio, Cd, A)  # Mass Flow Rate in lbm/s

    mass -= m_dot * TIMESTEP  # Mass (lbm)
    time += TIMESTEP  # Time (s)

    rho = mass / V  # Density (lbm/ft^3)
    P0 = rho * R * T  # Pressure (lbf/ft^2)

    pressures.append(P0 / 144)
    masses.append(mass)
    times.append(time)
    mdots.append(m_dot)
    pratios.append(p_ratio)
    rhos.append(rho)

    # pressure and mass vs time
fig, ax1 = plt.subplots(layout='constrained')
ax1.grid(c='gainsboro')
ax2 = ax1.twinx()
ax1.plot(times, pressures, c='lightcoral')
ax1.set_ylabel('Tank Pressure (psia)')
ax2.plot(times, masses, c='indigo')
ax2.set_ylabel('Fluid Mass (lbm)')
plt.title('Tank Pressure and Mass vs Time')
plt.show()
# mass flow rate vs time
fig, ax1 = plt.subplots(layout='constrained')
ax1.grid(c='gainsboro')
ax2 = ax1.twinx()
ax1.plot(times, mdots, c='lightcoral')
ax1.set_ylabel('Mass Flow Rate lbm/s')
plt.title('Mdot vs Time')
plt.show()
# pressure ratio vs time
fig, ax1 = plt.subplots(layout='constrained')
ax1.grid(c='gainsboro')
ax2 = ax1.twinx()
ax1.plot(times, pratios, c='lightcoral')
ax1.set_ylabel('Pressure Ratio')
plt.title('Pressure Ratio vs Time')
plt.show()
print(max(masses) / max(rhos))
print(f'Time to Blow Down: {time * 1000:.2f} ms')