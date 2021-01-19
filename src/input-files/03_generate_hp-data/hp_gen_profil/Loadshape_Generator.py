# -*- coding: utf-8 -*-
"""
Created on Thu May 24 13:47:36 2018

@author: Sascha Birk
"""
# In[Determine Runtime]:

import time
#Processingtime in minutes
timer_start = time.time()

# In[set up environment]

import os
import pandas as pd
import matplotlib.pyplot as plt
import heatpump as hp
import random as random

import bz2
#import pickle
import _pickle as cPickle

#####################################################################
### Pickle a file and then compress it into a file with extension ###
#####################################################################
def compress_pickle(title, data):
     with bz2.BZ2File(title, 'w') as f: 
      cPickle.dump(data, f)
     f.close()    


filepath = "./Input_House/Base_Szenario/"

OUTPUT = './Results/'

if not os.path.exists(OUTPUT):
    os.makedirs(OUTPUT)
    
# In[Determine scenario parameters]:
    
#number_of_buses = 10
#df_htw = pd.read_csv(filepath + 'df_S_15min.csv') #74 baseloadprofiles from HTW Berlin in Watt. Named 0-73

start = '2017-01-01 00:00:00'
end = '2018-01-01 00:00:00'

df = hp.new_scenario(start=start, end=end, periods = None, freq = "1 min", column = 'hp_demand')

# In[Input Heatpump]:

SigLinDe = pd.read_csv("./Input_House/heatpump_model/SigLinDe.csv", decimal=",")
building_type = ['DE_HEF33', 'DE_HEF34', 'DE_HMF33', 'DE_HMF34']

def read_weather_data(file_name, error_replacement_value, times):
    data = pd.read_csv(file_name, header=16, low_memory=False)
    data = data.drop([0, 1]).reset_index().drop(columns='index')
    #data['TIMESTAMP'] = pd.to_datetime(data['TIMESTAMP'], format="%Y-%m-%d %H:%M:%S")
    data['TIMESTAMP'] = times
    col_name = list(data)
    data[col_name[1]] = pd.to_numeric(data[col_name[1]])
    data.loc[data[col_name[1]] == -999.000, col_name[1]] = error_replacement_value
    data = data.set_index('TIMESTAMP')
    return data

# define timezone
tz = 'Europe/Berlin'

# Date and Time range should match with the weather data timestemp
times = pd.date_range(start='2017-01-01 00:00:00', end='2017-12-31 23:59:00', freq='1min', tz=tz)

t_a = read_weather_data('./Input_House/heatpump_model/UCON_TUB_Main_Building_minute_lev2_ta_56.00m_20170101-20180101.csv', 20, times)
#t_a.ta = t_a.ta + 10
#print(t_a.ta.max())
#print(t_a.ta.min())
#print(t_a.ta.mean())
#plt.hist(t_a.ta, bins = 100)
#plt.show()

def shorted_data(data, start_time, end_time, t_freq):
    data_shorted = data.loc[start_time:end_time]
    data_shorted = data_shorted.resample(t_freq).mean()
    data_shorted = data_shorted.round(4)

    return data_shorted

start_time = pd.to_datetime('2017-01-01 00:00:00', format='%Y-%m-%d %H:%M:%S')
end_time = pd.to_datetime('2017-12-31 23:59:00', format='%Y-%m-%d %H:%M:%S')

demand_daily = pd.read_csv('./Input_House/heatpump_model/demand_daily.csv')

'''
mean_temp_hours = pd.read_csv('./Input_House/heatpump_model/mean_temp_hours_2017.csv', header = None)
mean_temp_days = pd.DataFrame(pd.date_range("2017-01-01","2017-12-31",freq="D", name = 'Time'))
mean_temp_days['Mean_Temp'] = pd.read_csv("./Input_House/heatpump_model/mean_temp_days_2017.csv", header = None)
'''
mean_temp_hours = shorted_data(t_a, start_time, end_time, t_freq = 'H')
mean_temp_hours = mean_temp_hours.reset_index()
mean_temp_days = shorted_data(t_a, start_time, end_time, t_freq = 'D')
mean_temp_days['Mean_Temp'] = mean_temp_days['ta']
mean_temp_days = mean_temp_days.reset_index()
#print(mean_temp_hours.mean())
#print(mean_temp_days.mean())

#Hours of usage per year. According to BDEW multi family homes: 2000, single family homes: 2100
hours_year = [2000, 2100]
heatpump_power = 5 #power in kW
heatpump_type = ['Air', 'Ground']#"Air" or "Ground"
#Reference temperature for SigLinDe funktion
t_0 = 40 #°C
water_temp = 60

times = pd.date_range(start='2017-01-01 00:01:00', end='2018', freq='1T', tz='Europe/Berlin')

df = pd.DataFrame(index=times)

for b_type in building_type:
  if b_type == 'DE_HEF33' or b_type == 'DE_HEF34':
    h_year = hours_year[1]
  elif b_type == 'DE_HMF33' or b_type == 'DE_HMF34':
    h_year = hours_year[0]
  else:
    print('Error: no building_type defined.')
  for hp_type in heatpump_type:
    demand =  hp.hp_loadshape(b_type, SigLinDe, mean_temp_days, t_0, demand_daily, mean_temp_hours, hp_type, water_temp, h_year, heatpump_power, df)
    demand.index = times  
    df['Demand_th_' + b_type + '_' + hp_type] = demand['Demand_th']
    df['Demand_el_' + b_type + '_' + hp_type] = demand['Demand_el']
    print(' ')
    print(b_type + '_' + hp_type)
    print('Heat demand: ' + str(demand.Demand_th.sum()/60000) + ' MWh')
    print('Electricity demand: ' + str(demand.Demand_el.sum()/60000) + ' MWh')


# In[Include hp loadshape]:            
#demand =  hp.hp_loadshape(building_type, SigLinDe, mean_temp_days, t_0, demand_daily, mean_temp_hours, heatpump_type, water_temp, hours_year, heatpump_power, df)

print(df)
df = df.round(3)
print(df)

compress_pickle(OUTPUT + '/03_hp_load.pbz2', df)

#Processingtime in minutes
timer_end = time.time()
print('Runtime ' + str(round((timer_end-timer_start), 2)) + ' Seconds')

#plt.plot(range(len(mean_temp_hours)), mean_temp_hours)
#plt.plot(range(0, len(mean_temp_hours), 24), mean_temp_days['Mean_Temp'])
#plt.plot(demand)
#plt.legend(['Demand electrical','Demand thermal'])
#plt.ylabel('Power in kW')
#plt.xlabel('Time')
#plt.show()
