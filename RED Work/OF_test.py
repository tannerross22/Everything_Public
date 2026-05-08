from rocketcea.cea_obj import CEA_Obj
import numpy as np

# Inputs
Pc = 200 # Chamber Pressure (psi)
P_amb = 14.7  # ambient pressure (psi)
O_F = 2.1

# Genesis nozzle parameters
Ae_At = 3.07  # Exit-Throat Area Ratio (unitless)
fac_CR = 7.35  # Chamber-Throat Ratio (for finite area combustor)
A_e = np.pi*(((2.499/(39.3701*2)))**2)  # exit area (2.499in diameter to m^2)
A_t = A_e/Ae_At  # Throat area (m^2)

fr = 1  # frozen in chamber (If you change this be sure to check cf (line 51)
fr_tr = 0  # frozen at throat

C = CEA_Obj(oxName='N2O', fuelName='Ethanol', fac_CR=fac_CR)

T_f = C.get_Tcomb(Pc=Pc, MR=O_F)*(5/9)                                                          # Flame temperature converted from R to K
Rho = C.get_Densities(Pc=Pc, MR=O_F, eps=Ae_At, frozen=fr, frozenAtThroat=fr_tr)[-1]*16.018     # density converted from lb/cft to kg/m^3
M = C.get_MachNumber(Pc=Pc, MR=O_F, eps=Ae_At, frozen=fr, frozenAtThroat=fr_tr)                 # exit mach number
T_t = C.get_Temperatures(Pc=Pc, MR=O_F, eps=Ae_At, frozen=fr, frozenAtThroat=fr_tr)[-2]*(5/9)   # Throat temps converted from R to K
a = C.get_SonicVelocities(Pc=Pc, MR=O_F, eps=Ae_At, frozen=fr, frozenAtThroat=fr_tr)[-1]*0.3048 # exit sound speed converted from ft/s to m/s
ISP = C.get_Isp(Pc=Pc, MR=O_F, eps=Ae_At, frozen=fr, frozenAtThroat=fr_tr)                      # specific impulse
Pc_Pe = C.get_PcOvPe(Pc=Pc, MR=O_F, eps=Ae_At, frozen=fr, frozenAtThroat=fr_tr)

# Change this to get_PambCf if frozen assumption is not being used
cf = C.getFrozen_PambCf(Pamb=P_amb, Pc=Pc, MR=O_F, eps=Ae_At, frozenAtThroat=fr_tr)

V_e = M*a  # exit velocity (m/s)
m_dot = Rho*V_e*A_e  # mass flow
# Thrust = Rho*A_e*(V_e**2)/4.44822  # alternative way of finding thrust (gives same results)
Thrust = cf[0]*Pc*(39.3701**2)*A_t  # calculate thrust using thrust coefficient (lbs)
Thrust2 = m_dot*V_e/4.44822

print(f'Thrust with cf: {Thrust}')
print(f'Thrust with m_dot: {Thrust2}')
# print(f'\n{(1/Pc_Pe)*Pc}')

print(f'Fuel m_dot: {m_dot/(1+O_F)}')
print(f'Ox m_dot: {abs(m_dot-(m_dot/(1+O_F)))}')