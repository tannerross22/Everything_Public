import numpy as np
import matplotlib.pyplot as plt
import scipy.stats as stat
P =[0.6, 1, 1.4, 1.8, 2.2, 2.6, 3, 3.4, 3.8, 4.2, 4.6, 5, 5.4]
K = [5.89, 4.68, 4.1, 3.45, 3.25, 2.69, 2.25, 1.92, 1.55, 1.45, 1.19, 0.99, 0.84]

klog = []
for i in K:
    klog.append(np.log(i))

yhat = np.polyfit(P, klog, 1)
yhat_points = []
b1 = yhat[0]  # slope (B)
b0 = yhat[1]  # intercept
for i in P:
    yhat_points.append(b0+b1*i)

error = []
for i in range(len(P)):
    error.append((klog[i]-b1*P[i]-b0))
SE =0
for i in range(len(error)):
    SE+=error[i]**2
MSE = SE/len(error)
print(MSE)

f_stat = stat.f_oneway(klog,yhat_points)
print(f_stat)
# create list of points on the log scale
#plot model and log points
plt.plot(P, yhat_points)
plt.plot(P, klog)
plt.show()
