#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Oct 18 22:28:15 2021

@author: RL-INSTITUT\tabea.katerbau
"""

# Handle date time conversions between pandas and matplotlib
import pandas as pd
import matplotlib.pyplot as plt
from pandas.plotting import register_matplotlib_converters
register_matplotlib_converters()

scenarios = [640] #[630,631]
days = 2
timestep_min = 1
#winter_week = '2017-01-02_2017-01-11_1T'
#summer_week = '2017-05-24_2017-06-02_1T'
winter_week_shortened = '2017-01-04_2017-01-11_1T'
summer_week_shortened = '2017-05-26_2017-06-02_1T'


#week = [winter_week, summer_week]
week_shortened = [winter_week_shortened, summer_week_shortened]

net = ['simbench_rural_1', \
       'simbench_rural_2', \
       'simbench_rural_3', \
       'simbench_suburb_4', \
       'simbench_suburb_5']
    
data_soc = 'storage_state_of_charge_percent.csv'
'''  
def plot_soc(self):
    #busses_num = len(grid.component_buses.index)
    #array_bus = np.arange(busses_num)
    soc = self.storage_soc
    fig, ax = plt.subplots()
    ax.plot(soc.index, soc)
    ax.set_xlabel('Time')
    ax.set_ylabel('State of charge in %')
    #plt.legend(grid.component_buses.index)
    plt.show()
'''
    
for scenario_i in scenarios:
    for week_shortened_i in week_shortened:
        for net_i in net:
            file = '../output-files/shortened_data/' + str(scenario_i) + '/' + net_i + '/' + week_shortened_i + '/'
            data = pd.read_csv(file + data_soc, sep=",", decimal=".", header=0)
            label = 'State of charge in % (' + str(scenario_i) + week_shortened_i + net_i + ')'
            #bss_1 = data['0']
            #print(bss_1)
            #num_col = len(data.columns)
            data.plot()
            '''
            soc = data
            fig, ax = plt.subplots()
            ax.plot(soc.index, soc)
            ax.set_xlabel('Time')
            ax.set_ylabel('State of charge in %')
            #plt.legend(grid.component_buses.index)
            plt.show()
            '''
                
                   
                            
                            
                            
                            
                            