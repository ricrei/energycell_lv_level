import os
import csv
import time
import numpy as np
import pandas as pd
import pandapower as pp
import pandapower.networks as pn
import matplotlib.pyplot as plt

import bz2
import _pickle as cPickle

from pandapower.plotting.plotly import simple_plotly
from pandapower.plotting.plotly import pf_res_plotly


def get_tan_phi(cos_phi):
  tan_phi = np.tan(np.arccos(cos_phi))
  return tan_phi

def print_res(net):
 print('q_mvar  ' + str(net.sgen["q_mvar"]))
 print('U in pu ' + str(net.res_bus.vm_pu))

net = pn.create_kerber_landnetz_freileitung_1()

pv_p_mw = 0.018
tan_phi_max = get_tan_phi(.9)
U1 = .93
U2 = .97
U3 = 2 - U2
U4 = 2 - U1

for index in net.load.index:
  pp.create_sgen(net, net.load.loc[index, "bus"], p_mw = pv_p_mw, q_mvar = 0.0, name='pv_'+str(net.load.loc[index, "bus"]))
  net.load.loc[index, "p_mw"] = 0.0

pp.runpp(net)
#print_res(net)

#pf_res_plotly(net, aspectratio=(1,1))

n = 7
Q_t = pd.DataFrame(columns=range(n+1))
P_t = pd.DataFrame(columns=range(n+1))
S_t = pd.DataFrame(columns=range(n+1))
U_t = pd.DataFrame(columns=range(n+1))
cos_phi = pd.DataFrame(columns=range(n+1))
Q_t[0] = net.sgen["q_mvar"]
P_t[0] = net.sgen["p_mw"]
U_t[0] = net.res_bus.vm_pu[net.sgen["bus"]]
S_t[0] = np.sqrt(Q_t[0]**2 + P_t[0]**2)
cos_phi[0] = S_t[0]/P_t[0]

for i in range(1,n+1):
 #print(str(i)+'#########################')
 for index in net.sgen.index:
  U = net.res_bus.vm_pu[net.sgen.loc[index, "bus"]]
  P = net.sgen.loc[index, "p_mw"]
  Q = P * tan_phi_max
  m = Q/(U2 - U1)
  if U <= .93: # 1
      Q_U = Q
  if U <= .97 and U >= .93: # 2
      Q_U = -m*(U-U2)
  if U <= 1.03 and U >= .97: # 3
      Q_U = 0
  if U <= 1.07 and U >= 1.03: # 4
      Q_U = -m*(U-U3)
  if U >= 1.07: # 5
      Q_U = -Q

  net.sgen.loc[index, "q_mvar"] = Q_U

 pp.runpp(net)
 Q_t[i] = net.sgen["q_mvar"]
 U_t[i] = net.res_bus.vm_pu[net.sgen["bus"]]
 P_t[i] = net.sgen["p_mw"]
 S_t[i] = np.sqrt(Q_t[i]**2 + P_t[i]**2)
 cos_phi[i] = P_t[i]/S_t[i]

 #print_res(net)
 

 #pf_res_plotly(net, aspectratio=(1,1))

print(Q_t)
print(U_t)

#plt.figure()
#plt.plot(Q_t.T)

plt.figure()
plt.plot(cos_phi.T)

plt.figure()
plt.plot(U_t.T)

plt.show()
