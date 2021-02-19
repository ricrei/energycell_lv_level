import math
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

def get_tan_phi(cos_phi):
  tan_phi = np.tan(np.arccos(cos_phi))
  return tan_phi

U_pu = np.array([.9, .91, .92, .93, .94, .95, .96, .97, .98, .99, 1, 1.01, 1.02, 1.03, 1.04 ,1.05, 1.06, 1.07, 1.08, 1.09, 1.1])
Q_t = 0*U_pu
#S_t = Q_t
cos_phi = 0*U_pu

tan_phi_max = get_tan_phi(.9)
U1 = .93
U2 = .97
U3 = 2 - U2
U4 = 2 - U1
P = 10
Q = P * tan_phi_max
m = Q/(U2 - U1)

i = 0
for U in U_pu:
  if U <= 1.03 and U >= .97: # 3
      Q_U = 0
  if U >= 1.07: # 5
      Q_U = -Q
  if U <= .93: # 1
      Q_U = Q
  if U <= .97 and U >= .93: # 2
      Q_U = -m*(U-U2)
  if U <= 1.07 and U >= 1.03: # 4
      Q_U = -m*(U-U3)

  Q_t[i] = Q_U
  S_t = np.sqrt(P**2 + Q_U**2)
  cos_phi[i] = P/S_t
  i += 1

plt.figure()
plt.plot(U_pu, Q_t)
plt.plot(U_pu, cos_phi)

plt.show()
