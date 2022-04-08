#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fr April 01 11:08:14 2022

@authors: ricardo, tabea, paul
"""
import tools.EnergyCell as ec
import tools.evaluation.EvaluationAllCases as EvaAllCases

import time

import multiprocessing as mp
import concurrent.futures

##########################################
### Define timescope and timestepwidth ###
'''
time_scope = { 'start_time' : '2017-06-11 00:00:00+02:00',
               'end_time'   : '2017-06-12 00:00:00+02:00',
               't_freq'     : '10T',
             }
'''
time_scope = { 'start_time' : '2017-05-25 00:00:00+02:00',
               'end_time'   : '2017-05-26 00:00:00+02:00',
               't_freq'     : '10T',
             }

time_scope_year = { 'start_time' : '2017-04-01 00:00:00+01:00',
                    'end_time'   : '2018-08-01 00:00:00+01:00',
                    't_freq'     : '1H'
                  }

# timescopes to examine
time_scope_winter_with_extra_time = { 'start_time' : '2017-01-01 00:00:00+01:00',
                      'end_time'   : '2017-01-10 00:00:00+01:00',
                      't_freq'     : '1T',
                      'name'       : 'winter'
                    }


time_scope_summer_with_extra_time = { 'start_time' : '2017-05-27 00:00:00+02:00',
                      'end_time'   : '2017-06-03 00:00:00+02:00',
                      't_freq'     : '1T',
                      'name'       : 'summer'
                    }

time_scope_winter = { 'start_time' : '2017-01-03 00:00:00+01:00',
                      'end_time'   : '2017-01-10 00:00:00+01:00',
                      't_freq'     : '1T',
                      'name'       : 'winter'
                    }


time_scope_summer = { 'start_time' : '2017-05-27 00:00:00+02:00',
                      'end_time'   : '2017-06-03 00:00:00+02:00',
                      't_freq'     : '1T',
                      'name'       : 'summer'
                    }

time_scope_autumn = { 'start_time' : '2017-10-20 00:00:00+02:00',
                      'end_time'   : '2017-10-27 00:00:00+02:00',
                      't_freq'     : '1T',
                      'name'       : 'autumn'
                    }

time_scope_spring = { 'start_time' : '2017-03-05 00:00:00+01:00',
                      'end_time'   : '2017-03-12 00:00:00+01:00',
                      't_freq'     : '1T',
                      'name'       : 'spring'
                    }

time_scope = time_scope
###########################################

#######################
### Define scenario ###
# First number:
## 1: conventional, 2: full-electrified
## 3: maximum pv-expantion, 4: full-electrified and maximum pv-expansion
## 6: battery storage systems, 7: smart consumers, 8: battery storage systems and smart consumers
# Second number: PV
## 0: no PV, 1: Q(U), 2: fix cos(phi)
# Third number: BSS
## 0: no BSS, 1: direct, 2: Household-oriented feed-in damping, 3: Grid-oriented feed-in damping
## 4: Grid-oriented feed-in damping Community BSS at LV-Busbar,
## 5: Grid-oriented feed-in damping Community BSS in feeder
# Fourth number: HP
## 0: no HP, 1: direct, 2: Household-oriented feed-in damping, 3: Grid-oriented feed-in damping
## 4: evu-lock (EnWG §14a),
## 5: residual-load-driven
# Fifth number: EV
## 0: no EV, 1: direct, 2: Household-oriented feed-in damping, 3: Grid-oriented feed-in damping
# Sixth number: Curtailment
## 0: No Curtailment, 1: Curtailed Operation (residualload oriented)
# Seventh number: Grid Reinforcement
## 0: No Grid Reinforcement, 1: Grid Reinforcement
scenario = [
  7, # scenario number, 1-8
  1, # PV, 0-2
  0, # BSS, 0-5
  1, # HP, 0-5
  1, # EV, 0-3
  1, # Curtailment, 0/1
  0  # Grid reinforcement, 0/1
]
#######################

###########################
### Controller parameter ###
# PV_mod: qu, cos_phi
# PV_cos_phi: 0.9 - 1
control_parameter = {
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
            "test_net_one_load_branch", #13
            "test_net_n_load_branch"]  #14
# define net number
net_number = 10
######################

#############################
### Run Single Simulation ###
def run_single_simulation():

  # Initialize EnergyCell

  e = ec.EnergyCell(net_name = net_name[net_number],
                    scenario = scenario,
                    control_parameter = control_parameter,
                    time_scope = time_scope,
                    save_full_data = True)

  # Run powerflow
  e.run_pf_timeseries()

  # Initialize Evaluation
  e.initiate_evaluation()

  e.eva.calculate_relevant_outputdata()
  #e.eva.calculate_net_problems()

  e.eva.plot_residualload(add_curtail=True, add_losses=False)
  #e.eva.plot_ev_soc()
  #e.eva.plot_generation_consumption_as_heat_map()
  #e.eva.plot_colorbar_seaborn()
  #e.eva.plot_grid_issus_over_power()
  #e.eva.plot_grid_issus_over_time()
  #e.eva.plot_pv_active_power()
  #e.eva.plot_pv_reactive_power()
  #e.eva.plot_hp_soc()
  #e.eva.plot_hp_active_power()
  #e.eva.plot_hp_eva_th()
  #e.eva.plot_bss_active_power()
  #e.eva.plot_soc()
  #e.eva.plot_bss_e_mwh()
  #e.eva.plot_bss_p_mw()
  #e.eva.plot_grid(time_sample='2017-05-27 13:10:00+02:00')#2017-01-06 12:00:00+02:00
  #e.eva.plot_grid_2() # Baustelle

  e.eva.energyflow()

  # calculate max, min and balanced residualload weeks. 2017-01-01_2018-01-01_1D/ only!
  #e.eva.calculate_resi_week()

  # Initialize BSS Sizing
  #e.initiate_BSS_sizing()
  #e.bss_sizing.calculate_storage_sizing()
  #e.bss_sizing.bss_sizing_trafo()
  #e.bss_sizing.bss_sizing_line()
  #e.bss_sizing.bss_sizing_voltage()
  #e.bss_sizing.bss_sizing_pv()
  #e.bss_sizing.bss_sizing_fft()
#############################


###############################
### Run Multiple Simulation ###
def run_multiple_simulations():
  start = time.perf_counter()
  i = 1
  for time_scope_i in [time_scope_winter, time_scope_summer, time_scope_autumn, time_scope_spring]:
    for net_name_i in [7]:
      for scenario_i in [[6,1,1,1,1,1,0]]:
        print(' ')
        print('\33[32m' + 'Durchlauf: ' + str(i) + '\33[0m')
        i += 1
        e = ec.EnergyCell(net_name = net_name[net_name_i],
                          scenario = scenario_i,
                          control_parameter = control_parameter,
                          time_scope = time_scope_i)
        #e.run_pf_timeseries()
        #------------
        #e.initiate_evaluation()
        #e.eva.calculate_relevant_outputdata()
        #e.eva.calculate_net_problems()
        #-------------

  finish = time.perf_counter()

  print(f'Finished in {round(finish-start, 2)} s')
###############################

#######################################################
### Run Multiple Simulation in multiprocessing mode ###
def run_mp_on_ec(time_scope_i, net_name_i, scenario_i, control_parameter):
        e = ec.EnergyCell(net_name = net_name[net_name_i],
                          scenario = scenario_i,
                          control_parameter = control_parameter,
                          time_scope = time_scope_i)
        e.run_pf_timeseries()

def run_multiple_simulations_multiprocessing():
    start = time.perf_counter()

    pool = mp.Pool(6)
    time_scope = [time_scope_winter, time_scope_summer, time_scope_autumn, time_scope_spring]
    net_names = [9]
    scenario = [[4,1,0,1,1,1,0]]

    with concurrent.futures.ProcessPoolExecutor() as executor:
      results = [executor.submit(run_mp_on_ec, time_scope_i, net_name_i, scenario_i, control_parameter) for time_scope_i in time_scope for net_name_i in net_names for scenario_i in scenario]

    finish = time.perf_counter()

    print(f'Finished in {round(finish-start, 2)} s')

#######################################################


####################################
### Run Conversion csv -> pickle ###
def run_output_data_conversion():
  scenarios = [
        #[1,0,0,0,0,0,0],
        #[2,0,0,1,1,0,0], [2,0,0,1,1,1,0],
        #[3,1,0,0,0,0,0], [3,1,0,0,0,1,0],
        #[4,1,0,1,1,0,0], [4,1,0,1,1,1,0],# [4,1,0,1,1,0,1],
        #[6,1,1,1,1,0,0], [6,1,1,1,1,1,0],# [6,1,1,1,1,0,1],
        #[6,1,2,1,1,0,0], [6,1,2,1,1,1,0],# [6,1,2,1,1,0,1],
        #[6,1,3,1,1,0,0], [6,1,3,1,1,1,0],# [6,1,3,1,1,0,1],
        #[6,1,4,1,1,0,0], [6,1,4,1,1,1,0],# [6,1,4,1,1,0,1],
        #[6,1,5,1,1,0,0], [6,1,5,1,1,1,0],# [6,1,5,1,1,0,1],
        #[7,1,0,2,2,0,0], [7,1,0,2,2,1,0],# [7,1,0,2,2,0,1],
        #[7,1,0,3,3,0,0],
        [7,1,0,3,3,1,0],# [7,1,0,3,3,0,1],
        [8,1,3,3,3,0,0], [8,1,3,3,3,1,0],# [8,1,3,3,3,0,1],
                  ]

  evaluation_all = EvaAllCases.EvaluationAllCases(
                                 net_names = [7,8,9,10,11],
                                 scenarios = scenarios,#[[4,1,0,1,1,1,0]],
                                 time_scopes = [time_scope_winter, time_scope_summer, time_scope_autumn, time_scope_spring])

  print('Done')
####################################


#######################
run_single_simulation()
#run_multiple_simulations()
#run_multiple_simulations_multiprocessing()
#run_output_data_conversion()
#######################

