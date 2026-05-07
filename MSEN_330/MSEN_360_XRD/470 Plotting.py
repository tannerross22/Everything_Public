import numpy as np
import matplotlib.pyplot as plt

# ---------------------------------------------------------
# Replace these with YOUR actual data
# ---------------------------------------------------------
a_vals = np.array([ 3.95,
3.975,
4,
4.025,
4.05,
4.075,
4.1 ])   # lattice parameters (Å)
P_vals = np.array([30.1,
-17.28,
-59.8,
-97.96,
-132.08,
-162.53,
-188.91 ])            # pressures (kB)
# ---------------------------------------------------------

# Quadratic fit:  P(a) = c2*a^2 + c1*a + c0
c2, c1, c0 = np.polyfit(a_vals, P_vals, 2)

print("Quadratic coefficients:")
print(f"  c2 = {c2}")
print(f"  c1 = {c1}")
print(f"  c0 = {c0}")

# Solve quadratic equation for P(a) = 0
roots = np.roots([c2, c1, c0])
real_roots = [r.real for r in roots if np.isreal(r)]

if len(real_roots) == 0:
    print("No real root found (pressure curve does not cross zero).")
else:
    a_zero = real_roots[1]
    print(f"\nLattice parameter where pressure = 0: a0 = {a_zero:.6f} Å")

# Create smooth curve for plotting
a_fine = np.linspace(min(a_vals), max(a_vals), 500)
P_fine = c2*a_fine**2 + c1*a_fine + c0

# Plot
plt.figure(figsize=(7,5))
plt.plot(a_vals, P_vals, 'o', label='Data points')
plt.plot(a_fine, P_fine, '-', label='Quadratic fit')
plt.axhline(0, color='gray', linestyle='--')

if len(real_roots) > 0:
    plt.plot(a_zero, 0, 'r*', markersize=14, label='Zero-pressure point')

plt.xlabel("Lattice Parameter (Å)")
plt.ylabel("Pressure (kB)")
plt.title("Quadratic Fit: Pressure vs Lattice Parameter")
plt.legend()
plt.grid(True)
plt.tight_layout()
plt.show()
