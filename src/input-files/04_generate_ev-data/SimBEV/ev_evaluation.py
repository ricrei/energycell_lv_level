import os
import csv
import time
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

import bz2
import pickle
import _pickle as cPickle

#####################################################################
### Pickle a file and then compress it into a file with extension ###
#####################################################################
def compress_pickle(title, data):
     '''
     Method to pickle a file and then compress it into a file with extension.

     :param title: string
     :param data:  DataFrame
     '''
     with bz2.BZ2File(title, 'w') as f: 
      cPickle.dump(data, f)
     f.close()

#######################################
### Load any compressed pickle file ###
#######################################
def decompress_pickle(file):
     '''
     Method to load a compressed pickle file.

     :param file: string
     :return: DataFrame
     '''
     f = bz2.BZ2File(file, 'rb')
     data = cPickle.load(f)
     f.close()
     return data

EV = decompress_pickle('04_ev_load.pbz2')
EV_flex = decompress_pickle('04_ev_load_flex.pbz2')
total_share = decompress_pickle('total_share.pbz2')

sum_EV = EV.sum()

print('Avarage consumption of one car per year in kWh at home: ' + str(sum_EV.sum()/60/360))
print('Avarage consumption of one car in kWh/100km at home: ' + str(sum_EV.sum()/60/360/120))

total_share = total_share*26
print('Total consumption at home: %s kWh per year' % (total_share['6_home'].values))

sum_total = total_share.loc[0].sum()
home_share = total_share['6_home']*100/sum_total
print('Share of home charged energy: %s percent' % home_share.values)

plt.figure()
#plt.plot(EV['ev_1_30kWh_rural_charging_demand'])
plt.plot(EV_flex['ev_1_30kWh_rural_parking'])
plt.plot(EV['ev_1_30kWh_rural'])
plt.show()
