from rocketcea.cea_obj import CEA_Obj
import numpy as np
import matplotlib.pyplot as plt

# -----------------------------------------------------------
# USER INPUTS
# -----------------------------------------------------------

fuel = "C2H5OH"           # example
oxidizer = "N2O"        # example
Pc_vals = np.linspace(200, 700, 50)  # chamber pressure sweep (psi)
OF_vals = np.linspace(2.0, 6.0, 50) # mixture ratio sweep

cea = CEA_Obj(oxName=oxidizer, fuelName=fuel)

# -----------------------------------------------------------
# STORAGE ARRAYS
# -----------------------------------------------------------

results = {
    "Cstar": [],
    "Isp_vac": [],
    "Isp_sl": [],
    "gamma": [],
    "mw": [],
    "OF": []
}

# -----------------------------------------------------------
# MAIN SWEEP
# -----------------------------------------------------------

for OF in OF_vals:
    # Use midpoint chamber pressure for mixture optimization
    Pc_mid = np.mean(Pc_vals)

    Cstar = cea.get_Cstar(Pc=Pc_mid, MR=OF)
    Isp_vac = cea.get_Isp(Pc=Pc_mid, MR=OF, eps=40, ambPc=0.0)
    Isp_sl = cea.get_Isp(Pc=Pc_mid, MR=OF, eps=40, ambPc=14.7)

    gam = cea.get_gamma(Pc=Pc_mid, MR=OF)
    mw  = cea.get_MolWt(Pc=Pc_mid, MR=OF)

    results["OF"].append(OF)
    results["Cstar"].append(Cstar)
    results["Isp_vac"].append(Isp_vac)
    results["Isp_sl"].append(Isp_sl)
    results["gamma"].append(gam)
    results["mw"].append(mw)

# Convert to np arrays
for k in results:
    results[k] = np.array(results[k])

# -----------------------------------------------------------
# FIND OPTIMUMS
# -----------------------------------------------------------

OF_opt_Cstar = results["OF"][np.argmax(results["Cstar"])]
OF_opt_Isp_vac = results["OF"][np.argmax(results["Isp_vac"])]
OF_opt_Isp_sl = results["OF"][np.argmax(results["Isp_sl"])]

print("------------------------------------------------")
print(f"Optimal O/F (max C*)       = {OF_opt_Cstar:.3f}")
print(f"Optimal O/F (max Isp_vac)  = {OF_opt_Isp_vac:.3f}")
print(f"Optimal O/F (max Isp_sl)   = {OF_opt_Isp_sl:.3f}")
print("------------------------------------------------")

# -----------------------------------------------------------
# PLOT RESULTS
# -----------------------------------------------------------

plt.figure(figsize=(10,6))
plt.plot(results["OF"], results["Cstar"])
plt.xlabel("O/F Ratio")
plt.ylabel("C* (ft/s)")
plt.title("Characteristic Velocity vs O/F")
plt.grid(True)
plt.show()

plt.figure(figsize=(10,6))
plt.plot(results["OF"], results["Isp_vac"], label="Vacuum")
plt.plot(results["OF"], results["Isp_sl"], label="Sea Level")
plt.xlabel("O/F Ratio")
plt.ylabel("Isp (s)")
plt.title("Isp vs O/F")
plt.legend()
plt.grid(True)
plt.show()

plt.figure(figsize=(10,6))
plt.plot(results["OF"], results["gamma"])
plt.xlabel("O/F Ratio")
plt.ylabel("Gamma")
plt.title("Gamma (Specific Heat Ratio) vs O/F")
plt.grid(True)
plt.show()

plt.figure(figsize=(10,6))
plt.plot(results["OF"], results["mw"])
plt.xlabel("O/F Ratio")
plt.ylabel("Exhaust Molecular Weight")
plt.title("Molecular Weight vs O/F")
plt.grid(True)
plt.show()
