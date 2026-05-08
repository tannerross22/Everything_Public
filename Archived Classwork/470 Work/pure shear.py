import numpy as np
import matplotlib.pyplot as plt
from collections import defaultdict
# ---------------------------------------------------------
# INPUT DATA (replace these with your actual values)
# Δ values (Å) = a – a0
v = 62.36692264
delta_values = np.array([
    # example:
    0,
    0.01,
    0.02,
    0.03,
    0.04,
    0.05  # duplicates to show averaging
])

# Total energies (eV)
E_values = np.array([
    # example:
0,
0.00462707,
0.01954485,
0.04680529,
0.08800568,
0.14561143
])
# ---------------------------------------------------------


# Compute Δ²
delta2 = delta_values**2

# ---------------------------------------------------------
# Handle duplicates: average energies for identical Δ²
# ---------------------------------------------------------
groups = defaultdict(list)
for d2, E in zip(delta2, E_values):
    groups[np.round(d2, 10)].append(E)

clean_delta2 = []
clean_energy = []
for d2, Es in groups.items():
    clean_delta2.append(d2)
    clean_energy.append(np.mean(Es))

clean_delta2 = np.array(clean_delta2)
clean_energy = np.array(clean_energy)

# Sort for plotting
idx = np.argsort(clean_delta2)
clean_delta2 = clean_delta2[idx]
clean_energy = clean_energy[idx]

# ---------------------------------------------------------
# Fit a line:  E = A * Δ² + B
# ---------------------------------------------------------
A, B = np.polyfit(clean_delta2, clean_energy/v, 1)

print(f"Slope A (related to bulk modulus): {A:.6f}")
print(f"Intercept B: {B:.6f}")

# ---------------------------------------------------------
# Plot
# ---------------------------------------------------------
plt.figure(figsize=(7,5))
plt.scatter(clean_delta2, clean_energy/v, label="Data", s=60)
plt.plot(clean_delta2, A * clean_delta2 + B, label="Fit", linewidth=2)

plt.xlabel(r'Δ²')
plt.ylabel('ΔEnergy/Vo (eV/Å^3)')
plt.title('Energy vs Strain Squared (Δ²) Fit')
plt.grid(True)
plt.legend()
plt.tight_layout()
plt.show()
