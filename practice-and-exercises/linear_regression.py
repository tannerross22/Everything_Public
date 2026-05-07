import numpy as np
x = [0,40.64,81.28,121.92,162.56]
y = [25.27,25.06,24.57, 24.17, 23.86]
# x and y list of data

yhat = np.polyfit(x,y, 1)
# find the polynomial fit (told linear in the problem)
b1 = yhat[0]
b0 = yhat[1]
print(np.polyval([b1,b0],97)) # using the linear terms, predict the final value at 97 mm

