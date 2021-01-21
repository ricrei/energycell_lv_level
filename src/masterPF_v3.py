#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Jul 15 11:08:14 2020

@author: ricardo
"""
import tools.tool_data_analysis as tda
import tools.EnergyCell as ec

# Define all parameters
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

# define timescope and timestepwidth
# TODO: create dict
start_time = '2017-05-17 00:01:00+01:00'
end_time = '2017-05-17 23:59:00+01:00'
t_freq = '10T'
'''
start_time = '2017-05-17 00:00:00+02:00'
end_time = '2017-05-17 23:59:00+02:00'
t_freq = '10T'

start_time = '2017-01-11 00:00:00+01:00'
end_time = '2017-01-11 23:59:00+01:00'
t_freq = 'T'
'''

# Initialize EnergyCell
e = ec.EnergyCell(net_name=net_name[7], set_pv=True, set_ev=True, set_hp=True, start_time=start_time, end_time=end_time, t_freq=t_freq)

# Run powerflow
e.run_pf_timeseries()


################################################
############# ANALISE OUTPUT DATA ##############
################################################

#tda.calculate_relevant_outputdata(e.output_dir, t_freq)
#tda.calculate_net_problems(e.output_dir)
#tda.plot_generation_consumption_as_heat_map(e.output_dir)
#tda.plot_grid_issus_over_power(e.output_dir)
#tda.plot_residualload(e.output_dir)
#tda.plot_colorbar_seaborn(e.output_dir, start_time, end_time)
#tda.plot_input_data()
#tda.plot_net_res(net)
#tda.compare_results_of_different_timesteps()
