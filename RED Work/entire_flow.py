import numpy as np
import matplotlib.pyplot as plt
# keep it in PSI until SCFH, then convert
#behind the tank
regulator = 625 #psi
tank_pressure = 14.7 #psi
total_volume = 3 # gallons
ullage = .2*total_volume # gallons
Cv = .8 # Cv
SG = 0.967
Temp = 529.67  # rankine
step = 0.01  # seconds
time = 0
# Metric Section

T = Temp*5/9  # kelvin
V = total_volume/264.2  # m^3
P1 = regulator*6895  # Pa
P2 = tank_pressure*6895  # Pa
R = 8.3145  # J/mol*K
MW = 0.028  # kg/mol
m_ullage = ullage/264.2
def sonic(regulator, tank_pressure):
    if regulator > 2*tank_pressure:
        return True
    else:
        return False

def to_Pa(list):
    tank_pa = []
    for i in list:
        tank_pa.append(i*6895)
    return tank_pa

main_valve = False
tanks = [14.7]
times = [0]
tank_pa = to_Pa(tanks)
while tank_pressure < regulator:
    #calculate flow rate, add that amount to the tank
    if sonic(regulator,tanks[-1]) == False:
        Q = 962*Cv*np.sqrt((regulator**2-tanks[-1]**2)/(SG*Temp))
        ACFH = 14.7 / (tanks[-1]) * (Temp / 519) * Q
        flow = 0.00000786579 * ACFH  # convert to metric, m^3/s
        rho = tank_pa[-1] * MW / (R * T)
        mdot = flow * rho
        n = mdot * step / (MW)
        P2 += n * R * T / m_ullage
        tank_pressure = P2/6895
        time += step
        times.append(time)
        tank_pa.append(P2)
        tanks.append(tank_pressure)

    else:
        Q = Cv*816*regulator/np.sqrt(SG*Temp)  # flow in SCFH
        ACFH = 14.7/(tanks[-1])*(Temp/519)*Q
        flow = 0.00000786579*ACFH #convert to metric, m^3/s
        rho = tank_pa[-1]*MW/(R*T)  # kg/m^3
        mdot = flow*rho
        n = mdot*step/MW
        P2 += (n*R*T/m_ullage)
        tank_pressure = P2/6895
        time += step
        times.append(time)
        tank_pa.append(P2)
        tanks.append(tank_pressure)
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


main_valve =True
start_time = times[-1]
jet_flow = 5 #kg/s
jet_density = 800 #kg/m^3
jet_q = jet_flow/jet_density #m^3/s
Vgas = m_ullage #m^3
Vliquid = V-ullage #m^3
p_tank = regulator*6895-1
v_gas = [m_ullage]

while Vgas < V:
    Vgas += jet_q * step  # update gas volume
    p_tank = p_tank*v_gas[-1]/Vgas
    tanks.append(p_tank / 6895)
    tank_pa.append(p_tank)
    if sonic(regulator,tanks[-1]) == False:
        Q = 962*Cv*np.sqrt((regulator**2-tanks[-1]**2)/(SG*Temp))
        ACFH = 14.7 / (tanks[-1]) * (Temp / 519) * Q
        flow = 0.00000786579 * ACFH  # convert to metric, m^3/s
        rho = tank_pa[-1] * MW / (R * T)
        mdot = flow * rho
        n = mdot * step / (MW)
        p_tank += n * R * T / Vgas

    else:
        Q = Cv * 816 * regulator / np.sqrt(SG * Temp)  # flow in SCFH
        ACFH = 14.7 / (tanks[-1]) * (Temp / 519) * Q
        flow = 0.00000786579 * ACFH  # convert to metric, m^3/s
        rho = tank_pa[-1] * MW / (R * T)  # kg/m^3
        mdot = flow * rho
        n = mdot * step / MW
        p_tank += (n * R * T / Vgas)

    v_gas.append(Vgas)
    time += step
    times.append(time)



burn_time = times[-1]-start_time
print(burn_time)
pressure_drop = regulator-tanks[-1]
print(pressure_drop)
plt.plot(times,tanks)
plt.show()






