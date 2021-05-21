import pandas as pd
import numpy as np
import tools
import glob
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

input_folder_rural = '2021-05-19_114212_simbev_run_LR_Klein/'
#input_folder_rural = '2021-04-23_122652_simbev_run_LR_Klein/' # Home 100% -> 11kW
#input_folder_rural = '2021-04-23_151107_simbev_run_LR_Klein/' # Home 52% -> 11kW 
#input_folder_rural = '2021-04-23_153618_simbev_run_LR_Klein/' # Home 34% -> 11kW 
region_rural = 'rural'
file_names_rural = glob.glob(input_folder_rural+'*.csv')

input_folder_suburban = '2021-05-19_114409_simbev_run_SR_Mitte/'
#input_folder_suburban = '2021-04-23_122828_simbev_run_SR_Mitte/' # Home 100% -> 11kW
#input_folder_suburban = '2021-04-23_151213_simbev_run_SR_Mitte/' # Home 52% -> 11kW
#input_folder_suburban = '2021-04-23_153720_simbev_run_SR_Mitte/' # Home 34% -> 11kW
region_suburban = 'suburban'
file_names_suburban = glob.glob(input_folder_suburban+'*.csv')

input_folder_urban = '2021-05-19_114503_simbev_run_SR_Gross/'
#input_folder_urban = '2021-04-23_123019_simbev_run_SR_Gross/' # Home 100% -> 11kW
#input_folder_urban = '2021-04-23_151258_simbev_run_SR_Gross/' # Home 52% -> 11kW
#input_folder_urban = '2021-04-23_153750_simbev_run_SR_Gross/' # Home 34% -> 11kW
region_urban = 'urban'
file_names_urban = glob.glob(input_folder_urban+'*.csv')



df_EV = pd.DataFrame(index=times_year)
df_EV_parking_time = pd.DataFrame(index=times_year)
df_EV_charging_demand = pd.DataFrame(index=times_year)

total_share = pd.DataFrame(data=np.array([[0, 0, 0, 0, 0, 0, 0]]), columns=['0_work', '1_business', '2_school', '3_shopping', '4_private/ridesharing', '5_leisure', '6_home'])
total_share['0_work'] = 0

for file_names, region in zip([file_names_rural, file_names_suburban, file_names_urban], [region_rural, region_suburban, region_urban]):
 i = 0
 for filename in file_names:
  i += 1
  BEV = tools.read_simbev_data(filename)
  EV_year, parking_time, charging_demand = tools.get_BEV_timeseries_home_year_1min(BEV, times, max_charging_capacity = 9.9)
  car_type = BEV.car_type[0]
  bat_cap = BEV.bat_cap[0]
  df_EV['ev_'+str(i)+'_'+str(bat_cap)+'kWh_'+region] = EV_year
  #df_EV_parking_time['ev_'+str(i)+'_'+str(bat_cap)+'kWh_'+region] = parking_time
  #df_EV_charging_demand['ev_'+str(i)+'_'+str(bat_cap)+'kWh_'+region] = charging_demand
  print('create ev_'+str(i)+'_'+str(bat_cap)+'kWh_'+region)
  share = tools.get_share_of_charging_locations(BEV)
  total_share += share
  #break
 #compress_pickle('04_ev_load_'+str(region)+'.pbz2', df_EV)
 #df_EV = pd.DataFrame(index=times_year)
 #break

compress_pickle('04_ev_load.pbz2', df_EV)
#compress_pickle('04_ev_parking_time.pbz2', df_EV_parking_time)
#compress_pickle('04_ev_charging_demand.pbz2', df_EV_charging_demand)

#compress_pickle('total_share.pbz2', total_share)
sum_total = total_share.loc[0].sum()
home_share = total_share['6_home']*100/sum_total

print('Share of home charged energy: %s percent' % home_share.values)
print('Total consumption at home: %s kWh per week' % total_share['6_home'].values)

print('Consumption per year and car at home: ')
print(df_EV.sum()/3600*52)
'''
plt.figure()
plt.plot(df_EV['ev_1_30kWh_rural_charging_demand'])
plt.plot(df_EV['ev_1_30kWh_rural_parking'])
plt.plot(df_EV['ev_1_30kWh_rural'])
plt.show()
'''
