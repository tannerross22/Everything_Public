import numpy as np
import matplotlib.pyplot as plt

# Physical constants
hbar = 1.055e-34      # J·s
amu = 1.6605e-27      # kg
eV = 1.602e-19        # J

# Masses
masses_amu = [12, 1200, 12000]
masses = [m * amu for m in masses_amu]

# Box half-lengths (meters)
L_vals = np.array([1e-3, 1e-6, 1e-7, 1e-8, 1e-9])

# Energy levels to plot
levels = [1, 2]

plt.figure()

for m_amu, m in zip(masses_amu, masses):
    for n in levels:
        E = ((n-1/2)**2 * np.pi**2 * hbar**2) / (2 * m * L_vals**2)
        E /= eV  # convert to eV
        plt.loglog(L_vals, E, marker='o',
                   label=f"m = {m_amu} amu, n = {n}")
        print(E)

plt.xlabel("L (m)")
plt.ylabel("Energy (eV)")
plt.title("Energy Levels in 1D Infinite Square Well (−L to L)")
plt.legend()
plt.grid(True, which="both")
plt.show()
