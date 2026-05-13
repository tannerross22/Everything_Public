import numpy as np
import matplotlib.pyplot as plt

# Constants
gamma = 1.2  # Specific heat ratio for air
R = 287  # Specific gas constant for air in J/kg.K
C_p = gamma * R / (gamma - 1)  # Specific heat capacity at constant pressure
V = 0.007  # Volume of the receiving container in cubic meters
T0 = 298  # Initial temperature in Kelvin for the receiving container
P_upstream = 1.52e+7  # Upstream pressure in Pascals (high-pressure cylinder)
T_upstream = 298  # Temperature of gas in the high-pressure cylinder
P_downstream = 101325  # Initial pressure in the receiving container in Pascals
Cd = 0.63  # Discharge coefficient
A = 0.0000256  # Area of the orifice in square meters
h = 237  # Heat transfer coefficient (W/m^2.K)
A_wall = 0.534838  # Surface area of the container for heat transfer (in square meters)
T_ambient = 298  # Ambient temperature in Kelvin
P_set = 4.30e+6  # Set pressure for the regulator in Pascals

# Simulation parameters
time_step = 0.001  # Time step in seconds
total_time = 10  # Total time for the simulation in seconds
n_steps = int(total_time / time_step)  # Number of time steps

# Critical pressure ratio for choked flow
critical_pressure_ratio = (2 / (gamma + 1)) ** (gamma / (gamma - 1))

# Initialize arrays to store results
time = np.arange(0, total_time, time_step)
P_downstream_arr = np.zeros_like(time)
T_arr = np.zeros_like(time)
mass_flow_rate_arr = np.zeros_like(time)  # To store mass flow rate

P_downstream_arr[0] = P_downstream
T_arr[0] = T0

# Initialize mass in the container
mass_in_container = (P_downstream * V) / (R * T0)



# Start the simulation
for i in range(1, len(time)):
    # Calculate the current downstream pressure
    P_downstream = P_downstream_arr[i - 1]

    # Calculate the pressure ratio
    pressure_ratio = P_downstream / P_upstream

    # Check for choked flow
    if pressure_ratio > critical_pressure_ratio:
        # Choked flow
        mass_flow_rate = Cd * A * np.sqrt((gamma * P_upstream) / (R * T_upstream)) * (2 / (gamma + 1)) ** ((gamma + 1) / (2 * (gamma - 1)))
    else:
        # Non-choked flow
        mass_flow_rate = Cd * A * P_upstream * np.sqrt(2 * gamma / (R * (gamma - 1)) * ((pressure_ratio) ** (2 / gamma) - (pressure_ratio) ** ((gamma + 1) / gamma)))

    # Apply regulator behavior
    if P_downstream < P_set:
        # Proportional opening when downstream pressure is below set pressure
        opening_factor = (P_set - P_downstream) / P_set  # Proportional opening factor
        mass_flow_rate *= opening_factor  # Adjust the mass flow rate based on opening
    else:
        # Regulator is closed if downstream pressure exceeds or equals the set pressure
        mass_flow_rate = 0

    mass_flow_rate_arr[i] = mass_flow_rate  # Store mass flow rate at this time step

    # Update the mass in the receiving container
    mass_in_container += mass_flow_rate * time_step

    # Calculate the specific enthalpy of the incoming gas
    h_incoming = C_p * T_upstream

    # Heat loss due to temperature difference with surroundings
    Q_dot = h * A_wall * (T_arr[i - 1] - T_ambient)

    # Energy balance: updating internal energy (considering heat loss)
    delta_internal_energy = mass_flow_rate * h_incoming * time_step - Q_dot * time_step
    internal_energy = mass_in_container * C_p * T_arr[i - 1] + delta_internal_energy

    # Update the temperature based on the new internal energy
    T_arr[i] = internal_energy / (mass_in_container * C_p)

    # Update the pressure in the container using the ideal gas law
    P_downstream_arr[i] = (mass_in_container * R * T_arr[i]) / V

    # Prevent temperature from falling below ambient
    if T_arr[i] < T_ambient:
        T_arr[i] = T_ambient

# Plot results
plt.figure(figsize=(10, 8))

# Pressure vs. Time
plt.subplot(3, 1, 1)
plt.plot(time, P_downstream_arr / 1000)  # Convert Pa to kPa for better visualization
plt.title("Pressure, Temperature, and Mass Flow Rate vs Time (With Regulator)")
plt.ylabel("Pressure (kPa)")
plt.grid(True)

# Temperature vs. Time
plt.subplot(3, 1, 2)
plt.plot(time, T_arr)
plt.ylabel("Temperature (K)")
plt.grid(True)

# Mass Flow Rate vs. Time
plt.subplot(3, 1, 3)
plt.plot(time, mass_flow_rate_arr)
plt.xlabel("Time (s)")
plt.ylabel("Mass Flow Rate (kg/s)")
plt.grid(True)

plt.tight_layout()
plt.show()
