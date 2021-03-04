#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Jul 15 11:08:14 2020

@author: ricardo
"""
import tools.tool_data_analysis as tda
import tools.EnergyCell as ec

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
            "simbench_urban_6"]  #12

# Define timescope and timestepwidth
time_scope = { 'start_time' : '2017-04-17 00:00:00+01:00',
               'end_time'   : '2017-04-18 00:00:00+01:00',
               't_freq'     : '5T'
             }

time_scope_y = { 'start_time' : '2017-01-01 00:01:00+01:00',
               'end_time'   : '2017-12-31 23:59:00+01:00',
               't_freq'     : 'D'
             }

# Define scenario
# 1: conventional, 2: full-electrified, 3: maximum pv-expantion, 4: full-electrified and maximum pv-expansion
scenario = 4

# Initialize EnergyCell
e = ec.EnergyCell(net_name = net_name[7], scenario = scenario, time_scope = time_scope)

# Run powerflow
e.run_pf_timeseries()


################################################
############# ANALISE OUTPUT DATA ##############
################################################


tda.calculate_relevant_outputdata(e.output_dir, time_scope['t_freq'])
tda.calculate_net_problems(e.output_dir)
tda.plot_generation_consumption_as_heat_map(e.output_dir)
tda.plot_grid_issus_over_power(e.output_dir)
tda.plot_residualload(e.output_dir)
#tda.plot_colorbar_seaborn(e.output_dir, time_scope['start_time'], time_scope['end_time'])
#tda.plot_input_data()
#tda.plot_net_res(e.net)
#tda.compare_results_of_different_timesteps()
