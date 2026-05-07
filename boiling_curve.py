# By submitting this assignment, I agree to the following:
#   "Aggies do not lie, cheat, or steal, or tolerate those who do."
#   "I have not given or received any unauthorized aid on this assignment."
#
# Name:         Tanner Ross
# Section:      503
# Assignment:   5.4
# Date:         2/16/2024
#

from math import *

temp = float(input("Enter the excess temperature: "))
#  (1.3, 1000) B: (5, 7000) C: (30, 1.5x106) D: (120, 2.5x104) E: (1200, 1.5x106)
# y = y0(x/xnot)
# log(𝑦1 𝑦0)/
# log(𝑥1 𝑥0)


def flux1(x):
    y = 1000*(x/1.3)**((log10(7000/1000))/(log10(5/1.3)))  # for finding the flux of range1
    return y


def flux2(x):
    y = 7000 * (x / 5) ** ((log10(1500000 / 7000)) / (log10(30/5)))  # for finding the flux of range 2
    return y


def flux3(x):
    y = 1500000 * (x / 30) ** ((log10(25000 / 1500000)) / (log10(120/30)))  # for finding the flux of range 3
    return y


def flux4(x):
    y = 25000 * (x / 120) ** ((log10(1500000 / 25000)) / (log10(1200/120)))  # for finding the flux of range 4
    return y

# checking that number is valid for math
if temp < 1.3 or temp > 1200:
    print("Surface heat flux is not available")
# first range
elif 1.3 <= temp < 5:
    print(f'The surface heat flux is approximately {round(flux1(temp))} W/m^2')
# second range
elif 5 <= temp < 30:
    print(f'The surface heat flux is approximately {round(flux2(temp))} W/m^2')
# third range
elif 30 <= temp < 120:
    print(f'The surface heat flux is approximately {round(flux3(temp))} W/m^2')
# fourth range
elif 120 <= temp <= 1200:
    print(f'The surface heat flux is approximately {round(flux4(temp))} W/m^2')
