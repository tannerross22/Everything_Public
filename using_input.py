# By submitting this assignment, I agree to the following:
# "Aggies do not lie, cheat, or steal, or tolerate those who do."
# "I have not given or received any unauthorized aid on this assignment."
#
# Name: Tanner Ross
# Section: 503
# Assignment: 3.17
# Date: 2/3/2024
#

import math # need this for sin
print("This program calculates the applied force given mass and acceleration")
mass = float(input("Please enter the mass (kg): "))
acceleration = float(input("Please enter the acceleration (m/s^2): "))
force = mass*acceleration
print(f'Force is {force:.1f} N')
print("")
print("This program calculates the wavelength given distance and angle")
distance = float(input("Please enter the distance (nm): "))
angle = float(input("Please enter the angle (degrees): "))
wavelength = 2*distance*math.sin(angle*math.pi/180)
print(f'Wavelength is {wavelength:.4f} nm')
print("")
print("This program calculates how much Radon-222 is left given time and initial amount")
time = float(input("Please enter the time (days): "))
mass = float(input("Please enter the initial amount (g): "))
left = mass*2**(-time/3.8)
print(f'Radon-222 left is {left:.2f} g')
print("")
print("This program calculates the pressure given moles, volume, and temperature")
moles = float(input("Please enter the number of moles:"))
volume = float(input("Please enter the volume (m^3): "))
temp = float(input("Please enter the temperature (K): "))
pressure = moles*8.314*temp/volume/1000
print(f'Pressure is {pressure:.0f} kPa')