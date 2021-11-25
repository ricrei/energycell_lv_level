#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fr November 25 11:08:14 2021

@authors: ricardo, tabea, paul
"""
import tools.EnergyCell as ec
import tools.evaluation.EvaluationAllCases as EvaAllCases

import multiprocessing as mp
import concurrent.futures

import time

##########################################
### Define timescope and timestepwidth ###
time_scope_winter = { 'start_time' : '2017-01-04 00:00:00+01:00',
                      'end_time'   : '2017-01-11 00:00:00+01:00',
                      't_freq'     : '1T',
                      'name'       : 'winter'
                    }


time_scope_summer = { 'start_time' : '2017-05-26 00:00:00+02:00',
                      'end_time'   : '2017-06-02 00:00:00+02:00',
                      't_freq'     : '1T',
                      'name'       : 'summer'
                    }

time_scope_autumn = { 'start_time' : '2017-10-21 00:00:00+02:00',
                      'end_time'   : '2017-10-28 00:00:00+02:00',
                      't_freq'     : '1T',
                      'name'       : 'autumn'
                    }

time_scope = time_scope
###########################################

#######################
### Define scenario ###
# First digit:
## 1: conventional, 2: full-electrified
## 3: maximum pv-expantion, 4: full-electrified and maximum pv-expansion
## 5: grid extention, 6: battery storage systems
## 7: smart consumers, 8: battery storage systems and smart consumers
# Second digit:
## 0: HP,EV greedy mode, BSS simple mode (only in scenario[0] 1-6)
## 1: Household-oriented feed-in damping (only in scenario[0] 6, 7, 8)
## 2: Grid-oriented feed-in damping (only in scenario[0] 6, 7, 8)
## 3: Grid-oriented feed-in damping (only in scenario[0] 6, 8), Community BSS at LV-Busbar
## 4: Grid-oriented feed-in damping (only in scenario[0] 6, 8), Community BSS in feeder
# Third digit:
## 0: No Curtailment, 1: Curtailed Operation (residualload oriented)
#######################

###########################
### Controller parameter ###
# PV_mod: qu, cos_phi
# PV_cos_phi: 0.9 - 1
control_parameter = {
  'PV_mod' : 'qu',
  'PV_cos_phi' : .9}

############################

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
            "test_net_one_load_branch"]  #13
######################

def run_mp_on_ec(time_scope_i, net_name_i, scenario_i, control_parameter):
        print(' ')
        e = ec.EnergyCell(net_name = net_name[net_name_i],
                          scenario = scenario_i,
                          control_parameter = control_parameter,
                          time_scope = time_scope_i)
        #e.run_pf_timeseries()


if __name__ == '__main__':
  start = time.perf_counter()

  pool = mp.Pool(6)
  time_scope = [time_scope_winter, time_scope_summer, time_scope_autumn]
  net_names = [7]
  scenario = [[6,0,1]]

  with concurrent.futures.ProcessPoolExecutor() as executor:
    results = [executor.submit(run_mp_on_ec, time_scope_i, net_name_i, scenario_i, control_parameter) for time_scope_i in time_scope for net_name_i in net_names for scenario_i in scenario]

  finish = time.perf_counter()

  print(f'Finished in {round(finish-start, 2)} s')


