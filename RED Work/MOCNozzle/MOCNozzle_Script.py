import numpy as np
import matplotlib.pyplot as plt


def isentropic_flow_relations(M, gamma):
    """Calculate isentropic flow relations."""
    T_ratio = 1 / (1 + ((gamma - 1) / 2) * M ** 2)
    P_ratio = T_ratio ** (gamma / (gamma - 1))
    rho_ratio = T_ratio ** (1 / (gamma - 1))
    return T_ratio, P_ratio, rho_ratio


def prandtl_meyer_angle(M, gamma):
    """Calculate the Prandtl-Meyer angle."""
    if M < 1:
        raise ValueError(f"Mach number must be greater than 1 for Prandtl-Meyer calculation, got M={M}.")
    nu = (np.sqrt((gamma + 1) / (gamma - 1)) *
          np.arctan(np.sqrt((gamma - 1) * (M**2 - 1) / (gamma + 1))) -
          np.arctan(np.sqrt(M**2 - 1)))
    return np.degrees(nu)



def area_mach_relation(M, gamma):
    """Calculate the area-Mach relation."""
    term1 = ((gamma + 1) / 2) ** (-((gamma + 1) / (2 * (gamma - 1))))
    term2 = (1 / M) * ((1 + ((gamma - 1) / 2) * M ** 2) ** ((gamma + 1) / (2 * (gamma - 1))))
    return term1 * term2

def export_to_txt(x, y, filename="nozzle_contour.txt"):
    """Export the nozzle contour points to a .txt file with z-coordinates set to 0."""
    with open(filename, mode="w") as file:
        for xi, yi in zip(x, y):
            file.write(f"{xi:.6f}, {yi:.6f}, 0.000000\n")
    print(f"Nozzle contour points exported to {filename}")

def generate_nozzle_contour(gamma, d_throat, d_exit, L_nozzle, num_points=50):
    """Generate the nozzle contour using MOC with specified dimensions and desired axial length."""
    # Radii from diameters
    r_throat = d_throat / 2
    r_exit = d_exit / 2

    A_throat = np.pi * r_throat**2
    A_exit = np.pi * r_exit**2

    # Calculate Area Ratio
    A_ratio = np.linspace(1, A_exit / A_throat, num_points)

    # Initialize Mach numbers (start at M=1 at the throat)
    Mach_numbers = np.zeros(num_points)
    Mach_numbers[0] = 1.0  # Starting point: M = 1

    for i in range(1, num_points):
        # Solve iteratively to find supersonic M for the given A_ratio[i]
        def mach_solver(M):
            return area_mach_relation(M, gamma) - A_ratio[i]

        # Use a numerical solver to find supersonic Mach number
        from scipy.optimize import fsolve
        Mach_numbers[i] = fsolve(mach_solver, Mach_numbers[i - 1] + 0.1)[0]

    # Calculate Prandtl-Meyer angles
    nu = np.array([prandtl_meyer_angle(M, gamma) for M in Mach_numbers])
    theta_wall = np.radians(nu[-1])

    # Generate x and y coordinates
    x = np.zeros(num_points)
    y = np.zeros(num_points)
    y[0] = r_throat  # Start at the throat radius

    for i in range(1, num_points):
        delta_x = 1 / (num_points - 1)  # Increment x linearly (normalized length)
        delta_y = delta_x * np.tan(theta_wall - np.radians(nu[i]))
        x[i] = x[i - 1] + delta_x
        y[i] = max(y[i - 1] + delta_y, r_throat)  # Constrain minimum y to throat radius

    # Scale radial dimension so final radius matches the exit radius
    scale_factor_y = r_exit / y[-1]
    y *= scale_factor_y

    # Scale axial length to desired nozzle length
    scale_factor_x = L_nozzle / x[-1]
    x *= scale_factor_x

    # Return scaled x and y, and Mach numbers
    return x, y, Mach_numbers




# Input parameters
gamma = 1.19  # Specific heat ratio for air-like gases
d_throat = 0.0327  # Throat diameter (m)
d_exit = 0.0715  # Exit diameter (m)
num_points = 100  # Number of points along the nozzle
L_nozzle = 0.01632 # length in meters

# Generate the nozzle contour
x, y, Mach_numbers = generate_nozzle_contour(gamma, d_throat, d_exit, L_nozzle, num_points)

# Plot the nozzle contour
plt.figure(figsize=(8, 4))
plt.plot(x, y, label="Nozzle Contour")
plt.xlabel("Axial Distance (m)")
plt.ylabel("Radial Distance (m)")
plt.title("Optimal Nozzle Contour")
plt.grid()
plt.legend()
plt.show()

# Print key values
for i in range(0, len(x), len(x) // 10):
    print(f"x = {x[i]:.3f} m, y = {y[i]:.3f} m, Mach = {Mach_numbers[i]:.2f}")

export_to_txt(x,y,filename="nozzle_contour_scaled.txt")