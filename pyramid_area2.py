# By submitting this assignment, I agree to the following:
#   "Aggies do not lie, cheat, or steal, or tolerate those who do."
#   "I have not given or received any unauthorized aid on this assignment."
#
# Names:       Magnusson Hudak
#              Tanner Ross
#              Zachariah Assi
#              Oscar Umanzor
#
# Section:     503
# Assignment:  6.11
# Date:         2/20/2024

from math import *
length = float(input("Enter the side length in meters: "))
layers = int(input("Enter the number of layers: "))

side_area_1 = 3*length**2
difference = 3*length*layers - 3*length*(layers-1)
nside_area = side_area_1 + (layers-1) * difference

top_area_1 = sqrt(3)/4*length**2
difference = sqrt(3)/4*(length*layers)**2-sqrt(3)/4*(length*(layers-1))**2
ntop_area = top_area_1 + (layers-1)*difference
total_area = ntop_area+nside_area
print(f'You need {total_area:.2f} m^2 of gold foil to cover the pyramid')