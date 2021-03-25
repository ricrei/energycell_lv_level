import pandas as pd
import numpy as np
import tools
import matplotlib.pyplot as plt
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

# define timezone
tz = 'Europe/Berlin'

# Date and Time range should match with the weather data timestemp
times = pd.date_range(start='2017-01-01 00:00:00', end='2018-01-01 00:00:00', freq='15min', tz=tz)
times_year = pd.date_range(start='2017-01-01 00:01:00', end='2018-01-01 00:00:00', freq='1min', tz=tz)

input_folder = 'SimBEV-Data/test/'

file_names = [
#input_folder+'BEV_luxury_00001_standing_times.csv',
#input_folder+'BEV_luxury_00003_standing_times.csv', #100
#input_folder+'BEV_luxury_00004_standing_times.csv',
input_folder+'BEV_luxury_00005_standing_times.csv', #100
#input_folder+'BEV_luxury_00006_standing_times.csv',
#input_folder+'BEV_luxury_00008_standing_times.csv',
#input_folder+'BEV_luxury_00009_standing_times.csv',
#input_folder+'BEV_luxury_00010_standing_times.csv',
#input_folder+'BEV_luxury_00011_standing_times.csv',
#input_folder+'BEV_luxury_00012_standing_times.csv',
#input_folder+'BEV_medium_00000_standing_times.csv',
#input_folder+'BEV_medium_00001_standing_times.csv',
#input_folder+'BEV_medium_00005_standing_times.csv',
#input_folder+'BEV_medium_00006_standing_times.csv',
#input_folder+'BEV_medium_00007_standing_times.csv',
#input_folder+'BEV_medium_00008_standing_times.csv',
#input_folder+'BEV_medium_00009_standing_times.csv',
#input_folder+'BEV_medium_00010_standing_times.csv',
#input_folder+'BEV_medium_00011_standing_times.csv',
#input_folder+'BEV_medium_00012_standing_times.csv',
#input_folder+'BEV_mini_00001_standing_times.csv',
#input_folder+'BEV_mini_00003_standing_times.csv',
#input_folder+'BEV_mini_00004_standing_times.csv',
#input_folder+'BEV_mini_00006_standing_times.csv',
#input_folder+'BEV_mini_00007_standing_times.csv',
#input_folder+'BEV_mini_00008_standing_times.csv',
#input_folder+'BEV_mini_00009_standing_times.csv',
#input_folder+'BEV_mini_00010_standing_times.csv',
#input_folder+'BEV_mini_00011_standing_times.csv',
#input_folder+'BEV_mini_00013_standing_times.csv',
]

df_EV = pd.DataFrame(index=times_year)

total_share = pd.DataFrame(data=np.array([[0, 0, 0, 0, 0, 0, 0]]), columns=['0_work', '1_business', '2_school', '3_shopping', '4_private/ridesharing', '5_leisure', '6_home'])
total_share['0_work'] = 0
i = 0

for filename in file_names:
  i += 1
  BEV = tools.read_simbev_data(filename)
  EV_year = tools.get_BEV_timeseries_home_year_1min(BEV, times, max_charging_capacity = 9.9)
  car_type = BEV.car_type[0]
  bat_cap = BEV.bat_cap[0]
  df_EV['ev_'+str(i)+'_'+str(bat_cap)] = EV_year
  print('create ev_'+str(i)+'_'+str(bat_cap))
  share = tools.get_share_of_charging_locations(BEV)
  total_share += share

sum_total = total_share.loc[0].sum()
home_share = total_share['6_home']*100/sum_total

print('Share of home charged energy: %s percent' % home_share.values)
print('Total consumption at home: %s kWh per week' % total_share['6_home'].values)

print('Consumption per year and car at home: ')
print(df_EV.sum()/3600*52)

#df_EV.to_csv('04_ev_load.csv', mode='w', index=True, index_label='timestamp')
#compress_pickle('04_ev_load.pbz2', df_EV)
#print(df_EV)


EV = pd.DataFrame(index=times, columns=['0_work', '1_business', '2', '3_shopping', '4_private/ridesharing', '5_leisure', '6_home'])
EV = EV.fillna(0)

for index in BEV.index:
  #print(index)
  for i in range(BEV.charge_start[index], BEV.charge_end[index]):
    EV.loc[[times[i]], BEV.location[index]] += 1

plt.figure()
plt.plot(EV)
plt.legend(['0_work', '1', '2', '3_shopping', '4_private/ridesharing', '5_leisure', '6_home'])
plt.show()
