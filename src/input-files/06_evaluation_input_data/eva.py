import os
import csv
import time
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

def shorted_data_energy(data, start_time, end_time, t_freq):
        data_shorted = data.loc[start_time:end_time]
        data_shorted = data_shorted.resample(t_freq).sum()/60
        data_shorted = data_shorted.round(4)

        return data_shorted

def shorted_data_max(data, start_time, end_time, t_freq):
        data_shorted = data.loc[start_time:end_time]
        data_shorted = data_shorted.resample(t_freq).max()
        data_shorted = data_shorted.round(4)

        return data_shorted

load_p_data_file = '../load_p_sorted.csv'
load_q_data_file = '../load_q_sorted.csv'
pv_data_file = '../pv_ac_power.csv'
hp_data_file = '../hp_load.csv'
#ev_data_file = 'input-files/ev_ac_power_test.csv'

p0 = pd.read_csv(load_p_data_file)
q0 = pd.read_csv(load_q_data_file)
pv = pd.read_csv(pv_data_file)
#hp = pd.read_csv(hp_data_file)

start_time = '2017-01-01 00:01:00+01:00'
end_time = '2018-01-01 00:00:00+01:00'
t_freq = 'W'
start_time = pd.to_datetime(start_time, format='%Y-%m-%d %H:%M:%S')
end_time = pd.to_datetime(end_time, format='%Y-%m-%d %H:%M:%S')

####### LOAD ########

s0 = pd.DataFrame()
s0['total'] = (p0['p'+str(0)]**2 + q0['q'+str(0)]**2)**(1/2)
p_total = pd.DataFrame()
p_total = p0['p'+str(0)]

for i in range(1, 74):
     s0['total'] += (p0['p'+str(i)]**2 + q0['q'+str(i)]**2)**(1/2)
     p_total += p0['p'+str(i)]
s0 = s0/1000
p_total = p_total/1000

print('Maximale Scheinleistung in MW')
print(s0.max())
print('Gesamtenergieverbrauch in MWh')
print(p_total.sum()/60)

p_total.index = pd.to_datetime(p0['timestamp'], utc=True)
p_total_week = shorted_data_energy(p_total, start_time, end_time, t_freq)
#p_total_week.index = pd.to_datetime(p_total.index, utc=True)

####### PV ########

pv_orientation = [90, 100, 110, 120, 130, 140, 150, 160, 170, 180, 190, 200, 210, 220, 230, 240, 250, 260]
pv_rate = [10.8, 4.8, 4.4, 4, 4, 4.4, 5.2, 6.3, 6.3, 10.8, 4.9, 4.7, 4.3, 4, 4.3, 5, 5.9, 5.9]

pv = pv.set_index('timestamp')
pv.index = pd.to_datetime(pv.index, utc=True)

pv_sum = pd.DataFrame()
pv_sum['total'] = 0*pv['90']

j = 0
for i in pv_orientation:
  pv[str(i)] = pv[str(i)]*pv_rate[j]/100
  j += 1
  pv_sum['total'] = pv_sum['total'] + pv[str(i)]

pv_sum['total'] = pv_sum['total']/1000

pv_sum.index = pd.to_datetime(pv.index, utc=True)

#pv_shorted_max = shorted_data_max(pv_sum, start_time, end_time, t_freq)
pv_shorted_energy = shorted_data_energy(pv_sum, start_time, end_time, t_freq)
pv_shorted_energy.round(4).to_csv('pv_ac_power_week.csv', mode='w', index=True, index_label='timestamp', header='total')
print('Total pv production in MWh/kW')
print(pv_shorted_energy.sum())

plt.plot(p_total_week/74)
plt.plot(pv_shorted_energy)
plt.show()



