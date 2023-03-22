#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Nov 09 2022

@authors: ricardo
"""

import os
import sys
import pandas as pd
import matplotlib.pyplot as plt

time_scope_winter_15T = { 'start_time' : '2017-01-03 00:00:00+01:00',
                      'end_time'   : '2017-01-10 00:00:00+01:00',
                      't_freq'     : '15T',
                      'name'       : 'winter'
                    }


time_scope_summer_15T = { 'start_time' : '2017-05-27 00:00:00+02:00',
                      'end_time'   : '2017-06-03 00:00:00+02:00',
                      't_freq'     : '15T',
                      'name'       : 'summer'
                    }

time_scope_autumn_15T = { 'start_time' : '2017-10-20 00:00:00+02:00',
                      'end_time'   : '2017-10-27 00:00:00+02:00',
                      't_freq'     : '15T',
                      'name'       : 'autumn'
                    }

time_scope_spring_15T = { 'start_time' : '2017-03-05 00:00:00+01:00',
                      'end_time'   : '2017-03-12 00:00:00+01:00',
                      't_freq'     : '15T',
                      'name'       : 'spring'
                    }

######################
### Define network ###
net_name = ["kerber_rural_1", #0
            "kerber_rural_2", #1
            "kerber_rural_3", #2
            "kerber_rural_4",  #3
            "kerber_village",  #4
            "kerber_suburb_1", #5
            "kerber_suburb_2",  #6
            "simbench_rural_1", #7
            "simbench_rural_2", #8
            "simbench_rural_3", #9
            "simbench_suburb_4", #10
            "simbench_suburb_5", #11
            "simbench_urban_6",  #12
            "test_net_one_load_branch", #13
            "test_net_n_load_branch"]  #14
######################

def read_data(filename):
    data = pd.read_csv(filename, delimiter = ',', low_memory=False)
    data['timestamp'] = pd.to_datetime(data['timestamp'], utc=True)
    data = data.set_index('timestamp')
    return data

for time in [time_scope_winter_15T, time_scope_summer_15T, time_scope_autumn_15T, time_scope_spring_15T]:
  for scenario in [['A',1,0,1,0,0,0], ['B',1,0,1,0,0,0], ['C',1,0,1,0,0,0]]:
    for net_number in [7, 8, 9, 10, 11]:

      input_dir = os.path.join("./", "output-files/"+''.join(str(num) for num in scenario)+"/"+str(net_name[net_number])+"/"+time['start_time'][0:10]+"_"+time['end_time'][0:10]+"_"+time['t_freq']+"/")

      output_dir = os.path.join("./", "output-files/002_spiceEV_inputdata/")

      power_15T = read_data(input_dir+'power_total_MW.csv')

      df = pd.DataFrame(index=power_15T.index,columns=['res','load','pv'])
      df['load'] = power_15T['load'] + power_15T['hp']
      df['pv'] = power_15T['pv']
      df['res'] = power_15T['load'] + power_15T['hp'] - power_15T['pv']

      df.round(6).to_csv(output_dir + ''.join(str(num) for num in scenario)+"_"+str(net_name[net_number])+'_'+time['name'] + '.csv', header=True, index = True)

print('FINISH')

