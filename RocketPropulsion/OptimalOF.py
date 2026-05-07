import numpy as np
from rocketcea.cea_obj import CEA_Obj

# --------------------------------
# Define Propellants
# --------------------------------
ox = "N2O"
fuel = "C2H5OH"
C = CEA_Obj(oxName=ox, fuelName=fuel)

# --------------------------------
# Function to show performance
# --------------------------------
def show_perf(Pc=100.0, eps=40.0, MR=1.0):
    """
    RocketCEA example-style printing.
    Outputs T in Kelvin, MW in mol/kg, Cp in kJ/kg·K (for optimum only).
    """
    IspVac, Cstar, Tc_R, MW_gpm, gamma = C.get_IvacCstrTc_ChmMwGam(Pc=Pc, MR=MR, eps=eps)

    # Convert to requested units
    Tc_K = Tc_R * (5.0 / 9.0)               # Kelvin
    mol_per_kg = 1000.0 / MW_gpm            # mol/kg

    print('%10.1f %10.1f %10.3f %12.2f %12.2f %12.1f %12.5f %10.4f' %
          (Pc, eps, MR, IspVac, Cstar, Tc_K, mol_per_kg, gamma))

# --------------------------------
# Input
# --------------------------------
Pc = float(input("Enter chamber pressure (psi): "))
eps = 40.0   # Change if needed

# Sweep mixture ratios
OF_vals = np.linspace(1.0, 6.0, 200)

cstar_vals = []

for MR in OF_vals:
    try:
        IspVac, Cstar, Tc_R, MW_gpm, gam = C.get_IvacCstrTc_ChmMwGam(Pc=Pc, MR=MR, eps=eps)
    except:
        IspVac, Cstar, Tc_R, MW_gpm, gam = [np.nan]*5

    cstar_vals.append(Cstar)

cstar_vals = np.array(cstar_vals)

# --------------------------------
# Find optimum MR for maximum C*
# --------------------------------
max_idx = np.nanargmax(cstar_vals)
best_OF = OF_vals[max_idx]

Isp_best, Cstar_best, Tc_best_R, MW_best_gpm, gamma_best = \
    C.get_IvacCstrTc_ChmMwGam(Pc=Pc, MR=best_OF, eps=eps)

# Convert optimum values
Tc_best_K = Tc_best_R * (5.0 / 9.0)                     # K
mol_per_kg_best = 1000.0 / MW_best_gpm                  # mol/kg
Cp_best = C.get_Chamber_Cp(Pc=Pc, MR=best_OF)                   # BTU/lbm-R
Cp_best_kJkgK = Cp_best * 4.1868                        # kJ/kg·K
rho_best = C.get_Chamber_Density(Pc=Pc, MR=best_OF)             # slug/ft³ (unchanged)

# --------------------------------
# Print Table + Optimum Result
# --------------------------------

print("\n      Pc       eps        MR     IspVac(sec)    Cstar(ft/s)     T(K)      mol/kg      gamma")
for MR in np.linspace(1.0, 6.0, 12):
    show_perf(Pc=Pc, eps=eps, MR=MR)

print("\n==================== OPTIMUM C* ====================")
print(f"Best O/F Ratio:          {best_OF:.3f}")
print(f"Max C*:                  {Cstar_best:.2f} ft/s")
print(f"Vac Isp at Optimum:      {Isp_best:.2f} s")
print(f"Temperature (K):         {Tc_best_K:.1f} K")
print(f"Gamma:                   {gamma_best:.4f}")
print(f"Molecular Weight:        {mol_per_kg_best:.5f} mol/kg")
print(f"Specific Heat Cp:        {Cp_best_kJkgK:.4f} kJ/kg·K")
print(f"Density (rho):           {rho_best:.6f} slug/ft^3")
print("====================================================\n")
