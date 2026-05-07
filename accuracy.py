import numpy as np
import matplotlib.pyplot as plt
# keep it in PSI until SCFH, then convert
#behind the tank
regulator = 750 #psi
tank_pressure = 14.7 #psi
total_volume = 3 # gallons
ullage = .2*total_volume # gallons
Cv = 3 # Cv
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

def flow(Cv,regulator,SG,Temp):

tanks_list_psi = []
tanks_list_Pa = []
chamber_pressure= []
while time < 100:
