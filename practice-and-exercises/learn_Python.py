#Incline plane
import matplotlib.pyplot as plt
import numpy as np

theta = 0
time = 0
mass = 2
gravity = 9.81
mu_s = 1.5
mu_k = 0.4
inc = 0.1
velocity = 0
distance = 0
length = 10
theta_inc = 0.01
normal = mass*gravity*np.cos(theta)
max_static_friction = mu_s * normal
parallel_force = mass*gravity*np.sin(theta)

time_list = []
distance_list = []
velocity_list = []
theta_list = []


while parallel_force < max_static_friction and theta <= np.pi/2:
    parallel_force = mass*gravity*np.sin(theta)
    normal = mass * gravity * np.cos(theta)
    max_static_friction = mu_s * normal
    theta += theta_inc
    theta_list.append(theta)
    time_list.append(time)
    velocity_list.append(velocity)
    distance_list.append(distance)
    if parallel_force >= max_static_friction:
        theta_inc = 0
        while distance <= length:
            net_force = parallel_force - max_static_friction
            acceleration = net_force/mass
            velocity = velocity + acceleration*time
            distance = velocity*time + 0.5*acceleration*time**2
            time += inc
            theta += theta_inc
            time_list.append(time)
            distance_list.append(distance)
            velocity_list.append(velocity)
            theta_list.append(theta)


def show_vel():
    plt.plot(time_list, velocity_list)
    plt.show()


def show_theta():
    print(max((np.rad2deg(theta_list))))


show_vel()




