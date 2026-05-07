import numpy as np
import matplotlib.pyplot as plt

# Constants
R = 287.05  # Specific gas constant for nitrogen (J/kg-K)
Cv = 743  # Specific heat capacity at constant volume (J/kg-K)
Cp = 1040  # Specific heat capacity at constant pressure (J/kg-K)
gamma = Cp / Cv  # Heat capacity ratio

# Initial conditions
tank_volume = 0.05  # m^3 (50 liters)
initial_tank_pressure = 1e5  # Pa (1 atm = 101325 Pa)
initial_tank_temperature = 300  # K (room temperature)
regulator_pressure_outlet = 625 * 6894.76  # Convert psi to Pa
back_pressure_inlet = 2300 * 6894.76  # Convert psi to Pa
time_step = 0.1  # seconds
max_time = 600  # seconds (10 minutes)

# Provided outlet pressure (psi) and corresponding SCFM values
outlet_pressures_psi = np.array([625, 590, 570, 550, 535, 525, 515, 500, 490, 460, 425, 350, 225])
flow_rates_scfm = np.array([0, 10, 20, 40, 60, 80, 100, 120, 140, 160, 180, 200, 220])
time =0

pressure = initial_tank_pressure
time_points = []
pressures =[]
temperatures = []
mass_flow_rates = []
mass_flow = 0
temperature = 300

def flow_rate(downstream_pressure):
    if downstream_pressure < outlet_pressures_psi[-1] * 6894.76:
        SCFM =
    SCFM = np.interp(downstream_pressure, outlet_pressures_psi*6894.76, flow_rates_scfm)
    return SCFM*1.975*3600 # mass flow in kg/s
print(flow_rate(101325))
while time < max_time and pressure < regulator_pressure_outlet:
    mass_flow += flow_rate(pressure)
    mass_flow_rates.append(mass_flow)

    time+=time_step
    time_points.append(time)

print(mass_flow_rates)
plt.figure(figsize=(10, 6))

# Plot pressure
plt.subplot(3, 1, 1)
plt.plot(time_points[:len(pressures)], pressures)
plt.xlabel('Time (s)')
plt.ylabel('Pressure (Pa)')
plt.title('Tank Pressure Over Time')

# Plot temperature
plt.subplot(3, 1, 2)
plt.plot(time_points[:len(temperatures)], temperatures)
plt.xlabel('Time (s)')
plt.ylabel('Temperature (K)')
plt.title('Tank Temperature Over Time')

# Plot mass flow rate
plt.subplot(3, 1, 3)
plt.plot(time_points[:len(mass_flow_rates)], mass_flow_rates)
plt.xlabel('Time (s)')
plt.ylabel('Mass Flow Rate (kg/s)')
plt.title('Mass Flow Rate Over Time')

plt.tight_layout()
plt.show()
