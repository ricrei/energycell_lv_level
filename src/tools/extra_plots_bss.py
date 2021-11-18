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

scenarios = [621] #[630,631]
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
'''
fig, ax = plt.subplots(1, 2, figsize=(15,5), sharey=True,  gridspec_kw={'wspace': .05})   
     #ax[i].plot(power[i].index, power[i].pv, lw=.6)

for scenario_i in scenarios:
    for week_shortened_i in week_shortened: 
        #for net_i in net:
            #file = '../output-files/shortened_data/' + str(scenario_i) + '/' + net_i + '/' + week_shortened_i + '/'
            file = '../output-files/shortened_data/' + str(scenario_i) + '/' + 'simbench_rural_2' + '/' + week_shortened_i + '/'
            data = pd.read_csv(file + data_soc, sep=",", decimal=".", header=0)
            #label = 'State of charge in % (' + str(scenario_i) + week_shortened_i + net_i + ')'
            label = 'State of charge in % (' + str(scenario_i) + week_shortened_i + 'simbench_rural_2' + ')'
            #bss_1 = data['0']
            #print(bss_1)
            #num_col = len(data.columns)
            ax.plot(data)
            #data.plot()
'''    
fig, ax = plt.subplots(1, 2, figsize=(20,5), sharey=True,  gridspec_kw={'wspace': .05})     
for scenario_i in scenarios:   
    for i in [0,1]: 
                #fig, ax = plt.subplots()
             
                #for net_i in net:
                        #file = '../output-files/shortened_data/' + str(scenario_i) + '/' + net_i + '/' + week_shortened_i + '/'
                file = '../output-files/shortened_data/' + str(scenario_i) + '/' + 'simbench_rural_2' + '/' + week_shortened[i] + '/'
                data = pd.read_csv(file + data_soc, sep=",", decimal=".", header=0)
                #label = 'State of charge in % (' + str(scenario_i) + week_shortened_i + net_i + ')'
                #ax[0].plot(data, lw=.6)
                #ax[1].plot(data, lw=.6)
                #print(data)
                label = 'State of charge in % (' + str(scenario_i) + week_shortened[i] + 'simbench_rural_2' + ')'
                #bss_1 = data['0']
                #print(bss_1)
                #num_col = len(data.columns)
                ax[i].plot(data)
                
ax[0].set_ylabel('soc')
ax[0].set_xlabel('Summer')
ax[1].set_xlabel('Winter')

'''
  fig, ax = plt.subplots(1, 2, figsize=(15,5), sharey=True,  gridspec_kw={'wspace': .05}) #Tabea
  for i in [0,1]:
    ax[i].fill_between(power[i].index, 0, power[i].pv, alpha=0.7)
    ax[i].plot(power[i].index, power[i].pv, lw=.6)
    ax[i].fill_between(power[i].index, 0, -power[i].ev, alpha=0.7)
    ax[i].plot(power[i].index, -power[i].ev, lw=.6)
    ax[i].fill_between(power[i].index, -power[i].ev, -power[i].load-power[i].ev, alpha=0.7)
    ax[i].plot(power[i].index, -power[i].load-power[i].ev, lw=.6)
    ax[i].fill_between(power[i].index, -power[i].load-power[i].ev, -power[i].hp-power[i].load-power[i].ev, alpha=0.7)
    ax[i].plot(power[i].index, -power[i].hp-power[i].load-power[i].ev, lw=.6)
    power[i] = shorted_data(power[i], '10T')
    ax[i].plot(power[i].index, power[i].pv-power[i].hp-power[i].load-power[i].ev, color='black', lw=1)
    ax[i].set_xticks([k for k in power[i].index if (k.hour == 12) & (k.minute == 0)])
    ax[i].set_xticklabels(['  Day 1', '  Day 2', '  Day 3', '  Day 4', '  Day 5', '  Day 6', '  Day 7'])
    ax[i].set(xlim=(power[i].index[0], power[i].index[-1]), ylim=(-2.000, .500))
    plt.legend(['PV Generation','EV Load','Household Load','HP Load', 'Residual Load'], loc='lower right', shadow=True, markerscale=1.0)

  ax[0].set_ylabel('Power in MW')
  ax[0].set_xlabel('Summer')
  ax[1].set_xlabel('Winter')
'''

'''           
            
for scenario_i in scenarios:
    for week_shortened_i in week_shortened:
        #for net_i in net:
            #file = '../output-files/shortened_data/' + str(scenario_i) + '/' + net_i + '/' + week_shortened_i + '/'
            file = '../output-files/shortened_data/' + str(scenario_i) + '/' + 'simbench_rural_2' + '/' + week_shortened_i + '/'
            data = pd.read_csv(file + data_soc, sep=",", decimal=".", header=0)
            
            ax.plot(data)
            #label = 'State of charge in % (' + str(scenario_i) + week_shortened_i + net_i + ')'
            label = 'State of charge in % (' + str(scenario_i) + week_shortened_i + 'simbench_rural_2' + ')'
            #bss_1 = data['0']
            #print(bss_1)
            #num_col = len(data.columns)
            data.plot()
            

        
'''     

'''
            soc = data
            
            ax.set_xlabel('Time')
            ax.set_ylabel('State of charge in %')
            #plt.legend(grid.component_buses.index)
            plt.show()
'''              
                   
                            
                            
                            
                            
                            