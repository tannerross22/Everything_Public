# By submitting this assignment, I agree to the following:
#   "Aggies do not lie, cheat, or steal, or tolerate those who do."
#   "I have not given or received any unauthorized aid on this assignment."
#
# Names:       Magnusson Hudak
#              Tanner Ross
#              Zachariah Assi
#         Oscar Umanzor
#
# Section:     503
# Assignment:  4.14
# Date:         2/9/2024


############ Part A ############


a = (input('Enter True or False for a: '))
b = (input('Enter True or False for b: '))
c = (input('Enter True or False for c: '))

a_val = 0
b_val = 0
c_val = 0

if (a == 'true') or (a == 'True') or (a == 'T') or (a == 't'):
    a_val = 1
    a = True
elif (a == 'false') or (a == 'False') or (a == 'f') or (a == 'F'):
    a_val = 2
    a = False
else:
    print('Invalid input')

if (b == 'true') or (b == 'True') or (b == 'T') or (b == 't'):
    b_val = 1
    b = True
elif (b == 'false') or (b == 'False') or (b == 'f') or (b == 'F'):
    b_val = 2
    b = False
else:
    print('Invalid input')

if (c == 'true') or (c == 'True') or (c == 'T') or (c == 't'):
    c_val = 1
    c = True
elif (c == 'false') or (c == 'False') or (c == 'f') or (c == 'F'):
    c_val = 2
    c = False
else:
    print('Invalid input')
############ Part A ############


############ Part B ############


abc_and = a and b and c
abc_or = a or b and a or c and b or c

print(f'a and b and c: {abc_and}')
print(f'a or b or c: {abc_or}')
############ Part B ############


############ Part C ############

XOR = a and not b or b and not a
print(f'XOR: {XOR}')
odd_number = (a and b and c) or (a and not b and not c) or (b and not c and not a) or (c and not a and not b)
print(f"Odd number: {odd_number}")
############ Part C ############
