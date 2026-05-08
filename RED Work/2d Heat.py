"""
2D Finite Element TRANSIENT Heat Conduction Solver
- Linear triangular elements (3-node)
- Backward Euler time integration (unconditionally stable)
- Lumped mass matrix (diagonal)
- Multi-material with temperature-dependent k (Picard iteration per step)
- Dirichlet boundary conditions (specified temperature)

Governing PDE:  rho*Cp * dT/dt = div(k * grad(T)) + Q

Backward Euler:  (M/dt + K) * T^{n+1} = M/dt * T^n + f
"""

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.tri import Triangulation
from scipy.sparse import lil_matrix, diags
from scipy.sparse.linalg import spsolve

# ============================================================
# TUNABLE PARAMETERS    
# ============================================================

# --- Domain geometry (rectangular, split into two material regions) ---
Lx = 0.0435          # domain width  [m]
Ly = 0.0381          # domain height [m]
nx = 60           # elements in x
ny = 30           # elements in y

# --- Material properties ---
x_interface = 0.7 * Lx       # interface location [m]

# Material 1 (left): temperature-dependent k
k1_table_T = [22.6,
101,
199.3,
301.6,
401.6,
501.6,
601.6,
701.7,
801.3,
900.8,
1000.9]   # [°C]
k1_table_k = [133.02,
128.54,
117.62,
106.03,
96.7,
88.61,
82.22,
76.52,
71.78,
67.88,
64.26]   # [W/m·K]
rho1 = 1800      # density [kg/m^3]
cp1  = 1000       # specific heat [J/kg·K]

# Material 2 (right): constant k
k2   = 167       # thermal conductivity [W/m·K]
rho2 = 2700.0      # density [kg/m^3]
cp2  = 900.0       # specific heat [J/kg·K]

# --- Internal heat generation [W/m^3] ---
Q1 = 0.0
Q2 = 0.0

# --- Time stepping ---
t_end    = 20     # total simulation time [s]
dt       = 1       # time step [s]
n_steps  = int(t_end / dt)

# --- Initial condition ---
T_init = 25.0        # initial temperature everywhere [°C]

# --- Dirichlet boundary conditions (applied at t > 0) ---
T_left   = 2000     # [°C] — hot boundary snaps on at t=0+
T_right  = None      # None = insulated
T_top    = None
T_bottom = None

# --- Picard iteration settings (per time step) ---
max_iter = 20
k_tol    = 1e-4
relax    = 1.0

# --- Output settings ---
n_snapshots = 8      # number of time snapshots to plot

# ============================================================
# MESH GENERATION
# ============================================================

def generate_mesh(Lx, Ly, nx, ny):
    x = np.linspace(0, Lx, nx + 1)
    y = np.linspace(0, Ly, ny + 1)
    X, Y = np.meshgrid(x, y)
    nodes = np.column_stack([X.ravel(), Y.ravel()])
    n_nodes = len(nodes)

    elements = []
    for j in range(ny):
        for i in range(nx):
            n0 = j * (nx + 1) + i
            n1 = n0 + 1
            n2 = n0 + (nx + 1)
            n3 = n2 + 1
            elements.append([n0, n1, n3])
            elements.append([n0, n3, n2])
    elements = np.array(elements)
    return nodes, elements, n_nodes

# ============================================================
# ELEMENT ROUTINES
# ============================================================

def element_area(nodes_e):
    x, y = nodes_e[:, 0], nodes_e[:, 1]
    return 0.5 * abs((x[1]-x[0])*(y[2]-y[0]) - (x[2]-x[0])*(y[1]-y[0]))

def element_stiffness_and_load(nodes_e, k_e, Q_e):
    x, y = nodes_e[:, 0], nodes_e[:, 1]
    A = element_area(nodes_e)
    denom = 2.0 * A
    b = np.array([y[1]-y[2], y[2]-y[0], y[0]-y[1]]) / denom
    c = np.array([x[2]-x[1], x[0]-x[2], x[1]-x[0]]) / denom
    K_e = k_e * A * (np.outer(b, b) + np.outer(c, c))
    f_e = Q_e * A / 3.0 * np.ones(3)
    return K_e, f_e

# ============================================================
# LUMPED MASS MATRIX
# ============================================================

def assemble_lumped_mass(nodes, elements, mat_ids, rho_vals, cp_vals):
    """Assemble lumped (diagonal) mass matrix: M_i = sum over elements of rho*cp*A/3."""
    n = len(nodes)
    M_diag = np.zeros(n)
    for ie, elem in enumerate(elements):
        A = element_area(nodes[elem])
        rho_cp = rho_vals[mat_ids[ie]] * cp_vals[mat_ids[ie]]
        contrib = rho_cp * A / 3.0
        for a in range(3):
            M_diag[elem[a]] += contrib
    return M_diag

# ============================================================
# STIFFNESS ASSEMBLY
# ============================================================

def assemble_stiffness(nodes, elements, k_per_elem, Q_per_elem):
    n = len(nodes)
    K = lil_matrix((n, n))
    f = np.zeros(n)
    for ie, elem in enumerate(elements):
        K_e, f_e = element_stiffness_and_load(nodes[elem], k_per_elem[ie], Q_per_elem[ie])
        for a in range(3):
            f[elem[a]] += f_e[a]
            for b_idx in range(3):
                K[elem[a], elem[b_idx]] += K_e[a, b_idx]
    return K.tocsr(), f

# ============================================================
# BOUNDARY CONDITIONS
# ============================================================

def get_boundary_nodes(nodes, Lx, Ly):
    tol = 1e-10
    return {
        "left":   np.where(np.abs(nodes[:, 0])      < tol)[0],
        "right":  np.where(np.abs(nodes[:, 0] - Lx) < tol)[0],
        "bottom": np.where(np.abs(nodes[:, 1])      < tol)[0],
        "top":    np.where(np.abs(nodes[:, 1] - Ly) < tol)[0],
    }

def apply_dirichlet(K, f, bc_nodes, bc_vals):
    K = K.tolil()
    bc_set = set(bc_nodes)
    for node, val in zip(bc_nodes, bc_vals):
        col = np.array(K[:, node].todense()).flatten()
        for i in range(len(f)):
            if i not in bc_set:
                f[i] -= col[i] * val
    for node, val in zip(bc_nodes, bc_vals):
        K[node, :] = 0
        K[:, node] = 0
        K[node, node] = 1.0
        f[node] = val
    return K.tocsr(), f

# ============================================================
# MATERIAL ASSIGNMENT
# ============================================================

def assign_materials(nodes, elements, x_interface):
    centroids = np.mean(nodes[elements], axis=1)
    return np.where(centroids[:, 0] < x_interface, 0, 1)

# ============================================================
# HEAT FLUX
# ============================================================

def compute_heat_flux(nodes, elements, T, k_per_elem):
    n_elem = len(elements)
    qx, qy = np.zeros(n_elem), np.zeros(n_elem)
    for ie, elem in enumerate(elements):
        nodes_e = nodes[elem]
        T_e = T[elem]
        x, y = nodes_e[:, 0], nodes_e[:, 1]
        A = element_area(nodes_e)
        denom = 2.0 * A
        b = np.array([y[1]-y[2], y[2]-y[0], y[0]-y[1]]) / denom
        c = np.array([x[2]-x[1], x[0]-x[2], x[1]-x[0]]) / denom
        qx[ie] = -k_per_elem[ie] * (b @ T_e)
        qy[ie] = -k_per_elem[ie] * (c @ T_e)
    return qx, qy

# ============================================================
# PLOTTING
# ============================================================

def plot_snapshots(nodes, elements, snapshots, snap_times, x_interface):
    n = len(snapshots)
    ncols = 3
    nrows = int(np.ceil(n / ncols))
    fig, axes = plt.subplots(nrows, ncols, figsize=(7.5, 2.5 * nrows),
                             constrained_layout=True)
    if nrows * ncols == 1:
        axes = np.array([axes])
    axes = np.atleast_2d(axes).flatten()

    tri = Triangulation(nodes[:, 0], nodes[:, 1], elements)

    T_all = np.concatenate(snapshots)
    vmin, vmax = T_all.min(), T_all.max()

    tcf = None
    for i, (T_snap, t) in enumerate(zip(snapshots, snap_times)):
        ax = axes[i]
        tcf = ax.tricontourf(tri, T_snap, levels=30, cmap='inferno', vmin=vmin, vmax=vmax)
        ax.axvline(x_interface, color='w', ls='--', lw=0.5)
        ax.set_title(f't = {t:.1f} s', fontsize=9)
        ax.set_aspect('equal')
        ax.set_xlabel('x [m]', fontsize=7)
        ax.set_ylabel('y [m]', fontsize=7)
        ax.tick_params(labelsize=6)

    for j in range(i + 1, len(axes)):
        axes[j].set_visible(False)

    fig.colorbar(tcf, ax=axes.tolist(), label='Temperature [°C]', shrink=0.6)
    fig.suptitle('Transient Temperature Evolution', fontsize=11)
    plt.savefig('fem_transient_snapshots.png', dpi=150, bbox_inches='tight')
    plt.show()
    print("Saved: fem_transient_snapshots.png")

def plot_centerline_history(nodes, snapshots, snap_times, Ly):
    """Plot T vs x along the horizontal centerline at each snapshot."""
    tol = Ly / 40
    center_mask = np.abs(nodes[:, 1] - Ly / 2) < tol
    x_center = nodes[center_mask, 0]
    sort_idx = np.argsort(x_center)
    x_sorted = x_center[sort_idx]

    fig, ax = plt.subplots(figsize=(7.5, 4.5))
    for T_snap, t in zip(snapshots, snap_times):
        T_center = T_snap[center_mask][sort_idx]
        ax.plot(x_sorted, T_center, label=f't={t:.0f}s')

    ax.set_xlabel('x [m]')
    ax.set_ylabel('Temperature [°C]')
    ax.set_title('Centerline Temperature vs. Time')
    ax.legend(fontsize=7, ncol=2)
    ax.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig('fem_transient_centerline.png', dpi=150, bbox_inches='tight')
    plt.show()
    print("Saved: fem_transient_centerline.png")

# ============================================================
# MAIN — TRANSIENT SOLVER
# ============================================================

if __name__ == "__main__":
    # --- Mesh ---
    nodes, elements, n_nodes = generate_mesh(Lx, Ly, nx, ny)
    n_elem = len(elements)
    mat_ids = assign_materials(nodes, elements, x_interface)
    mat1_mask = (mat_ids == 0)
    print(f"Mesh: {n_nodes} nodes, {n_elem} elements")
    print(f"Material 1 (k(T), rho={rho1}, cp={cp1}): {np.sum(mat1_mask)} elements")
    print(f"Material 2 (k={k2}, rho={rho2}, cp={cp2}): {np.sum(~mat1_mask)} elements")
    print(f"Time: {n_steps} steps x dt={dt}s = {t_end}s\n")

    # --- k(T) interpolator ---
    k1_T = np.array(k1_table_T, dtype=float)
    k1_k = np.array(k1_table_k, dtype=float)
    def k1_of_T(T_val):
        return np.interp(T_val, k1_T, k1_k)

    # --- Lumped mass (constant, assembled once) ---
    rho_vals = [rho1, rho2]
    cp_vals  = [cp1,  cp2]
    M_diag = assemble_lumped_mass(nodes, elements, mat_ids, rho_vals, cp_vals)
    M_over_dt = M_diag / dt        # precompute M/dt vector
    M_sparse = diags(M_over_dt)    # sparse diagonal for adding to K

    # --- Source term (constant) ---
    Q_per_elem = np.where(mat_ids == 0, Q1, Q2)

    # --- Boundary conditions ---
    bnd = get_boundary_nodes(nodes, Lx, Ly)
    bc_node_list, bc_val_list = [], []
    for edge, T_bc in [("left", T_left), ("right", T_right),
                        ("top", T_top), ("bottom", T_bottom)]:
        if T_bc is not None:
            bc_node_list.append(bnd[edge])
            bc_val_list.append(np.full(len(bnd[edge]), T_bc))
    bc_nodes = np.concatenate(bc_node_list)
    bc_vals  = np.concatenate(bc_val_list)

    # --- Initial condition ---
    T = np.full(n_nodes, T_init)

    # --- Snapshot schedule ---
    snap_steps = np.linspace(0, n_steps, n_snapshots + 1, dtype=int)
    # Always include step 0 and final
    snap_steps = np.unique(np.concatenate([[0, n_steps], snap_steps]))
    snapshots  = [T.copy()]
    snap_times = [0.0]

    # --- Initialize k field from T_init ---
    k_per_elem = np.where(mat1_mask, k1_of_T(T_init), k2)

    # --- Time loop ---
    print(f"{'Step':>6s}  {'t [s]':>8s}  {'T_min':>8s}  {'T_max':>8s}  {'Picard':>6s}")
    print("-" * 46)

    for step in range(1, n_steps + 1):
        t = step * dt
        T_old = T.copy()

        # Picard iteration within this time step
        for it in range(max_iter):
            # Assemble stiffness with current k
            K, f_source = assemble_stiffness(nodes, elements, k_per_elem, Q_per_elem)

            # Effective system: (M/dt + K) T^{n+1} = M/dt * T^n + f
            A_eff = (M_sparse + K).tolil()
            rhs = M_over_dt * T_old + f_source

            # Apply Dirichlet BCs
            A_sys, rhs_sys = apply_dirichlet(A_eff, rhs.copy(), bc_nodes, bc_vals)

            # Solve
            T = spsolve(A_sys, rhs_sys)

            # Update k for material 1
            T_elem = np.mean(T[elements], axis=1)
            k_new = k_per_elem.copy()
            k_new[mat1_mask] = k1_of_T(T_elem[mat1_mask])
            k_new = relax * k_new + (1.0 - relax) * k_per_elem

            with np.errstate(divide='ignore', invalid='ignore'):
                max_dk = np.max(np.abs(k_new - k_per_elem) / np.maximum(np.abs(k_per_elem), 1e-30))

            k_per_elem = k_new

            if max_dk < k_tol:
                break

        # Print progress at snapshot steps or every 10%
        if step in snap_steps or step % max(1, n_steps // 10) == 0:
            print(f"{step:6d}  {t:8.2f}  {T.min():8.2f}  {T.max():8.2f}  {it+1:6d}")

        # Store snapshot
        if step in snap_steps:
            snapshots.append(T.copy())
            snap_times.append(t)

    print(f"\nDone. Final T range: [{T.min():.2f}, {T.max():.2f}]")

    # --- Heat flux at final time ---
    qx, qy = compute_heat_flux(nodes, elements, T, k_per_elem)
    q_mag = np.sqrt(qx**2 + qy**2)
    print(f"|q|_max at t_end = {q_mag.max():.1f} W/m^2")

    # --- Plots ---
    plot_snapshots(nodes, elements, snapshots, snap_times, x_interface)
    plot_centerline_history(nodes, snapshots, snap_times, Ly)