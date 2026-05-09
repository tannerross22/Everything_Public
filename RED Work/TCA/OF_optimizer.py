from rocketcea.cea_obj import CEA_Obj
import numpy as np
import matplotlib.pyplot as plt

# Graphs for visualization
graphs = True

# before running this code you may need to install the rocketcea module
# type "pip install rocketcea" into the python terminal
# go here for more info on installation: https://rocketcea.readthedocs.io/en/latest/quickstart.html

# TBD
Pc = 280  # Chamber Pressure (psi)
Manifold_P = 500  # psi
P_amb = 14.7  # ambient pressure (psi)

# Genesis nozzle parameters
Ae_At = 3.07  # Exit-Throat Area Ratio (unitless)
fac_CR = 7.35  # Chamber-Throat Ratio (for finite area combustor)
A_e = np.pi*(((2.499/(39.3701*2)))**2)  # exit area (2.499in diameter to m^2)
A_t = A_e/Ae_At  # Throat area (m^2)

C = CEA_Obj(oxName='N2O', fuelName='JetA', fac_CR=fac_CR)

O_F_range = np.linspace(2, 9, 100)  # guess relevant O:Fs based on selected fuel/oxidizer

# this value indicates whether the combustion is evaluated as frozen or moving equilibrium
# frozen combustion assumes that combustion products do not react further throughout the nozzle
# from what I understand, these additional reactions do not have time to happen before they are ejected in small nozzles
# our nozzle is pretty small, so this will be enabled.
# more information here: https://rocketcea.readthedocs.io/en/latest/engine_mr.html

fr = 1  # frozen in chamber (If you change this be sure to check cf (line 51)
fr_tr = 0  # frozen at throat

Thrusts = []
Flame_temps = []
Throat_temps = []
ISPs = []
Rhos = []
V_Es = []
for O_F in O_F_range:
    T_f = C.get_Tcomb(Pc=Pc, MR=O_F)*(5/9)                                                          # Flame temperature converted from R to K
    Rho = C.get_Densities(Pc=Pc, MR=O_F, eps=Ae_At, frozen=fr, frozenAtThroat=fr_tr)[-1]*16.018     # density converted from lb/cft to kg/m^3
    M = C.get_MachNumber(Pc=Pc, MR=O_F, eps=Ae_At, frozen=fr, frozenAtThroat=fr_tr)                 # exit mach number
    T_t = C.get_Temperatures(Pc=Pc, MR=O_F, eps=Ae_At, frozen=fr, frozenAtThroat=fr_tr)[-2]*(5/9)   # Throat temps converted from R to K
    a = C.get_SonicVelocities(Pc=Pc, MR=O_F, eps=Ae_At, frozen=fr, frozenAtThroat=fr_tr)[-1]*0.3048 # exit sound speed converted from ft/s to m/s
    ISP = C.get_Isp(Pc=Pc, MR=O_F, eps=Ae_At, frozen=fr, frozenAtThroat=fr_tr)                      # specific impulse

    # Change this to get_PambCf if frozen assumption is not being used
    cf = C.getFrozen_PambCf(Pamb=P_amb, Pc=Pc, MR=O_F, eps=Ae_At, frozenAtThroat=fr_tr)

    V_e = M*a  # exit velocity (m/s)
    m_dot = Rho*V_e*A_e  # mass flow
#     Thrust = Rho*A_e*(V_e**2)/4.44822  # alternative way of finding thrust (gives same results)
    Thrust = cf[0]*Pc*(39.3701**2)*A_t  # calculate thrust using thrust coefficient (lbs)

    if O_F > O_F_range[0]:
        if Thrust > Thrusts[-1]:
            Max_Thrust = O_F, Thrust, ISP,  T_f, m_dot, cf
        if T_f > Flame_temps[-1]:
            Max_Temp = O_F, T_f
        if ISP > ISPs[-1]:
            Max_isp = O_F, Thrust, ISP, T_f, m_dot, cf

    Thrusts.append(Thrust)
    Flame_temps.append(T_f)
    Throat_temps.append(T_t)
    ISPs.append(ISP)
    Rhos.append(Rho)
    V_Es.append(V_e)


if graphs:
    plt.plot(O_F_range, ISPs, 'b', label='ISP')
    plt.vlines(Max_isp[0], min(ISPs), max(ISPs), color='k', linestyles='dashdot', label='Max ISP OF')
    plt.ylabel('Lbs')
    plt.title('ISP')
    plt.xlabel('OF Ratio')
    plt.legend()
    plt.show()

    plt.plot(O_F_range, Thrusts, 'b', label='Thrust')
    # plt.vlines(Max_Thrust[0], min(Thrusts), max(Thrusts), color='k', label='Max thrust OF')
    plt.vlines(Max_isp[0], min(Thrusts), max(Thrusts), color='k', linestyles='dashdot', label='Max ISP OF')
    plt.ylabel('Lbs')
    plt.title('Thrust')
    plt.xlabel('OF Ratio')
    plt.legend()
    plt.show()

    plt.plot(O_F_range, [i / max(Rhos) for i in Rhos], 'g', label='Density')
    plt.plot(O_F_range, [i / max(V_Es) for i in V_Es], 'b', label='Velocity')
    # plt.vlines(Max_Thrust[0], 0.5, 1, color='k', linestyles='--', label='Max thrust OF')
    plt.vlines(Max_isp[0], 0.5, 1, color='k', linestyles='dashdot', label='Max ISP OF')
    plt.title('Density vs Velocity (exit)')
    plt.xlabel('OF Ratio')
    plt.ylabel('non dimensionalized')
    plt.legend()
    plt.show()

    plt.show()
    plt.plot(O_F_range, Throat_temps, 'orange', label='Throat Temp')
    plt.plot(O_F_range, Flame_temps, 'r', label='Flame Temp')
    # plt.vlines(Max_Thrust[0], min(Flame_temps), max(Flame_temps), color='k', linestyles='--', label='Max thrust OF')
    plt.vlines(Max_isp[0], min(Flame_temps), max(Flame_temps), color='k', linestyles='dashdot', label='Max ISP OF')
    plt.title('Temperatures')
    plt.xlabel('OF Ratio')
    plt.ylabel('Kelvin')
    plt.legend()
    plt.show()

print(f'Injector pressure drop: {100*(Manifold_P-Pc)/Manifold_P}%')

# print(f'\nMax Thrust O:F')
# print(f'O:F: {Max_Thrust[0]}')
# print(f'Thrust: {Max_Thrust[1]} (lb)')
# print(f'ISP: {Max_Thrust[2]} (s)')
# print(f'Combustion Temperature: {Max_Thrust[3]} (K)')
# print(f'Mass flow: {Max_Thrust[4]} (kg/s)')
# print(f'{Max_Thrust[5][-1]} (psi)')

print(f'\nMax ISP O:F')
print(f'O:F: {Max_isp[0]}')
print(f'Thrust: {Max_isp[1]} (lb)')
print(f'ISP: {Max_isp[2]} (s)')
print(f'Combustion Temperature: {Max_isp[3]} (K)')
print(f'Mass flow: {Max_isp[4]} (kg/s)')
print(f'Fuel m_dot:{Max_isp[4]/(1+Max_isp[0])}')
print(f'Ox m_dot:{abs(Max_isp[4]-(Max_isp[4]/(1+Max_isp[0])))}')
print(f'{(Max_isp[5][-1])} (psi)')

print(f'\nMax Temperature O:F')
print(f'O:F: {Max_Temp[0]}')
print(f'Combustion Temperature: {Max_Temp[1]} (K)')
