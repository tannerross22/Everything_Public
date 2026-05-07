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

# Start off each of the areas at 0
side_area = 0
top_area = 0
for i in range(1, layers+1):
    side_area += 3*i*length**2  # Add the side area for each layer
    if i == 1:
        top_area += sqrt(3)/4*length**2  # Top layer is different
    else:
        top_area += sqrt(3)/4*(i*length)**2  # Other layers need the layer above it to subtract off
        top_area -= sqrt(3)/4*((i-1)*length)**2

total_area = side_area+top_area
print(f'You need {total_area:.2f} m^2 of gold foil to cover the pyramid')
