import math
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation

# Pendulum parameters
initial_angle = math.radians(20)  # Initial angle in radians
length = 1.0  # Length of the pendulum in meters
mass = 10.0  # Mass of the pendulum in kilograms
damping_factor = 0.1  # Damping factor

# Simulation parameters
time_step = 0.01  # Time step in seconds
duration = 10.0  # Duration of the simulation in seconds

# Initialize lists to store the position values
positions_x = []
positions_y = []

# Initialize variables
time = 0.0
current_angle = initial_angle
current_angular_velocity = 0.0

# Perform the simulation
while time < duration:
    # Calculate the acceleration using the equation: acceleration = (-g / length * sin(angle)) - (damping_factor * angular_velocity)
    acceleration = (-9.8 / length * math.sin(current_angle)) - (damping_factor * current_angular_velocity)

    # Update the angular velocity and angle using numerical integration
    current_angular_velocity += acceleration * time_step
    current_angle += current_angular_velocity * time_step

    # Calculate the x and y positions of the pendulum
    x = length * math.sin(current_angle)
    y = -length * math.cos(current_angle)

    # Append the x and y positions to the lists
    positions_x.append(x)
    positions_y.append(y)

    # Increment the time
    time += time_step


# Create a function to update the plot for each frame of the animation
def update(frame):
    plt.cla()  # Clear the current plot

    # Plot the trajectory of the pendulum up to the current frame
    plt.scatter(positions_x[frame], positions_y[frame], color='red')  # Mark the current position

    plt.xlabel('x-position')
    plt.ylabel('y-position')
    plt.title('Pendulum Motion')
    plt.xlim(-1.5 * length, 1.5 * length)  # Set the x-axis limits
    plt.ylim(-1.5 * length, 0.5 * length)  # Set the y-axis limits

    # Draw a line representing the string that the ball is hanging from
    plt.plot([0, positions_x[frame]], [0, positions_y[frame]], color='blue')


# Create the animation
animation = FuncAnimation(plt.gcf(), update, frames=len(positions_x), interval=10)

plt.show()
