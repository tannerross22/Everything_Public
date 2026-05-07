def print_values(x, y):
    for i in range(x, y + 1):
        print(i, end=' ')


input1 = int(input())
input2 = int(input())

print('Testing static input: ')
print_values(4, 8)
print(f'\nTesting user input: ')
print_values(input1, input2)