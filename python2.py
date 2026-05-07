"""
SymmetryElements.py

This script is the code to familiarize yourself with basic symmetry operations. 

(c) Hsiao 2024 (modified from Shamberger 2020)..................................................................................................)

@author: Kaiwen Hsiao    email: kwhsiao@tamu.edu
"""

# these lines required to run!  Do not change the next couple lines
import numpy as np
import sympy as sp

# %%###########################################################################
#          ROTATION MATRICES                                                  #
###############################################################################    
print("\n************************************")
print("ROTATION MATRICES")

# In 3D, a rotation matrix around the x-axis is given as below (note: rotation 
# around the y and z axes (in cartesian coordinate systems) are given: 
# https://en.wikipedia.org/wiki/Rotation_matrix ).

pi = np.pi     # define pi = 3.14159...
theta = pi     # define theta, the angle of rotation

A1 =  np.mat([[1, 0, 0],         # A1 is a 3x3 rotation matrix around the x axis!
      [0, np.cos(theta), -1*np.sin(theta)],
      [0, np.sin(theta), np.cos(theta)]])

print(A1)
# note: numerically, 1e-16 is essentially ~ 0.

# 1) Modify the code below to calculate the effect of a 90 degree (pi/2) rotation 
# around the x axis on the following points: 1,1,1

theta = pi/2     # define theta, the angle of rotation

A1 =  np.mat([[1, 0, 0],         
      [0, np.cos(theta), -1*np.sin(theta)],
      [0, np.sin(theta), np.cos(theta)]])

b =   np.mat([[1],[1],[1]])     # b is a column vector!

print(" ")
print("90deg rotation around x axis")
print("A1*b: \n",A1*b)

# 2) Modify the code below to calculate the effect of a 90 degree (pi/2) rotation 
# around the y axis on the following points: 1,1,1

theta = pi/2     # define theta, the angle of rotation

A1 =  np.mat([[np.cos(theta), 0, np.sin(theta)],
      [0, 1, 0],
      [-np.sin(theta), 0, np.cos(theta)]])

b =   np.mat([[1],[1],[1]])     # b is a column vector!

print(" ")
print("90deg rotation around y axis")
print("A1*b: \n",A1*b)

# If you rotate a point around the x axis by pi/2 radians 4x in a row, you should
# come back to the original point! Using rotation matrices, we can string additional
# operations on the left hand side like this: c = A3.A2.A1.b, where A1, A2, and 
# A3 are all rotation matrices, operating in that particular order (i.e., point
# b is first rotated by A1, next rotated by A2, and finally rotated by A3, in 
# that particular order).
#
# 3) Modify the code below to illustrate the results of rotating the point 1,1,1 
# once, twice, three times, and four times by a pi/2 rotation around the x axis.

theta = pi/2     # define theta, the angle of rotation

A1 =  np.mat([[1, 0, 0],         # A1 is a 3x3 rotation matrix around the x axis!
      [0, np.cos(theta), -1*np.sin(theta)],
      [0, np.sin(theta), np.cos(theta)]])

b =   np.mat([[1],[1],[1]])     # b is a column vector!

print(" ")
print("sequential rotations around x axis")
print("original point: \n", b)
print("point after 1 rotation: \n", A1*b) # the point after n rotations around the x-axis
print("point after 2 rotations: \n", A1*A1*b)
print("point after 3 rotations: \n", A1*A1*A1*b)
print("point after 4 rotations: \n", A1*A1*A1*A1*b)
# %%###########################################################################
#          INVERSION POINTS                                                   #
###############################################################################    
print("\n************************************")
print("\nINVERSION POINTS")

#The inversion operation is given as follows:

x = sp.Symbol('x')
y = sp.Symbol('y')
z = sp.Symbol('z')
b = sp.Matrix([[x],[y],[z]])

I = sp.Matrix([[1,0,0], [0,1,0], [0,0,1]])  # the identity matrix!

#4) modify the code below to define the inversion matrix 
INV = sp.Matrix([[-1,0,0], [0,-1,0], [0,-1,0]])  # inversion operation!


print("the original point:", b)  # the original point
print("the point operated on by the identity operation:", I*b)  # the original point
print("the point operated on by the inversion operation:", INV*b)  # the inverted point 

# %%###########################################################################
#          REFLECTION PLANES                                                  #
###############################################################################    
print("\n************************************")
print("\nREFLECTION PLANES")

# The reflection operation across the x=0 plane (yz plane), also called 𝜎_𝑥 , 
# is given as:

REFLX_x = sp.Matrix([[-1,0,0], [0,1,0], [0,0,1]])  # sigma_x operation

print("the original point:", b)  # the original point
print("the point operated on by sigma_x:", REFLX_x*b)  # the reflected point

#5) modify the code below to define reflection operation across the z=0 plane (xy) plane 

REFLX_z = sp.Matrix([[1,0,0], [0,1,0], [0,0,-1]]) # sigma_z operation

print("the original point:", b) # the original point 
print("the point operated on by sigma_z:", REFLX_z*b) # the reflected point

# %%###########################################################################
#          PROBLEMS                                                           #
###############################################################################    
print("\n************************************\n")
print("PROBLEM 1\n")

# Add code below (hint: copy what you need from above!) to show that sequential
# operation of: 1) a two-fold rotation around x (2_𝑥), and 2) a reflection 
# across the yz plane (sigma_𝑥) is equivalent to the inversion operation


b = np.mat([[1],[1],[1]])

theta = pi # rotational degree

A1 = np.mat([[1, 0, 0],         # A1 is a 3x3 rotation matrix around the x axis!
      [0, np.cos(theta), -1*np.sin(theta)],
      [0, np.sin(theta), np.cos(theta)]])

print("2-fold rotation matrix around x-axis: \n", A1)
print("original point: \n", b)
print("point after rotation: \n", A1*b)

REFLEX = np.mat([[-1, 0, 0],
               [0, 1, 0],
               [0, 0, 1]])
print("reflection across x-axis matrix: \n", REFLEX)
print("point after reflection across x-axis: \n", REFLEX*A1*b)

INV = ([[-1, 0, 0],
              [0, -1, 0],
              [0, 0, -1]])
print("original point after inversion: \n", INV*b)


print("\n************************************\n")
print("PROBLEM 2\n")

# Add code below (hint: copy what you need from above!) to show a sequential 
# operation by sigma_𝑥, sigma_𝑦, and sigma_z.  Which operation is this sequence equivalent
# to?

b = np.mat([[1],[1],[1]])

REFLEX_1 = np.mat([[-1, 0, 0],
               [0, 1, 0],
               [0, 0, 1]])
REFLEX_2 = np.mat([[1, 0, 0],
               [0, -1, 0],
               [0, 0, 1]])
REFLEX_3 = np.mat([[1, 0, 0],
               [0, 1, 0],
               [0, 0, -1]])

print("original point: \n", b)
print("point after reflected across each axis: \n", REFLEX_1*REFLEX_2*REFLEX_3*b)
print("this sequence is equivalent to an Inversion operation")

print("\n************************************\n")
print("PROBLEM 3\n")
# Add code below (hint: copy what you need from above!) to show that sequential
# operation of: 1) a four-fold rotation around x (2_𝑥), and 2) a inversion 
# across the origin 

b = np.mat([[1],[1],[1]])
theta = pi/2 # rotational degree

A1 =  np.mat([[1, 0, 0],         # A1 is a 3x3 rotation matrix around the x axis!
      [0, np.cos(theta), -1*np.sin(theta)],
      [0, np.sin(theta), np.cos(theta)]])

INV = np.mat([[-1, 0, 0],         # INV is an inversion matrix around the origin!
              [0,-1, 0],
              [0, 0, -1]])

print("original point: \n", b)
print("point after four-fold rotation around x axis, followed by inversion: \n", INV*(A1*b))
print("point after four-fold rotation around x axis, followed by inversion: \n", INV*(A1*(A1*INV*b)))
print("point after four-fold rotation around x axis, followed by inversion: \n", INV*(A1*(INV*(A1*(A1*INV*b)))))
print("point after four-fold rotation around x axis, followed by inversion: \n", INV*(A1*(INV*(A1*(INV*(A1*(A1*INV*b)))))))