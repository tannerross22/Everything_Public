import numpy as np
import matplotlib.pyplot as plt

# --- Data from your 8-atom supercell calculations ---
x = np.array([1,
0.875,
0.75,
0.625,
0.5,
0.375,
0.25,
0.125,
0])
E_alloy = np.array([-7.488058291,
-7.097121065,
-6.692925144,
-6.317513616,
-5.924508205,
-5.564092,
-5.181039247,
-4.821875718,
-4.444197581])

# Reference energies for pure Pt and pure Au
E_Pt = E_alloy[0]
E_Au = E_alloy[-1]

# --- Compute ideal mixture energies ---
E_ideal = x*E_Pt+ (1-x)*E_Au

# --- Compute mixing energy deviation ---
DeltaH_mix = E_alloy - E_ideal

# --- Print results ---
print(f"{'x(Pt)':>8} {'E_alloy(eV)':>15} {'E_ideal(eV)':>15} {'DeltaH_mix(eV)':>15}")
for xi, Ea, Ei, dH in zip(x, E_alloy, E_ideal, DeltaH_mix):
    print(f"{xi:8.3f} {Ea:15.6f} {Ei:15.6f} {dH:15.6f}")

# --- Optional: plot mixing energy ---
plt.figure(figsize=(6,4))
plt.plot(x, DeltaH_mix, 'o-', color='blue')
plt.xlabel('Pt fraction (x)')
plt.ylabel('ΔH_mix (eV)')
plt.title('Mixing Energy Deviation for 8 atom Pt-Au alloy')
plt.grid(True)
plt.show()
