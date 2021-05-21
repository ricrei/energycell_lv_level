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


EV_rural = decompress_pickle('04_ev_load_rural.pbz2')
EV_suburban = decompress_pickle('04_ev_load_suburban.pbz2')
EV_urban = decompress_pickle('04_ev_load_urban.pbz2')

EV = pd.concat([EV_rural, EV_suburban, EV_urban], axis=1)

compress_pickle('04_ev_load.pbz2', EV)
