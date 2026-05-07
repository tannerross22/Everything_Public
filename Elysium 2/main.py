import math

''' 
    Takes in pintle orifice diameter and annular orifice thickness
    and returns the area of impingement. Important for lmr
'''
def area_and_bf(N, orifice_diam, outer_radius, inner_radius, pintle_radius):
    orifice_area = N * .25 * math.pi * (orifice_diam ** 2)
    orifice_ring_area = 2 * math.pi * inner_radius * orifice_diam
    film_area = math.pi * ((outer_radius)**2 - (pintle_radius)**2)
    blockage_factor = (N*orifice_diam) / (2*pintle_radius*math.pi)

    area_availability_check = orifice_ring_area  - (N * (orifice_diam**2))

    return orifice_area, film_area, blockage_factor, area_availability_check

'''
    Finds velocity of flow based on the pressure difference
'''
def velocities(orifice_area, film_area):
    radial_mass_flow  =  Cd * orifice_area * math.sqrt(2*abs(P_Pintle - Pc) * rho_eth * 32.174)
    axial_mass_flow  = Cd * film_area * math.sqrt(2*abs(P_Manifold - Pc) * rho_ox * 32.174)
    radial_velocity = radial_mass_flow / (rho_eth * orifice_area)
    axial_velocity = axial_mass_flow / (rho_ox * film_area)

    total_mass_flow = radial_mass_flow + axial_mass_flow

    return radial_mass_flow, axial_mass_flow, radial_velocity, axial_velocity, total_mass_flow
'''
    Local Momentum Ratio (LMR): used for angle calculations
    mr: mass flow radial, vr: velocoty radial, etc.
'''
def lmr(mr, ma, vr, va):
    tmr = (mr * vr) / (ma * va)
    lmr = (rho_eth * (orifice_area / N) * (vr)**2) / (rho_ox * (orifice_diam * (outer_radius - pintle_radius)) * (va**2))
    return tmr, lmr


'''
    Angle Calculation Model
'''

def spray_angle():
    if 0 <= lmr < 3:
        Q = 0.61
    elif 3 <= lmr < 4.5:
        Q = 0.7
    else:
        Q = 0.75
    theta_lmr = Q * math.degrees(math.atan(2 * lmr))
    return theta_lmr

rho_ox = 47.62 #lbm/ft^3
rho_eth = 30.28 #lbm/ft^3
N, orifice_diam,inner_radius, pintle_radius, outer_radius = 26, 0.003333, 0.01233333, 0.023, 0.024167 #Feet
P_Pintle, P_Manifold, Pc = 112320, 112320, 67392 #lbf/ft^2
Cd = .63


orifice_area,film_area,blockage_factor,area_check = area_and_bf(N,orifice_diam,outer_radius,inner_radius,pintle_radius)
mr,ma,vr,va,total_mass_flow= velocities(orifice_area,film_area)
tmr, lmr= lmr(mr,ma,vr,va)
angle_lmr = spray_angle()

if area_check > 0: 
    print(f"Spray angle from the vertical: \nLMR model: {angle_lmr}\n\nBlockage factor: {blockage_factor}\n\nMass flow total: {total_mass_flow}\n\nLeeway of tot. orifice area to gap area: {area_check}")
else:
    print(f"Ammount area of pintles orifices over gap area: {area_check}")


'''
Efficiency code that runs through multiple configurations
'''
import numpy as np
import pandas as pd
import math

# Constants
rho_ox = 37.46  # lbm/ft^3
rho_eth = 49.256  # lbm/ft^3
P_Pintle, P_Manifold, Pc = 112320, 112320, 67392  # lbf/ft^2
Cd = 0.63
pintle_radius = 0.023  # Fixed value
inner_radius = 0.01233333  # Fixed value

def area_and_bf(N, orifice_diam, outer_radius):
    orifice_area = N * 0.25 * math.pi * (orifice_diam ** 2)
    orifice_ring_area = 2 * math.pi * inner_radius * orifice_diam
    film_area = math.pi * ((outer_radius) ** 2 - (pintle_radius) ** 2)
    blockage_factor = (N * orifice_diam) / (2 * pintle_radius * math.pi)
    area_availability_check = orifice_ring_area - (N * (orifice_diam ** 2))
    return orifice_area, film_area, blockage_factor, area_availability_check

def velocities(orifice_area, film_area):
    radial_mass_flow = Cd * orifice_area * math.sqrt(2 * abs(P_Pintle - Pc) * rho_eth * 32.174)
    axial_mass_flow = Cd * film_area * math.sqrt(2 * abs(P_Manifold - Pc) * rho_ox * 32.174)
    radial_velocity = radial_mass_flow / (rho_eth * orifice_area)
    axial_velocity = axial_mass_flow / (rho_ox * film_area)
    total_mass_flow = radial_mass_flow + axial_mass_flow
    return radial_mass_flow, axial_mass_flow, radial_velocity, axial_velocity, total_mass_flow

def lmr(mr, ma, vr, va, orifice_area, N, orifice_diam, outer_radius):
    tmr = (mr * vr) / (ma * va)
    lmr_value = (rho_eth * (orifice_area / N) * (vr) ** 2) / (rho_ox * (orifice_diam * (outer_radius - pintle_radius)) * (va ** 2))
    return tmr, lmr_value

def spray_angle(lmr):
    if 0 <= lmr < 3:
        Q = 0.61
    elif 3 <= lmr < 4.5:
        Q = 0.7
    else:
        Q = 0.75
    return Q * math.degrees(math.atan(2 * lmr))

# Optimization Loop
results = []
for N in range(10, 51):  # Vary N from 10 to 50
    for orifice_diam in np.linspace(0.002, 0.005, 10):  # Vary orifice diameter
        for outer_radius in np.linspace(0.0235, 0.025, 10):  # Vary outer radius
            orifice_area, film_area, blockage_factor, area_check = area_and_bf(N, orifice_diam, outer_radius)
            if not (0.3 < blockage_factor < 0.7 and area_check > 0):
                continue
            mr, ma, vr, va, total_mass_flow = velocities(orifice_area, film_area)
            if abs(total_mass_flow - 2) > 0.01:
                continue
            tmr, lmr_value = lmr(mr, ma, vr, va, orifice_area, N, orifice_diam, outer_radius)
            angle = spray_angle(lmr_value)
            results.append([N, orifice_diam, outer_radius, blockage_factor, lmr_value, angle])

# Display Results
df = pd.DataFrame(results, columns=["N", "Orifice_diam", "Outer_radius", "Blockage Factor", "LMR", "Spray Angle"])
print(df)