import math
tau = 2*math.pi
digits = int(input("Please enter the number of digits of precision for tau: "))

print(f'The value of tau to {digits} digits is: {tau:.{digits}f}')
