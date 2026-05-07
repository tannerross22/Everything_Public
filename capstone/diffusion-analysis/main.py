import numpy as np


def calculate_actuator_lengths(theta, phi, fixed_points, moving_points, neutral_lengths):
    """
    Calculate actuator lengths for given angles.

    Parameters:
        theta (float): Tilt angle in radians.
        phi (float): Pan angle in radians.
        fixed_points (array): (n, 3) array of fixed anchor points (x, y, z).
        moving_points (array): (n, 3) array of moving points in neutral position.
        neutral_lengths (array): Rest lengths of actuators in neutral position.

    Returns:
        lengths (array): Adjusted lengths for each actuator.
    """
    # Define rotation matrices
    R_x = np.array([[1, 0, 0],
                    [0, np.cos(theta), -np.sin(theta)],
                    [0, np.sin(theta), np.cos(theta)]])
    R_y = np.array([[np.cos(phi), 0, np.sin(phi)],
                    [0, 1, 0],
                    [-np.sin(phi), 0, np.cos(phi)]])

    # Total rotation
    R = np.dot(R_y, R_x)

    # Rotate moving points
    rotated_points = np.dot(moving_points, R.T)

    # Calculate new lengths
    lengths = np.linalg.norm(rotated_points - fixed_points, axis=1)

    return lengths


# Example setup
fixed_points = np.array([[1, 0, 0], [-1, 0, 0], [0, 1, 0], [0, -1, 0]])  # Example anchors
moving_points = np.array([[1, 0, 1], [-1, 0, 1], [0, 1, 1], [0, -1, 1]])  # Neutral positions
neutral_lengths = np.linalg.norm(moving_points - fixed_points, axis=1)

# Input angles (radians)
theta = np.radians(0)  # Example tilt
phi = np.radians(0)  # Example pan

# Calculate actuator lengths
actuator_lengths = calculate_actuator_lengths(theta, phi, fixed_points, moving_points, neutral_lengths)
print("Actuator Lengths:", actuator_lengths)
