# By submitting this assignment, I agree to the following:
# "Aggies do not lie, cheat, or steal, or tolerate those who do."
# "I have not given or received any unauthorized aid on this assignment."
#
# Name: Tanner Ross
# Section: 503
# Assignment: 3.18
# Date: 2/3/2024
#


import math # needed for sqrt


def tri_area(a):
    return math.sqrt(3)/4*a**2


def sqarea(a):
    return a**2


def pent(a):
    return 1/4*math.sqrt(5*(5+2*math.sqrt(5)))*a**2


def deca(a):
    return 3*(2+math.sqrt(3))*a**2


a = float(input("Please enter the side length: "))
print(f'A triangle with side {a:.2f} has area {tri_area(a):.3f}')
print(f'A square with side {a:.2f} has area {sqarea(a):.3f}')
print(f'A pentagon with side {a:.2f} has area {pent(a):.3f}')
print(f'A dodecagon with side {a:.2f} has area {deca(a):.3f}')
