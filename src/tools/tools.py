import os
import csv
import time
import numpy as np
import pandas as pd

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

#####################                
### Read csv-file ###
#####################
def read_data(file):
     data = pd.read_csv(file, low_memory=False)
     data['timestamp'] = pd.to_datetime(data['timestamp'], utc=True)
     data = data.set_index('timestamp')
     data.index = data.index.tz_convert('Europe/Berlin')
     #data = data.drop(['timestamp'], axis=1)
     return data

def shorted_data(self, data, t_freq):
    data_shorted = data.resample(t_freq).mean()
    data_shorted = data_shorted.round(4)
    data_shorted.index = pd.DatetimeIndex(data_shorted.index, tz=None, ambiguous='infer')

    return data_shorted

####################################################
### convert csv file into compressed pickle file ###
####################################################
def csv_2_pickle(file):
      df = read_data(file)
      print(df)
      file = file[0:-4]
      compress_pickle(file, df)

def text1(string):
    CSTART = '\33[1m'
    CEND   = '\33[0m'
    return CSTART + string + CEND

def text2(string):
    CSTART = '\33[39m'
    CEND   = '\33[0m'
    return CSTART + string + CEND

def textbold(string):
    CBOLD = '\33[49;1;49m'
    CEND   = '\33[0m'
    return CBOLD + string + CEND

def textred(string):
    CBOLD = '\33[1;31m'
    CEND   = '\33[0m'
    return CBOLD + string + CEND

def textgreen(string):
    CBOLD = '\33[1;32m'
    CEND   = '\33[0m'
    return CBOLD + string + CEND

####################################################
###         method to print progress bar   # █   ###
####################################################
# The MIT License (MIT)
# Copyright (c) 2016 Vladimir Ignatev
#
# Permission is hereby granted, free of charge, to any person obtaining 
# a copy of this software and associated documentation files (the "Software"), 
# to deal in the Software without restriction, including without limitation 
# the rights to use, copy, modify, merge, publish, distribute, sublicense, 
# and/or sell copies of the Software, and to permit persons to whom the Software 
# is furnished to do so, subject to the following conditions:
# 
# The above copyright notice and this permission notice shall be included 
# in all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, 
# INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR 
# PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE
# FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT
# OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE 
# OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
import sys

def progress(count, total, status=''):
    bar_len = 50
    filled_len = int(round(bar_len * count / float(total)))

    percents = round(100.0 * count / float(total), 1)
    bar = '█' * filled_len + '-' * (bar_len - filled_len)

    sys.stdout.write('\r[%s] %s%s ... %s\r' % (bar, percents, '%', status))
    sys.stdout.flush()  # As suggested by Rom Ruben (see: http://stackoverflow.com/questions/3173320/text-progress-bar-in-the-console/27871113#comment50529068_27871113) https://gist.github.com/vladignatyev/06860ec2040cb497f0f3
# █

####################################################
###                   load data                  ###
####################################################
def get_time_sun(time_scope):
    folder = 'input-files/'

    if 'name' in time_scope.keys():
      if time_scope['name'] in ['summer','winter','autumn','spring']:
        season = time_scope['name']
      else:
        season = None
    else:
      season = None

    if season != None:
      if season == 'summer':
            folder = folder + 'XX_inputdata_summer/'
      elif season == 'winter':
            folder = folder + 'XX_inputdata_winter/'
      elif season == 'autumn':
            folder = folder + 'XX_inputdata_autumn/'
      elif season == 'spring':
            folder = folder + 'XX_inputdata_spring/'
      else:
            raise ValueError('season in time_scope is invailed!') 
    file_sun_set_rise = folder + '16_t_sun_rise_set_transit.pbz2'
    return decompress_pickle(file_sun_set_rise)

def get_amb_temp(time_scope):
    folder = 'input-files/'

    if 'name' in time_scope.keys():
      if time_scope['name'] in ['summer','winter','autumn','spring']:
        season = time_scope['name']
      else:
        season = None
    else:
      season = None

    if season != None:
      if season == 'summer':
            folder = folder + 'XX_inputdata_summer/'
      elif season == 'winter':
            folder = folder + 'XX_inputdata_winter/'
      elif season == 'autumn':
            folder = folder + 'XX_inputdata_autumn/'
      elif season == 'spring':
            folder = folder + 'XX_inputdata_spring/'
      else:
            raise ValueError('season in time_scope is invailed!') 

    file_ambient_temp = folder + '15_temperature_ambient_short.pbz2'
    return decompress_pickle(file_ambient_temp)

