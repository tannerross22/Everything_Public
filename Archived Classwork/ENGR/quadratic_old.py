import matplotlib.pyplot as plt
import numpy as np
import scipy.optimize as opt
from matplotlib.animation import FuncAnimation


# Constants
gravity = 9.81
time_step = 0.0075
duration = 100

# Simulate the ball's motion
position = np.array([0.0, 2])
velocity = np.array([.5, 0])
time = 0.0
bounce = 0.85
time_values = []
position_values = []
x = np.linspace(-4, 4, 100)
threshold_speed = 0.08


def f(x):
    return x**2





def reflect_velocity(position, velocity):
    # Quadratic equation: y = f(x)
    def f(x):
        return x**2

    # Calculate the x-coordinate of the ball's position
    position_x = position[0]

    # Calculate the y-coordinate of the quadratic wall at the ball's x-coordinate
    wall_y = f(position_x)

    # Calculate the derivative of the quadratic equation at the ball's x-coordinate
    derivative = 2 * position_x

    # Calculate the tangent vector of the wall at the point of contact
    tangent_vector = np.array([1, derivative])
    tangent_vector = tangent_vector / np.linalg.norm(tangent_vector)

    # Calculate the normal vector of the wall at the point of contact
    normal_vector = np.array([-derivative, 1])
    normal_vector = normal_vector / np.linalg.norm(normal_vector)

    # Calculate the component of the ball's velocity in the direction perpendicular to the wall
    Vn = np.dot(velocity, normal_vector)

    # Calculate the vector in the direction of the normal
    VnN = Vn * normal_vector

    # Calculate the new velocity after the collision
    new_vel = velocity - 2 * VnN

    return new_vel


def snap_to_quadratic(position):
    # Quadratic equation: y = f(x)
    def f(x):
        return x ** 2

    # Solve for the x-coordinate on the quadratic curve that is closest to the ball's current x-coordinate
    result = opt.minimize_scalar(lambda x: (x - position[0]) ** 2 + (f(x) - position[1]) ** 2)
    closest_x = result.x

    # Calculate the y-coordinate on the quadratic curve for the closest x-coordinate
    closest_y = f(closest_x)

    # Set the ball's position to the closest point on the quadratic curve
    snapped_pos = np.array([closest_x, closest_y])

    return snapped_pos


while time <= duration:
    # Append current time and position to the lists
    time_values.append(time)
    position_values.append(position)

    # Update the position and velocity using the equations of motion
    position = position + velocity * time_step
    velocity = velocity - np.array([0.0, gravity]) * time_step

    # Check if the ball hits the wall
    if position[1] <= position[0]**2:
        position = snap_to_quadratic(position)
        velocity = reflect_velocity(position, velocity * bounce)
    speed = np.linalg.norm(velocity)
    if speed <= threshold_speed and -0.03 < position[0] < 0.03:
        # Subtract from the magnitude of the velocity until the speed is zero
        velocity = 0
    # Increment the time
    time += time_step

# Convert the lists to numpy arrays
time_values = np.array(time_values)
position_values = np.array(position_values)

fig, ax = plt.subplots()
line, = ax.plot([], [], 'o-', lw=2)
func_line, = ax.plot(x, x ** 2, 'r-', lw=2)


def init():
    line.set_data([], [])
    return line,


def update(frame):
    line.set_data([position_values[frame, 0]], [position_values[frame, 1]])
    return line,


ani = FuncAnimation(fig, update, frames=len(time_values), interval=time_step*1000, init_func=init, blit=True)



# Set the x and y limits of the plot
ax.set_xlim(-4, 4)
ax.set_ylim(0, 4)

plt.show()
