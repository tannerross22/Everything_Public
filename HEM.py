
from CoolProp.CoolProp import PropsSI
import matplotlib.pyplot as plt
import scipy.optimize as opt
import scipy.interpolate as int
import numpy as np
import math

# Define the fluid and known conditions
fluid = 'NitrousOxide'
inj_dP = 2.608             # MPa (300 psi)
P_inlet = 4137000          # Inlet pressure in Pa
T_inlet = 268              # Inlet temperature in K
A = math.pi*(6.0/2000)**2  # Cross-sectional area in m^2 (example value)
C_d = 0.63                 # Discharge coefficient (example value)

# Calculate the inlet specific enthalpy and density
h_inlet = PropsSI('H', 'P', P_inlet, 'T', T_inlet, fluid)  # Inlet specific enthalpy in J/kg
rho_inlet = PropsSI('D', 'P', P_inlet, 'T', T_inlet, fluid)  # Inlet density in kg/m^3

# Initialize lists to store results
pressure_drops = []
mass_flow_rates_HEM = []
mass_flow_rates_incompressible = []
mass_flow_rates_NHNE = []
mass_flow_rates_MOHM = []
vapor_mass_fractions = []

g_low_lst = []

# Initialize variable to hold the maximum mass flow rate for HEM
max_mass_flow_rate_HEM = 0.0

# Iterate over a range of downstream pressures
# range(int(P_inlet), int(P_inlet * 0.1), -int(P_inlet * 0.01))
for P_outlet in np.linspace(P_inlet*0.99, P_inlet*0.1, 1000):
    # Calculate the pressure drop
    delta_P = P_inlet - P_outlet
    pressure_drops.append(delta_P/1e6)

    # HEM Calculation
    # Calculate the outlet specific enthalpy and density
    h_outlet = PropsSI('H', 'P', P_outlet, 'S', PropsSI('S', 'P', P_inlet, 'T', T_inlet, fluid), fluid)
    rho_outlet = PropsSI('D', 'P', P_outlet, 'H', h_outlet, fluid)  # Outlet density in kg/m^3

    # Dyer NHNE model properties
    P_sat = PropsSI('P', 'T', T_inlet, 'Q', 0, fluid)
    kappa = np.sqrt((P_inlet-P_outlet)/(P_sat-P_outlet))

    # Omega model properties
    Cp_inlet = PropsSI('C', 'P', P_inlet, 'T', T_inlet, fluid)
    rho_inlet = PropsSI('D', 'P', P_inlet, 'T', T_inlet, fluid)
    rho_inlet_gas = PropsSI('D', 'T', T_inlet, 'Q', 1, fluid)
    h_inlet_gas = PropsSI('H', 'T', T_inlet, 'Q', 1, fluid)

    v_LG = abs((1/rho_inlet_gas)-(1/rho_inlet))
    h_LG = abs(h_inlet_gas-h_inlet)
    omega = Cp_inlet*T_inlet*P_sat*rho_inlet*((v_LG/h_LG)**2)

    n_st = 2*omega/(1+(2*omega))
    n_s = P_sat/P_inlet
    n = P_outlet/P_inlet
    
    def func(n_c):
        return (n_c**2) + ((omega**2)-(2*omega))*((1-n_c)**2) + 2*(omega**2)*np.log(n_c) + 2*(omega**2)*(1-n_c)
    n_c = opt.newton(func, n)

    G_low = (np.sqrt(P_inlet*rho_inlet)*(np.sqrt(2*(1-n_s) + (2*(omega*n_s*np.log(n_s/n_c)) - ((omega-1)*(n_s-n_c)))))) / ((omega*((n_s/n_c)-1))+1)
    G_sat = np.sqrt(P_inlet*rho_inlet)*(n_c/np.sqrt(omega))

    G_MOHM = ((P_sat/P_inlet)*G_sat) + ((1-(P_sat/P_inlet))*G_low)
    mass_flow_rates_MOHM.append(G_MOHM*A)
    g_low_lst.append(G_sat)

    # Calculate the mass flow rate using HEM
    mass_flow_rate_HEM = C_d * A * rho_outlet * math.sqrt(2 * (h_inlet - h_outlet))

    # Check if this flow rate is less than the previous maximum (indicating choked flow)
    if mass_flow_rate_HEM < max_mass_flow_rate_HEM:
        # Hold the maximum mass flow rate if choked flow occurs
        mass_flow_rate_HEM = max_mass_flow_rate_HEM
    else:
        # Update the maximum mass flow rate
        max_mass_flow_rate_HEM = mass_flow_rate_HEM

    mass_flow_rates_HEM.append(mass_flow_rate_HEM)

    # Traditional Incompressible Flow Calculation
    mass_flow_rate_incompressible = C_d * A * math.sqrt(2 * rho_inlet * delta_P)
    mass_flow_rates_incompressible.append(mass_flow_rate_incompressible)

    mass_flow_rate_NHNE = ((1-(1/(1+kappa)))*mass_flow_rate_incompressible) + ((1/(1+kappa))*mass_flow_rate_HEM)
    mass_flow_rates_NHNE.append(mass_flow_rate_NHNE)

# Format and interpolate Razavi model spline
for i in range(len(mass_flow_rates_MOHM)):
    if (mass_flow_rates_MOHM[i] > mass_flow_rates_NHNE[i]):
        blend_point = i
mass_flow_rates_MOHM[:blend_point] = mass_flow_rates_NHNE[:blend_point]
MOHM_spl = int.interp1d(pressure_drops, mass_flow_rates_MOHM)

print(f'Injector mass flow rate: {MOHM_spl(inj_dP)} kg/s')

# Plotting the results
fig, ax1 = plt.subplots()

# Plot mass flow rate vs. pressure drop for HEM
color = 'tab:blue'
ax1.set_xlabel('Pressure Drop (MPa)')
ax1.set_ylabel('Mass Flow Rate (kg/s)')
ax1.plot(pressure_drops, mass_flow_rates_HEM, color=color, label="HEM")
ax1.plot(pressure_drops, mass_flow_rates_incompressible, color='tab:green', linestyle='-.', label="SPI")
ax1.plot(pressure_drops, mass_flow_rates_NHNE, 'r', label='NHNE')
ax1.plot(pressure_drops, mass_flow_rates_MOHM, 'c', label='MOHM')
ax1.vlines(inj_dP, min(mass_flow_rates_HEM), max(mass_flow_rates_incompressible), 'k', label='Injector dP')


# Title and legends
fig.suptitle('Mass Flow Rate and Vapor Mass Fraction vs. Pressure Drop')
fig.legend(loc='upper left', bbox_to_anchor=(0.1, 0.9))

# Show plots
plt.grid(True)
plt.show()
