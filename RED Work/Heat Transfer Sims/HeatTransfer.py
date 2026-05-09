import numpy as np
from scipy.optimize import brentq

# ═══════════════════════════════════════════════════════════════
#  INPUTS — review flags marked with  ⚠  REVIEW
# ═══════════════════════════════════════════════════════════════

# --- Combustion / CEA inputs (from your nozzle sizing) ---
To        = 3020.0      # K,     chamber stagnation temperature
Pc_psi    = 600.0       # psi,   chamber pressure
k         = 1.170       # -,     ratio of specific heats (gamma)
Cp_gas    = 2820.0      # J/kg*K, gas specific heat
M_mol     = 25.287      # g/mol, molecular weight
mdot      = 3.543       # kg/s,  total mass flow rate
r_recov   = 0.90        # -,     turbulent recovery factor (standard for turbulent BL)

# --- Transport properties (estimated — get from CEA if possible) ---
mu_gas    = 8.0e-5      # Pa*s   ⚠ REVIEW: estimated for ~3000K combustion products;
                        #         CEA throat transport output preferred.
                        #         Typical range 6e-5 to 9e-5 Pa*s at these conditions.
Pr_gas    = 0.72        # -      ⚠ REVIEW: estimated from CEA literature for N2O/EtOH
                        #         products at throat (~0.70–0.73 typical range).

# --- Nozzle geometry (from your nozzle sizing script) ---
Dt_in     = 1.318       # in,    throat diameter (from your constrained nozzle calc)
t_graph_in = 1.60       # in,    ⚠ REVIEW: graphite wall thickness at retaining ring
                        #         interface — confirmed known value
De_in     = 3.75        # in,    exit diameter (constrained)
R_curv_in = 1.5 * (Dt_in / 2)  # in, throat radius of curvature (1.5*rt standard)

# --- Graphite properties (isostatic press, conservative estimates) ---
k_graph   = 130        # W/m*K  ⚠ REVIEW: isostatic graphite radial conductivity.
                        #         Conservative low end — typical range 80–130 W/m*K
                        #         at room temp, decreasing ~30% by 1000°C.
                        #         Get spec sheet from your supplier if possible.
rho_graph = 1800.0      # kg/m^3 ⚠ REVIEW: typical isostatic graphite 1750–1850 kg/m^3
Cp_graph  = 720.0       # J/kg*K ⚠ REVIEW: ~710–750 J/kg*K at moderate temps

# --- Aluminum retaining ring properties (6061-T6 assumed) ---
k_al      = 167.0       # W/m*K  (6061-T6; use 130 if 7075)
rho_al    = 2700.0      # kg/m^3
Cp_al     = 896.0       # J/kg*K
t_al_in   = 0.5       # in     ⚠ REVIEW: radial wall thickness of aluminum ring
L_contact_in = 1.5      # in     ⚠ REVIEW: axial length of graphite-to-aluminum
                        #         contact interface

# --- Contact conductance (dry clamped graphite-aluminum) ---
h_contact = 3000.0      # W/m^2*K  ⚠ REVIEW: dry clamped metal-graphite interface.
                        #           Conservative range: 1000–5000 W/m^2*K.
                        #           Use 1000 for worst case, 5000 for well-clamped.

# --- Ambient / outer boundary ---
T_amb     = 260       # K,    ambient temperature
h_amb     = 10.0        # W/m^2*K  ⚠ REVIEW: natural convection on outer Al surface.
                        #           10–25 W/m^2*K natural conv; use 50+ if forced

# --- Burn time ---
t_burn    = 10.25       # s     (from propellant mass / mdot calculation)

# ═══════════════════════════════════════════════════════════════
#  DERIVED GEOMETRY
# ═══════════════════════════════════════════════════════════════

R_univ   = 8.314
Ro       = R_univ / (M_mol / 1000)    # J/kg*K specific gas constant
Pc_pa    = Pc_psi * 6894.757

# Unit conversions
Dt_m         = Dt_in * 0.0254
De_m         = De_in * 0.0254
t_graph_m    = t_graph_in * 0.0254
t_al_m       = t_al_in * 0.0254
L_contact_m  = L_contact_in * 0.0254
R_curv_m     = R_curv_in * 0.0254

# Throat area and derived quantities
A_star   = np.pi / 4 * Dt_m**2
c_star   = Pc_pa * A_star / mdot      # characteristic velocity

# ═══════════════════════════════════════════════════════════════
#  STEP 1: ADIABATIC WALL TEMPERATURE AT THROAT
# ═══════════════════════════════════════════════════════════════
# At throat, Me = 1 by definition
Me_throat = 1.0
T_static_throat = To / (1 + (k - 1) / 2 * Me_throat**2)   # K
Taw = T_static_throat * (1 + r_recov * (k - 1) / 2 * Me_throat**2)

# ═══════════════════════════════════════════════════════════════
#  STEP 2: BARTZ HEAT TRANSFER COEFFICIENT AT THROAT
# ═══════════════════════════════════════════════════════════════
# Bartz equation:
# h = (0.026 / Dt^0.2) * (mu^0.2 * Cp / Pr^0.6) * (Pc/c*)^0.8 * (Dt/Rc)^0.1 * (A*/A)^0.9
# At throat: A*/A = 1, Dt/Rc = Dt/R_curv
sigma = 1.0   # correction factor, ~1.0 for initial estimate
h_gas = (0.026 / Dt_m**0.2) * \
        (mu_gas**0.2 * Cp_gas / Pr_gas**0.6) * \
        (Pc_pa / c_star)**0.8 * \
        (Dt_m / R_curv_m)**0.1 * \
        sigma

# ═══════════════════════════════════════════════════════════════
#  STEP 3: THERMAL RESISTANCE NETWORK (series, 1D radial)
# ═══════════════════════════════════════════════════════════════
# Resistances per unit area (m^2*K/W) at the contact interface area
A_int = np.pi * Dt_m * L_contact_m    # m^2, interface area (cylindrical)

R_conv_gas   = 1 / (h_gas * A_int)           # hot gas convection to nozzle ID
R_graph      = t_graph_m / (k_graph * A_int) # conduction through graphite wall
R_contact    = 1 / (h_contact * A_int)       # graphite-to-aluminum contact
R_al         = t_al_m / (k_al * A_int)       # conduction through aluminum ring
R_amb        = 1 / (h_amb * A_int)           # convection from outer Al to ambient

R_total      = R_conv_gas + R_graph + R_contact + R_al + R_amb

# ═══════════════════════════════════════════════════════════════
#  STEP 4: STEADY-STATE TEMPERATURES AT EACH NODE
# ═══════════════════════════════════════════════════════════════
Q_ss = (Taw - T_amb) / R_total           # W, steady-state heat flux

T_nozzle_ID   = Taw - Q_ss * R_conv_gas              # graphite inner wall
T_graph_OD    = T_nozzle_ID - Q_ss * R_graph         # graphite outer wall / Al interface
T_al_ID       = T_graph_OD - Q_ss * R_contact        # aluminum inner face
T_al_OD       = T_al_ID - Q_ss * R_al                # aluminum outer face

# ═══════════════════════════════════════════════════════════════
#  STEP 5: TRANSIENT CHECK — thermal penetration depth
# ═══════════════════════════════════════════════════════════════
alpha_al    = k_al / (rho_al * Cp_al)       # m^2/s, thermal diffusivity Al
alpha_graph = k_graph / (rho_graph * Cp_graph)  # m^2/s, thermal diffusivity graphite

delta_al    = np.sqrt(alpha_al * t_burn)    # m, penetration depth in Al
delta_graph = np.sqrt(alpha_graph * t_burn) # m, penetration depth in graphite

# Transient temperature estimate at Al inner face using 1D semi-infinite solid
# T(x,t) = T_amb + (T_surface - T_amb) * erfc(x / (2*sqrt(alpha*t)))
from scipy.special import erfc
T_surface_al = T_al_ID   # use steady-state inner face as driving surface temp
T_al_OD_transient = T_amb + (T_surface_al - T_amb) * \
                    erfc(t_al_m / (2 * np.sqrt(alpha_al * t_burn)))

# ═══════════════════════════════════════════════════════════════
#  RESULTS
# ═══════════════════════════════════════════════════════════════
print("=" * 58)
print("  NOZZLE THERMAL ANALYSIS — RETAINING RING TEMPERATURE")
print("=" * 58)

print(f"\n--- Boundary Conditions ---")
print(f"  Adiabatic wall temp (Taw)    = {Taw:.1f} K  ({Taw-273.15:.1f} °C)")
print(f"  Bartz h_gas at throat        = {h_gas:.1f} W/m²K")
print(f"  Ambient temperature          = {T_amb:.1f} K  ({T_amb-273.15:.1f} °C)")
print(f"  Interface area               = {A_int*1e4:.2f} cm²")

print(f"\n--- Thermal Resistances (K/W) ---")
print(f"  R_conv_gas  (hot gas → nozzle ID) = {R_conv_gas:.5f}")
print(f"  R_graphite  (through wall)        = {R_graph:.5f}")
print(f"  R_contact   (graphite → Al)       = {R_contact:.5f}")
print(f"  R_aluminum  (through ring)        = {R_al:.5f}")
print(f"  R_ambient   (Al OD → air)         = {R_amb:.5f}")
print(f"  R_total                           = {R_total:.5f}")
print(f"  Dominant resistance: ", end="")
resistances = {'R_conv_gas': R_conv_gas, 'R_graphite': R_graph,
               'R_contact': R_contact, 'R_aluminum': R_al, 'R_ambient': R_amb}
print(max(resistances, key=resistances.get))

print(f"\n--- Steady-State Temperatures ---")
print(f"  Graphite inner wall (ID)     = {T_nozzle_ID:.1f} K  ({T_nozzle_ID-273.15:.1f} °C)")
print(f"  Graphite outer wall (OD)     = {T_graph_OD:.1f} K  ({T_graph_OD-273.15:.1f} °C)")
print(f"  Aluminum ring inner face     = {T_al_ID:.1f} K  ({T_al_ID-273.15:.1f} °C)")
print(f"  Aluminum ring outer face     = {T_al_OD:.1f} K  ({T_al_OD-273.15:.1f} °C)")
print(f"  Steady-state heat flow Q     = {Q_ss:.1f} W")

print(f"\n--- Transient Check (t_burn = {t_burn:.2f} s) ---")
print(f"  Thermal penetration in Al    = {delta_al*1000:.1f} mm  (ring thickness = {t_al_m*1000:.1f} mm)")
print(f"  Thermal penetration in graph = {delta_graph*1000:.1f} mm  (wall = {t_graph_m*1000:.1f} mm)")
if delta_al < t_al_m:
    print(f"  ⚠  Al ring NOT at steady state — transient estimate used for OD")
else:
    print(f"  Al ring reaches steady state within burn time ✓")
print(f"  Al ring OD temp (transient)  = {T_al_OD_transient:.1f} K  ({T_al_OD_transient-273.15:.1f} °C)")

print(f"\n--- Aluminum Strength Assessment ---")
print(f"  Al inner face temp           = {T_al_ID-273.15:.1f} °C")
if T_al_ID - 273.15 < 150:
    print(f"  ✓  Below 150°C — 6061-T6 retains full yield strength")
elif T_al_ID - 273.15 < 200:
    print(f"  ⚠  150–200°C range — 6061-T6 begins losing strength (~10–20% reduction)")
else:
    print(f"  ✗  Above 200°C — significant strength loss in 6061-T6 (>30%)")

print(f"\n--- Key Uncertainties (sensitivity drivers) ---")
print(f"  h_contact varies 1000–5000 W/m²K:")
for hc in [1000, 3000, 5000]:
    R_c = 1 / (hc * A_int)
    R_t = R_conv_gas + R_graph + R_c + R_al + R_amb
    Q_t = (Taw - T_amb) / R_t
    T_al_id = Taw - Q_t*(R_conv_gas + R_graph + R_c)
    print(f"    h_contact={hc:5d} → T_al_inner = {T_al_id-273.15:.1f} °C")
print(f"  k_graph varies 60–130 W/mK:")
for kg in [60, 80, 130]:
    R_g = t_graph_m / (kg * A_int)
    R_t = R_conv_gas + R_g + R_contact + R_al + R_amb
    Q_t = (Taw - T_amb) / R_t
    T_al_id = Taw - Q_t*(R_conv_gas + R_g + R_contact)
    print(f"    k_graph  ={kg:5d} → T_al_inner = {T_al_id-273.15:.1f} °C")
print("=" * 58)