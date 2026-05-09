import numpy as np
from scipy.optimize import brentq

# ── Tunable inputs ────────────────────────────────────────────────────────────
mdot        = 3.543       # kg/s total mass flow
Pc_psi      = 600.0       # chamber pressure, psi
OF          = 4.25        # O/F ratio
To          = 3020.0      # K, chamber stagnation temp (from CEA)
k           = 1.170       # gamma (from CEA)
Cp          = 2820.0      # J/kg*K (from CEA)
M_mol       = 25.287      # g/mol, molecular weight (from CEA)
alt_opt_ft  = 9240.0      # ft, altitude for ambient pressure reference
De_max_in   = 3.75        # in, max exit diameter (hard constraint)
L_star      = 0.700       # m, characteristic length
CR          = 3.0         # contraction ratio Ac/At
# ─────────────────────────────────────────────────────────────────────────────

# Constants
R_univ   = 8.314          # J/mol*K
g0       = 9.80665        # m/s^2

# Derived gas properties
Ro       = (R_univ / (M_mol / 1000))   # J/kg*K, specific gas constant
Pc_pa    = Pc_psi * 6894.757           # Pa

# Ambient pressure at optimization altitude (US Standard Atmosphere approx)
alt_m    = alt_opt_ft * 0.3048
Pa       = 101325 * (1 - 2.25577e-5 * alt_m) ** 5.25588   # Pa

# ── Throat conditions ─────────────────────────────────────────────────────────
T_star   = To * (2 / (k + 1))                             # K, throat temp
V_star   = np.sqrt(k * Ro * T_star)                       # m/s, throat velocity (= local speed of sound)
rho_star = Pc_pa / (Ro * To) * (2 / (k + 1))**(1/(k-1)) # kg/m^3
A_star   = mdot / (rho_star * V_star)                     # m^2, throat area
D_star_in = np.sqrt(4 * A_star / np.pi) / 0.0254          # in, throat diameter

# ── Fixed exit area from diameter constraint ──────────────────────────────────
De_m     = De_max_in * 0.0254                             # m
Ae       = np.pi / 4 * De_m**2                           # m^2
epsilon  = Ae / A_star                                    # expansion ratio (result, not input)

# ── Back-calculate exit Mach from area-Mach relation ─────────────────────────
# A/A* = (1/Me) * [(2/(k+1)) * (1 + (k-1)/2 * Me^2)]^((k+1)/(2(k-1)))
def area_mach_residual(Me):
    term = (2 / (k + 1)) * (1 + (k - 1) / 2 * Me**2)
    return (1 / Me) * term**((k + 1) / (2 * (k - 1))) - epsilon

Me = brentq(area_mach_residual, 1.01, 10.0)   # supersonic root

# ── Exit conditions ───────────────────────────────────────────────────────────
Te  = To / (1 + (k - 1) / 2 * Me**2)          # K
Pe  = Pc_pa * (Te / To)**(k / (k - 1))        # Pa
Ve  = Me * np.sqrt(k * Ro * Te)               # m/s

# ── Ideal nozzle for comparison (Pe = Pa) ────────────────────────────────────
def ideal_exit(Pa_target):
    Me_ideal = np.sqrt((2 / (k - 1)) * ((Pc_pa / Pa_target)**((k - 1) / k) - 1))
    Te_ideal = To / (1 + (k - 1) / 2 * Me_ideal**2)
    Ve_ideal = Me_ideal * np.sqrt(k * Ro * Te_ideal)
    Ae_ideal = (mdot / (Pc_pa / (Ro * To) * (2/(k+1))**(1/(k-1)))) / Me_ideal * \
               ((2/(k+1)) * (1 + (k-1)/2 * Me_ideal**2))**((k+1)/(2*(k-1)))
    De_ideal_in = np.sqrt(4 * Ae_ideal / np.pi) / 0.0254
    thrust_ideal = mdot * Ve_ideal + (Pa_target - Pa) * Ae_ideal
    Isp_ideal = thrust_ideal / (mdot * g0)
    return De_ideal_in, Ve_ideal, thrust_ideal, Isp_ideal

De_ideal_in, Ve_ideal, F_ideal, Isp_ideal = ideal_exit(Pa)

# ── Thrust and Isp ────────────────────────────────────────────────────────────
F    = mdot * Ve + (Pe - Pa) * Ae     # N
Isp  = F / (mdot * g0)               # s

# ── Chamber sizing ────────────────────────────────────────────────────────────
Vc        = L_star * A_star           # m^3
Ac        = CR * A_star              # m^2
Dc_in     = np.sqrt(4 * Ac / np.pi) / 0.0254   # in
Lc_in     = (Vc / Ac) / 0.0254                 # in

# ── Parabolic nozzle length (80% bell, Rao approximation) ────────────────────
theta_i   = np.radians(32.5)
theta_e   = np.radians(13.0)
rt_in     = D_star_in / 2
Ln_in     = (np.sqrt(epsilon) - 1) * rt_in / np.tan(np.radians(15)) * 0.8   # 80% of 15-deg cone

mdot_n2o  = mdot * OF / (1 + OF)
mdot_etoh = mdot / (1 + OF)

# ── Print results ─────────────────────────────────────────────────────────────
print("=" * 55)
print("  NOZZLE SIZING — DIAMETER-CONSTRAINED (3.75\" exit)")
print("=" * 55)
print(f"\n--- Inputs ---")
print(f"  mdot total         = {mdot:.4f} kg/s  ({mdot*2.20462:.4f} lbm/s)")
print(f"  mdot N2O           = {mdot_n2o:.4f} kg/s")
print(f"  mdot EtOH          = {mdot_etoh:.4f} kg/s")
print(f"  Pc                 = {Pc_psi:.1f} psi  ({Pc_pa/1e6:.4f} MPa)")
print(f"  To                 = {To:.1f} K")
print(f"  k (gamma)          = {k:.4f}")
print(f"  Ro                 = {Ro:.3f} J/kg*K")
print(f"  Pa @ {alt_opt_ft:.0f} ft        = {Pa:.1f} Pa  ({Pa/6894.757:.3f} psi)")

print(f"\n--- Throat ---")
print(f"  A*                 = {A_star*1e4:.4f} cm²  ({A_star*1550.003:.4f} in²)")
print(f"  D*                 = {D_star_in:.4f} in  ({D_star_in*25.4:.4f} mm)")
print(f"  T*                 = {T_star:.2f} K")
print(f"  V*                 = {V_star:.2f} m/s")

print(f"\n--- Exit (constrained to {De_max_in}\" diameter) ---")
print(f"  Ae                 = {Ae*1e4:.4f} cm²  ({Ae*1550.003:.4f} in²)")
print(f"  ε (expansion ratio)= {epsilon:.4f}  (was optimized at {De_ideal_in:.3f}\" → ε_ideal computed below)")
print(f"  Me                 = {Me:.4f}")
print(f"  Pe                 = {Pe:.1f} Pa  ({Pe/6894.757:.3f} psi)")
print(f"  Pa                 = {Pa:.1f} Pa  ({Pa/6894.757:.3f} psi)")
print(f"  Pe/Pa              = {Pe/Pa:.3f}  ({'underexpanded' if Pe > Pa else 'overexpanded'})")
print(f"  Te                 = {Te:.2f} K")
print(f"  Ve                 = {Ve:.2f} m/s")

print(f"\n--- Thrust & Performance ---")
print(f"  Momentum thrust    = {mdot*Ve:.2f} N  ({mdot*Ve/4.44822:.2f} lbf)")
print(f"  Pressure thrust    = {(Pe-Pa)*Ae:.2f} N  ({(Pe-Pa)*Ae/4.44822:.2f} lbf)")
print(f"  Total Thrust       = {F:.2f} N  ({F/4.44822:.2f} lbf)")
print(f"  Isp                = {Isp:.2f} s")

print(f"\n--- Ideal nozzle comparison (Pe = Pa @ {alt_opt_ft:.0f} ft) ---")
print(f"  Ideal exit diam    = {De_ideal_in:.4f} in  (exceeds {De_max_in}\" constraint)")
print(f"  Ideal Ve           = {Ve_ideal:.2f} m/s")
print(f"  Ideal Thrust       = {F_ideal:.2f} N  ({F_ideal/4.44822:.2f} lbf)")
print(f"  Ideal Isp          = {Isp_ideal:.2f} s")
print(f"  Thrust penalty     = {(F_ideal - F)/F_ideal * 100:.2f}%")
print(f"  Isp penalty        = {(Isp_ideal - Isp)/Isp_ideal * 100:.2f}%")

print(f"\n--- Chamber Sizing ---")
print(f"  Vc                 = {Vc*61023.7:.2f} in³")
print(f"  Dc                 = {Dc_in:.4f} in")
print(f"  Lc                 = {Lc_in:.4f} in")
print(f"  Nozzle length (80%)= {Ln_in:.4f} in")
print("=" * 55)