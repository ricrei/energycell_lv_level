#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu May 31 2022

@authors: ricardo, tabea, paul
"""
import sys
import tools.EnergyCell as ec
import tools.evaluation.EvaluationAllCases as EvaAllCases
import tools.economics.Economics as Economics

import time

import multiprocessing as mp
import concurrent.futures

##########################################
### Define timescope and timestepwidth ###

## T ~ minutes
## H ~ hours

time_scope = { 'start_time' : '2017-01-05 00:00:00+01:00',
               'end_time'   : '2017-01-07 00:00:00+01:00',
               't_freq'     : '15T',
             }

'''
time_scope_year = { 'start_time' : '2017-01-01 00:00:00+01:00',
                    'end_time'   : '2017-12-31 23:59:00+01:00',
                    't_freq'     : '1T'
                  }

time_scope_year = { 'start_time' : '2017-01-01 00:00:00+00:00',
                    'end_time'   : '2017-06-30 23:59:00+00:00',
                    't_freq'     : '1T'
                  }
'''
# timescopes to examine

time_scope_winter = { 'start_time' : '2017-01-03 00:00:00+01:00',
                      'end_time'   : '2017-01-10 00:00:00+01:00',
                      't_freq'     : '15T',
                      'name'       : 'winter'
                    }

time_scope_summer = { 'start_time' : '2017-05-27 00:00:00+02:00',
                      'end_time'   : '2017-06-03 00:00:00+02:00',
                      't_freq'     : '15T',
                      'name'       : 'summer'
                    }

time_scope_autumn = { 'start_time' : '2017-10-20 00:00:00+02:00',
                      'end_time'   : '2017-10-27 00:00:00+02:00',
                      't_freq'     : '15T',
                      'name'       : 'autumn'
                    }

time_scope_spring = { 'start_time' : '2017-03-05 00:00:00+01:00',
                      'end_time'   : '2017-03-12 00:00:00+01:00',
                      't_freq'     : '15T',
                      'name'       : 'spring'
                    }

time_scope_all_seasons = [
                      time_scope_spring,
                      time_scope_summer,
                      time_scope_autumn,
                      time_scope_winter
                      ]

# Seasons long
'''
time_scope_winter = { 'start_time' : '2017-01-01 00:00:00+01:00',
                      'end_time'   : '2017-03-31 00:00:00+01:00',
                      't_freq'     : '15T',
                      'name'       : 'winter'
                    }


time_scope_summer = { 'start_time' : '2017-07-01 00:00:00+02:00',
                      'end_time'   : '2017-09-30 00:00:00+02:00',
                      't_freq'     : '15T',
                      'name'       : 'summer'
                    }

time_scope_autumn = { 'start_time' : '2017-10-01 00:00:00+02:00',
                      'end_time'   : '2017-12-31 00:00:00+02:00',
                      't_freq'     : '15T',
                      'name'       : 'autumn'
                    }

time_scope_spring = { 'start_time' : '2017-04-01 00:00:00+01:00',
                      'end_time'   : '2017-06-30 00:00:00+01:00',
                      't_freq'     : '15T',
                      'name'       : 'spring'
                    }

time_scope_all_seasons = [
                      time_scope_spring,
                      time_scope_summer,
                      time_scope_autumn,
                      time_scope_winter
                      ]
'''

#time_scope = time_scope
time_scope = time_scope_spring
#time_scope = time_scope_all_seasons
###########################################

#######################
### Define scenario ###
# First number:
## 1: conventional, 2: full-electrified
## 3: maximum pv-expantion, 4: full-electrified and maximum pv-expansion
## 6: battery storage systems, 7: smart consumers, 8: battery storage systems and smart consumers
## A: SFH15, B: SFH45, C: SFH100
# Second number: PV
## 0: no PV, 1: Q(U), 2: fix cos(phi)
# Third number: BSS
## 0: no BSS, 1: direct, 2: Household-oriented feed-in damping, 3: Grid-oriented feed-in damping
## 4: Grid-oriented feed-in damping Community BSS at LV-Busbar,
## 5: Grid-oriented feed-in damping Community BSS in feeder
# Fourth number: HP
## 0: no HP, 1: direct
## Resiload  + 2: noBC_TES1, 3: noBC_TES2, 4: BC_TES1, 5: BC_TES2
## LinCh_FID + 6: noBC_TES1, 7: noBC_TES2, 8: BC_TES1, 9: BC_TES2
# Fifth number: EV
## 0: no EV, 1: direct, 2: Household-oriented feed-in damping, 3: Grid-oriented feed-in damping
# Sixth number: Curtailment
## 0: No Curtailment, 1: Curtailed Operation (residualload oriented)
# Seventh number: Grid Reinforcement
## 0: No Grid Reinforcement, 1: Grid Reinforcement
scenario = [
  'C', # scenario number, 1-8
  1, # PV, 0-2
  0, # BSS, 0-5
  9, # HP, 0-5
  0, # EV, 0-3
  1, # Curtailment, 0/1
  0  # Grid reinforcement, 0/1
]
#######################

###########################
### Controller parameter ###
control_parameter = {
  'PV_cos_phi' : .9,
  'BSS_efficiency_AC2Bat' : 0.953,
  'BSS_efficiency_Bat2AC' : 0.955,
  'BSS_efficiency_storage' : 0.959,
  'BSS_start_soc_percent_winter' : 25,
  'BSS_start_soc_percent_summer' : 75,
  'BSS_start_soc_percent'        : 50,
  'BSS_sizing_factor_power_to_capacity' : .75,
  'BSS_sizing_factor_bss_to_pv' : .75,
  'BSS_soc_reserve_percent_winter' : 20,
  'EV_usable_c_bat' : 100,
  'EV_start_soc' : 100,
  'EV_charging_power' : .011,     # in MW
  'EV_charging_efficiency' : .9,  # 0-1
  'EV_direct_charge_limit' : 80,  # in %
  'EV_linear_charge_limit' : 90,
  'EV_linear_charge_limit_summer' : 80,
  'HP_cos_phi' : 1,
  'HP_t_sink' : 45,     #default sink-temprature
  'HP_t_ground_source' : 8,
  'HP_max_p_kw': 0.0148, # in MW
  'HP_dp_SFH15_p_kw': 0.0032, # in MW thermal power design point
  'HP_dp_SFH45_p_kw': 0.0059, # in MW thermal power design point
  'HP_dp_SFH100_p_kw': 0.0114, # in MW thermal power design point
  'HP_max_p_oversizing': 1.3, # in MW
  'HP_TES_max_capacity_def_mwh' : .0325, #any kind of default
  'HP_building_capacity_mwh' : .014,
  'HP_TES_start_soc' : .5, # 0-1
  'HP_TES_start_soc_winter' : 0.25, # 0-1
  'HP_TES_start_soc_summer' : 0.75, # 0-1
  'HP_TES_loss_per_s' : 0.04 / 86400,   #4% per day / 86400
  'HP_upper_TES_reserve': 1., # default = 1
  'HP_lower_TES_reserve': 0.05, # default = 0 
  'HP_upper_TES_reserve_summer': .5, # default = 1
  'HP_lower_TES_reserve_winter': .35, # default = 0
}
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
net_number = 8
######################

#############################
### Run Single Simulation ###
def run_single_simulation():

  # Initialize EnergyCell

  e = ec.EnergyCell(net_name = net_name[net_number],
                    scenario = scenario,
                    control_parameter = control_parameter,
                    time_scope = time_scope,
                    save_full_data = True, 		 	# default: False
                    verbose = True,        		 		# default: False
                    grid_reinforce_dev_mode = False) 	# default: False

  # Run powerflow
  e.run_pf_timeseries()

  # Initialize Evaluation
  e.initiate_evaluation()

  e.eva.calculate_relevant_outputdata()
  #e.eva.calculate_net_problems()

  ##calc values for pauls issues
  e.eva.calc_hp_values()

  e.eva.plot_residualload(add_curtail=True, add_losses=False)
  #e.eva.plot_ev_soc()
  #e.eva.plot_generation_consumption_as_heat_map()
  #e.eva.plot_colorbar_seaborn()
  #e.eva.plot_grid_issus_over_power()
  #e.eva.plot_grid_issus_over_time()
  #e.eva.plot_pv_active_power()
  #e.eva.plot_pv_reactive_power()
  e.eva.plot_hp_soc()
  e.eva.plot_hp_cop()
  e.eva.plot_hp_active_power()
  e.eva.plot_hp_eva_th()
  #e.eva.plot_bss_active_power()
  #e.eva.plot_soc()
  #e.eva.plot_bss_e_mwh()
  #e.eva.plot_bss_p_mw()
  #e.eva.plot_curtailed_power()
  #e.eva.plot_flex_power()
  #e.eva.plot_grid(time_sample='2017-01-06 12:00:00+01:00')#2017-01-06 12:00:00+02:00
  #e.eva.plot_grid_2() # Baustelle

  #e.eva.energyflow_on_HH_level() # ??? Ist das nicht bereits ausgelagert?

  #e.eva.plot_test()

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
def run_multiple_simulations(scenarios):
  start = time.perf_counter()
  i = 1
  for time_scope_i in [time_scope_winter, time_scope_summer, \
  	time_scope_autumn, time_scope_spring]:
  #for time_scope_i in [time_scope_spring]:
    for net_name_i in [8]:
      for scenario_i in scenarios:
        print(' ')
        print('\33[32m' + 'Durchlauf: ' + str(i) + '\33[0m')
        i += 1
        e = ec.EnergyCell(net_name = net_name[net_name_i],
                          scenario = scenario_i,
                          control_parameter = control_parameter,
                          time_scope = time_scope_i,
                          save_full_data = True,  # default: False
                          verbose = False)        # default: False)
        e.run_pf_timeseries()
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
                          time_scope = time_scope_i,
                          save_full_data = False)
        e.run_pf_timeseries()

def run_multiple_simulations_multiprocessing(scenarios):
    start = time.perf_counter()

    pool = mp.Pool(6)
    time_scope = [time_scope_winter, time_scope_autumn, time_scope_spring, time_scope_summer]
    net_names = [7, 8, 9, 10, 11]

    with concurrent.futures.ProcessPoolExecutor() as executor:
      results = [executor.submit(run_mp_on_ec, time_scope_i, net_name_i, scenario_i, control_parameter) for scenario_i in scenarios for time_scope_i in time_scope for net_name_i in net_names]

    finish = time.perf_counter()

    print(f'Finished in {round(finish-start, 2)} s')

#######################################################

####################################
### Run Conversion csv -> pickle ###
def run_output_data_conversion(scenarios):

  evaluation_all = EvaAllCases.EvaluationAllCases(
                                 #net_names = [7, 8, 9, 10, 11],
                                 net_names = [8],
                                 scenarios = scenarios,#[[4,1,0,1,1,1,0]],
                                 time_scopes = [time_scope_winter, time_scope_summer, time_scope_autumn, time_scope_spring])
                                 #time_scopes = [time_scope_spring])

  print('Done')
####################################

#####################
### Run Economics ###
def run_economics(scenarios):
    for scenario_i in scenarios:
      for net_name_i in [7, 8, 9, 10, 11]:
        #print(' ')
        print('\33[32m' + 'Durchlauf: ' + str(scenario_i) + ' ' + str(net_name[net_name_i]) + '\33[0m')
        e_eco = Economics.MainEconomics(scenario_i, net_name[net_name_i], time_scope_all_seasons)
        #e_eco.calculate_relevant_outputdata()
        e_eco.energyflow()

        ### determine annuity of investmentcosts (01)
        e_eco.determine_annuity_investments(include_grid_reinforce = True)

        ### determine operational expanses (02)
        e_eco.determine_operational_expanses()

        ### determine Costs and Revenues of Energyflows (03)
        e_eco.determine_local_energy_trading_price()
        e_eco.determine_grid_charges()
        e_eco.determine_energy_costs_revenues()

        # concate (01) - (03) in one table
        e_eco.write_to_conclusion_table()

        #e_eco.plot_costs_revenues_per_HH()



  # [4,1,0,1,1,1,0] Basis mit Abregelung							-
  # [4,1,0,1,1,0,1] Basis mit Netzausbau							-			
  # [8,1,3,3,3,1,0] Heimspeicher + flexible verbraucher				-
  # [8,1,5,3,3,1,0] Communityspeicher + flexible verbraucher		-
  # [8,1,3,3,3,1,1] moderater Netzausbau							Netzausbau implementieren / alles muss durchlaufen
  
#####################

#######################
scenarios = [
        ##SFH15
        ['A',0,0,2,0,1,0],
        ['A',1,0,2,0,1,0],
        ['A',3,0,2,0,1,0],
        ['A',0,0,3,0,1,0],
        ['A',1,0,3,0,1,0],
        ['A',3,0,3,0,1,0],
        ['A',0,0,4,0,1,0],
        ['A',1,0,4,0,1,0],
        ['A',3,0,4,0,1,0],
        ['A',0,0,5,0,1,0],
        ['A',1,0,5,0,1,0],
        ['A',3,0,5,0,1,0],      
        ['A',0,0,6,0,1,0],
        ['A',1,0,6,0,1,0],
        ['A',3,0,6,0,1,0],
        ['A',0,0,7,0,1,0],
        ['A',1,0,7,0,1,0],
        ['A',3,0,7,0,1,0],
        ['A',0,0,8,0,1,0],
        ['A',1,0,8,0,1,0],
        ['A',3,0,8,0,1,0],
        ['A',0,0,9,0,1,0],
        ['A',1,0,9,0,1,0],
        ['A',3,0,9,0,1,0],
        ##SFH45
        ['B',0,0,2,0,1,0],
        ['B',1,0,2,0,1,0],
        ['B',3,0,2,0,1,0],
        ['B',0,0,3,0,1,0],
        ['B',1,0,3,0,1,0],
        ['B',3,0,3,0,1,0],
        ['B',0,0,4,0,1,0],
        ['B',1,0,4,0,1,0],
        ['B',3,0,4,0,1,0],
        ['B',0,0,5,0,1,0],
        ['B',1,0,5,0,1,0],
        ['B',3,0,5,0,1,0],        
        ['B',0,0,6,0,1,0],
        ['B',1,0,6,0,1,0],
        ['B',3,0,6,0,1,0],
        ['B',0,0,7,0,1,0],
        ['B',1,0,7,0,1,0],
        ['B',3,0,7,0,1,0],
        ['B',0,0,8,0,1,0],
        ['B',1,0,8,0,1,0],
        ['B',3,0,8,0,1,0],
        ['B',0,0,9,0,1,0],
        ['B',1,0,9,0,1,0],
        ['B',3,0,9,0,1,0],
        ##SFH100
        ['C',0,0,2,0,1,0],
        ['C',1,0,2,0,1,0],
        ['C',3,0,2,0,1,0],
        ['C',0,0,3,0,1,0],
        ['C',1,0,3,0,1,0],
        ['C',3,0,3,0,1,0],
        ['C',0,0,4,0,1,0],
        ['C',1,0,4,0,1,0],
        ['C',3,0,4,0,1,0],
        ['C',0,0,5,0,1,0],
        ['C',1,0,5,0,1,0],
        ['C',3,0,5,0,1,0],
        ['C',0,0,6,0,1,0],
        ['C',1,0,6,0,1,0],
        ['C',3,0,6,0,1,0],
        ['C',0,0,7,0,1,0],
        ['C',1,0,7,0,1,0],
        ['C',3,0,7,0,1,0],
        ['C',0,0,8,0,1,0],
        ['C',1,0,8,0,1,0],
        ['C',3,0,8,0,1,0],
        ['C',0,0,9,0,1,0],
        ['C',1,0,9,0,1,0],
        ['C',3,0,9,0,1,0],
            ]

run_single_simulation()
#run_multiple_simulations(scenarios)
#run_multiple_simulations_multiprocessing(scenarios)
#run_output_data_conversion(scenarios)
#run_economics(scenarios)
#######################
