import numpy as np
import matplotlib.pyplot as plt
from rocketcea.cea_obj import CEA_Obj

# ------------------------------
# User parameters
# ------------------------------
Pc_vals = np.linspace(200, 700, 50)     # Chamber pressures (psi)
OF_vals = np.linspace(2.0, 6.0, 10)     # Mixture ratios

# Example propellants — change as needed
ox = "N2O"
fuel = "C2H5OH"
cea = CEA_Obj(oxName=ox, fuelName=fuel)

# Storage matrices
cstar_map = np.zeros((len(Pc_vals), len(OF_vals)))

# ------------------------------
# Sweep Pc and OF
# ------------------------------
for i, Pc in enumerate(Pc_vals):
    for j, OF in enumerate(OF_vals):
        try:
            cstar_map[i, j] = cea.get_Cstar(Pc=Pc, MR=OF)
        except:
            cstar_map[i, j] = np.nan

# ------------------------------
# Line plots: C* vs Pc at various OF
# ------------------------------
plt.figure()
OF_plot_vals = [2,2.5,3,3.5,4,4.5,5,5.5,6]

for OF in OF_plot_vals:
    idx = np.argmin(np.abs(OF_vals - OF))
    plt.plot(Pc_vals, cstar_map[:, idx], label=f"OF={OF}")

plt.xlabel("Chamber Pressure (psi)")
plt.ylabel("C* (ft/s)")
plt.title("C* vs Chamber Pressure for Selected OF Ratios")
plt.legend()
plt.grid(True)
plt.show()

# ------------------------------
# 2D contour plot of C*
# ------------------------------
Pc_grid, OF_grid = np.meshgrid(OF_vals, Pc_vals)

plt.figure()
cp = plt.contourf(Pc_grid, OF_grid, cstar_map, levels=40)
plt.colorbar(cp)
plt.xlabel("Mixture Ratio (O/F)")
plt.ylabel("Chamber Pressure (psi)")
plt.title("C* Contour Map")
plt.show()
