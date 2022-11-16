#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Nov 09 2022

@authors: ricardo
"""

import os
import pandas as pd
import matplotlib.pyplot as plt

import bz2
import pickle
import _pickle as cPickle

def compress_pickle(title, data):
     '''
     Method to pickle a file and then compress it into a file with extension.

     :param title: string
     :param data:  DataFrame
     '''
     with bz2.BZ2File(title, 'w') as f: 
      cPickle.dump(data, f)
     f.close()

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


def read_data(filename):
    data = pd.read_csv(filename, delimiter = ',', low_memory=False)
    data['timestamp'] = decompress_pickle('XX_inputdata_'+season+'/10_time_short.pbz2')# pd.to_datetime(data['time'], utc=True)
    data = data.set_index('timestamp')
    return data

season = 'autumn'
#df = read_data('paperplanes.csv')
df = read_data('greedy_paperplanes.csv')
region = 'rural'
charging_strategy = 'gre'

batcap_dict = {
  'luxu'   : '110kWh',
  'medi'   : '090kWh',
  'mini'   : '060kWh',
}

i = 1
for c in df.columns:
  if 'bev' not in c:
    df = df.drop(c, axis=1)
  elif 'home' != c[-4:]:
    df = df.drop(c, axis=1)
  else:
    ev_num = str("{:03d}".format(i))
    batcap = batcap_dict[c[4:8]]
    new_c = 'ev_'+ev_num+'_'+batcap+'_'+region
    df = df.rename(columns = {c : new_c})
    #df[new_c] += i # test quatsch
    i += 1

compress_pickle('XX_inputdata_'+season+'/14_ev_load_'+str(region)+'_'+str(season)+'_'+str(charging_strategy)+'.pbz2', df)
