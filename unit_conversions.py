# By submitting this assignment, I agree to the following:
#   "Aggies do not lie, cheat, or steal, or tolerate those who do."
#   "I have not given or received any unauthorized aid on this assignment."
#
# Names:       Magnusson Hudak
#              Tanner Ross
#              Zachariah Assi
#			Oscar Umanzor
#
# Section:     503
# Assignment:  3.15 Unit Conversions
# Date:         2/3/2024



number = float(input('Please enter the quantity to be converted:')) #input for the number used in the rest of conversions



def Newtons_Convert(x):
    Newton = x * 4.44822
    return Newton


print(f'{number:.2f} pounds force is equivalent to {Newtons_Convert(number):.2f} Newtons')


def feet_convert(y):
    feet = y * 3.28084
    return feet


print(f'{number:.2f} meters is equivalent to {feet_convert(number):.2f} feet')


def atmosphere(z):
    kilo = z * 101.325
    return kilo


print(f'{number:.2f} atmospheres is equivalent to {atmosphere(number):.2f} kilopascals')


def watts(L):
    BTU = L * 3.412141633
    return BTU


print(f'{number:.2f} watts is equivalent to {watts(number):.2f} BTU per hour')


def liters(P):
    degrees = (P * 0.2641722) * 60
    return degrees


print(f'{number:.2f} liters per second is equivalent to {liters(number):.2f} US gallons per minute')


def degree(H):
    Fer = (H * 1.8) + 32
    return Fer


print(f'{number:.2f} degrees Celsius is equivalent to {degree(number):.2f} degrees Fahrenheit')

