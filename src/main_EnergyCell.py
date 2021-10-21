#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed March 17 11:08:14 2020

@authors: ricardo, tabea, paul
"""
import tools.EnergyCell as ec
import tools.evaluation.EvaluationAllCases as EvaAllCases

##########################################
### Define timescope and timestepwidth ###
time_scope = { 'start_time' : '2017-05-26 00:00:00+02:00', 
               'end_time'   : '2017-05-30 00:00:00+02:00',
               't_freq'     : '1H' 
             } 

time_scope_year = { 'start_time' : '2017-01-01 00:00:00+01:00',
                    'end_time'   : '2018-01-01 00:00:00+01:00',
                    't_freq'     : '1H'
                  }

# timescopes to examine
time_scope_winter_with_extra_time = { 'start_time' : '2017-01-02 00:00:00+01:00',
                      'end_time'   : '2017-01-11 00:00:00+01:00',
                      't_freq'     : '1T',
                      'name'       : 'winter'
                    }


time_scope_summer_with_extra_time = { 'start_time' : '2017-05-24 00:00:00+02:00',
                      'end_time'   : '2017-06-02 00:00:00+02:00',
                      't_freq'     : '1T',
                      'name'       : 'summer'
                    }

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
scenario = [6, 4, 1]
#scenario = [8, 1, 1]
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
# define net number
net_number = 8
######################

#######################
# 0: single simulation
# 1: all scenarios and grids
run_simulation = 0
#######################

#############################
### Run Single Simulation ###
if run_simulation == 0:

  # Initialize EnergyCell
  
  e = ec.EnergyCell(net_name = net_name[net_number],
                    scenario = scenario,
                    control_parameter = control_parameter,
                    time_scope = time_scope)
  
  # Run powerflow
  e.run_pf_timeseries()

  # Initialize Evaluation
  e.initiate_evaluation()

  e.eva.calculate_relevant_outputdata()
  e.eva.calculate_net_problems()

  e.eva.plot_residualload(add_curtail=True, add_losses=True)
  #e.eva.plot_ev_soc()
  #e.eva.plot_generation_consumption_as_heat_map()
  #e.eva.plot_colorbar_seaborn()
  #e.eva.plot_grid_issus_over_power()
  #e.eva.plot_grid_issus_over_time()
  #e.eva.plot_pv_active_power()
  #e.eva.plot_pv_reactive_power()
  #e.eva.plot_bss_active_power()
  e.eva.plot_soc()
  #e.eva.plot_bss_e_mwh()
  e.eva.plot_bss_p_mw()
  #e.eva.plot_grid(time_sample='2017-05-26 12:00:00+02:00')#2017-01-06 12:00:00+02:00
  #e.eva.plot_grid_2() # Baustelle

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
elif run_simulation == 1:

  i = 1
  for time_scope_i in [time_scope_winter_with_extra_time, time_scope_summer_with_extra_time]:
    for net_name_i in [7, 8, 9, 10, 11]: # [7, 8, 9, 10, 11]
      for scenario_i in [ [6,4,0], [6,4,1]]:
        print(' ')
        print('\33[32m' + 'Durchlauf: ' + str(i) + '\33[0m')
        i += 1
        e = ec.EnergyCell(net_name = net_name[net_name_i],
                          scenario = scenario_i,
                          control_parameter = control_parameter,
                          time_scope = time_scope_i)
        e.run_pf_timeseries()
        #------------
        e.initiate_evaluation()
        e.eva.calculate_relevant_outputdata()
        e.eva.calculate_net_problems() # 
        e.eva.plot_soc()
        #e.eva.plot_bss_e_mwh()
        #e.eva.plot_bss_p_mw()
        #e.eva.plot_residualload() 
        e.eva.plot_residualload(add_curtail=True, add_losses=True)#
        #-------------


elif run_simulation == 11:
  scenarios = [640, 641
  ]
  ''' 
  scenarios = [
  100,
  200,
  300,
  400, 401,
  500,
  600, 601, 610, 611, 620, 621,
  710, 711, 720, 721,
  810, 811, 820, 821,
  ]
  '''
  evaluation_all = EvaAllCases.EvaluationAllCases(
                                 net_names = net_name,
                                 scenarios = scenarios,
                                 time_scopes = [time_scope_winter_with_extra_time, time_scope_summer_with_extra_time])

  print('Done')
###############################

