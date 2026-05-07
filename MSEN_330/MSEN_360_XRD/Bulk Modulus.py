import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

# ---------------------------------------------------
# 1. Load Data
# ---------------------------------------------------
# Your CSV should have: a,Volume,Pressure(kB),Energy(eV)
df = pd.read_csv("eos_data.csv")

V = df["Volume"].values
P = df["Pressure(kB)"].values  # already in kB

# ---------------------------------------------------
# 2. Fit P(V) with a quadratic: P = aV^2 + bV + c
# ---------------------------------------------------
coeffs = np.polyfit(V, P, 2)
a, b, c = coeffs

print("Quadratic fit:  P(V) = aV^2 + bV + c")
print(f"a = {a}, b = {b}, c = {c}")

# ---------------------------------------------------
# 3. Find zero-pressure volume (solve aV^2 + bV + c = 0)
# ---------------------------------------------------
roots = np.roots(coeffs)

# pick the root nearest your minimum volume / physically correct root
V0 = roots[np.argmin(np.abs(roots - np.mean(V)))]
# alternative: print(roots) if you want to manually choose

print(f"Equilibrium volume (P=0): V0 = {V0}")

# ---------------------------------------------------
# 4. Compute derivative dP/dV = 2aV + b at V0
# ---------------------------------------------------
dPdV = 2*a*V0 + b

print(f"dP/dV at V0 = {dPdV}  (units: kB per Å^3)")

# ---------------------------------------------------
# 5. Bulk modulus: B = -V * dP/dV  (convert kB → GPa)
# ---------------------------------------------------
# conversion: 1 kB = 0.1 GPa
B_kB = -V0 * dPdV
B_GPa = B_kB * 0.1

print(f"Bulk Modulus: {B_kB} kB  =  {B_GPa} GPa")

# ---------------------------------------------------
# 6. Plot P(V) + quadratic fit
# ---------------------------------------------------
V_fit = np.linspace(min(V), max(V), 300)
P_fit = a * V_fit**2 + b * V_fit + c

plt.figure(figsize=(8,6))
plt.scatter(V, P, label="Data", s=50)
plt.plot(V_fit, P_fit, label="Quadratic Fit")
plt.axhline(0, color='gray', linestyle='--')

# mark equilibrium point
plt.scatter([V0], [0], color='red', label=f"P=0 → V0={V0:.2f}")

plt.xlabel("Volume (Å³)")
plt.ylabel("Pressure (kB)")
plt.title("Equation of State Fit: Pressure vs Volume")
plt.legend()
plt.grid(True)
plt.tight_layout()
plt.show()
