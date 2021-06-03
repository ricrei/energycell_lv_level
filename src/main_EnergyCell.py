#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed March 17 11:08:14 2020

@authors: ricardo, tabea, paul
"""
import tools.EnergyCell as ec
import pandas as pd

# Define all gird names
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
            "test_net_one_load_branch"]  #13

# Define timescope and timestepwidth
time_scope = { 'start_time' : '2017-05-26 00:00:00+02:00',
               'end_time'   : '2017-05-27 00:00:00+02:00',
               't_freq'     : '1H'
             }
'''
time_scope = { 'start_time' : '2017-05-26 14:00:00+02:00',
               'end_time'   : '2017-05-26 14:00:00+02:00',
               't_freq'     : 'H'
             }
'''
# timescopes to examine
time_scope_winter = { 'start_time' : '2017-01-04 00:00:00+01:00',
                      'end_time'   : '2017-01-11 00:00:00+01:00',
                      't_freq'     : 'T',
                      'name'       : 'winter'
                    }


time_scope_summer = { 'start_time' : '2017-05-26 00:00:00+02:00',
                      'end_time'   : '2017-06-02 00:00:00+02:00',
                      't_freq'     : 'T',
                      'name'       : 'summer'
                    }


# Define scenario
# 1: conventional, 2: full-electrified
# 3: maximum pv-expantion, 4: full-electrified and maximum pv-expansion
# 5: grid extention (not implemented), 6: battery storage systems
# 7: smart consumers, 8: battery storage systems and smart consumers
scenario = 6

# Initialize EnergyCell
e = ec.EnergyCell(net_name = net_name[7], scenario = scenario, \
                  time_scope = time_scope)

# Run powerflow
e.run_pf_timeseries()

# Initialize Evaluation
e.initiate_evaluation()

################################################
############# ANALISE OUTPUT DATA ##############
################################################

e.eva.calculate_relevant_outputdata()
e.eva.calculate_net_problems()

e.eva.plot_residualload()
#e.eva.plot_generation_consumption_as_heat_map()
#e.eva.plot_colorbar_seaborn()
#e.eva.plot_grid_issus_over_power()
e.eva.plot_grid_issus_over_time()
#e.eva.plot_pv_reactive_power()
e.eva.plot_soc() # abhängigkeit von grid wegen anzahl busse...ändern

'''
i = 0
CGREEN = '\33[32m'
CEND   = '\33[0m'
for time_scope_i in [time_scope_winter, time_scope_summer]:
  for net_name_i in [7, 8, 9, 10, 11]:
    for scenario_i in [1, 2, 3, 4]:
      print(' ')
      print(CGREEN + 'Durchlauf: ' + str(i) + CEND)
      i += 1
      e = ec.EnergyCell(net_name = net_name[net_name_i],
                        scenario = scenario_i,
                        time_scope = time_scope_i)
      e.run_pf_timeseries()

print('Done')
'''
