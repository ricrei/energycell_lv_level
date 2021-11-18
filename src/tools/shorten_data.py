#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Oct 13 09:17:40 2021

@author: RL-INSTITUT\tabea.katerbau
"""

# Handle date time conversions between pandas and matplotlib
import pandas as pd
from pandas.plotting import register_matplotlib_converters
register_matplotlib_converters()

scenarios = [610,611] #[630,631]
days = 2
timestep_min = 1
winter_week = '2017-01-02_2017-01-11_1T'
summer_week = '2017-05-24_2017-06-02_1T'
winter_week_shortened = '2017-01-04_2017-01-11_1T'
summer_week_shortened = '2017-05-26_2017-06-02_1T'


week = [winter_week, summer_week]
week_shortened = [winter_week_shortened, summer_week_shortened]

net = ['simbench_rural_1', \
       'simbench_rural_2', \
       'simbench_rural_3', \
       'simbench_suburb_4', \
       'simbench_suburb_5']

output_data = ['losses_active_power_MW.csv', \
               'load_reactive_power_MW.csv', \
               'power_total_MW.csv', \
               'trafo_active_power_MW.csv', \
               'v_pu_ext_grid.csv', \
               'curtailed_power_MW.csv', \
               'pv_reactive_power_MW.csv', \
               'pv_active_power_MW.csv', \
               'ev_soc.csv', \
               'storage_active_power_MW.csv', \
               'storage_state_of_charge_percent.csv', \
               'storage_energy_content_MWh.csv', \
               'res_bus_vm_pu.csv', \
               'res_trafo_load_percent.csv', \
               'trafo_reactive_power_MW.csv', \
               'load_active_power_MW.csv', \
               'res_line_load_percent.csv']
#output_data = ['losses_active_power_MW.csv']
    
timesteps_per_hour = 60/timestep_min
num_rows_del = days * 24 * timesteps_per_hour

for scenario_i in scenarios:
    for week_i in week:
        for net_i in net:
            for output_data_i in output_data:
                file = '../output-files/' + str(scenario_i) + '/' + net_i + '/' + week_i + '/'
                data = pd.read_csv(file + output_data_i, sep=",", decimal=".", header=0)
                data_shortened = data.drop(data[data.index < num_rows_del].index)
                for week_shortened_i in week_shortened:
                    if week_shortened_i == winter_week_shortened and week_i == winter_week:
                        data_shortened.to_csv('../output-files/shortened_data/' \
                                      + str(scenario_i) +'/' + net_i + '/' \
                                      + week_shortened_i + '/' + str(output_data_i), \
                                          sep=',', index = False)
                    elif week_shortened_i == summer_week_shortened and week_i == summer_week:
                        data_shortened.to_csv('../output-files/shortened_data/' \
                                      + str(scenario_i) +'/' + net_i + '/' \
                                      + week_shortened_i + '/' + str(output_data_i), \
                                          sep=',', index = False)

