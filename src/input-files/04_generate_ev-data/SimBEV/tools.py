import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

def read_simbev_data(file_name):
    data = pd.read_csv(file_name, low_memory=False)
    return data

def get_BEV_timeseries_home_year_1min(BEV, times_year, max_charging_capacity):
  BEV_home = BEV[BEV.location == '6_home']

  EV_year = pd.DataFrame(index=times_year, columns=['ev'])
  EV_year['ev'] = 0

  parking_time = pd.DataFrame(index=times_year, columns=['parking'])
  parking_time['parking'] = 0

  charging_demand = pd.DataFrame(index=times_year, columns=['charging_demand'])
  charging_demand['charging_demand'] = 0

  for index in BEV_home.index:
      chargingdemand = BEV_home.chargingdemand[index]
      for i in range(BEV_home.park_start[index], BEV_home.park_end[index]+1):
        #if i == BEV_home.park_start[index]:
        #  charging_demand.loc[[times_year[i]], ['charging_demand']] = chargingdemand
        if chargingdemand > max_charging_capacity/4:
          EV_year.loc[[times_year[i]], ['ev']] = max_charging_capacity
          chargingdemand -= max_charging_capacity/4
          parking_time.loc[[times_year[i]], ['parking']] = 1
        else:
          EV_year.loc[[times_year[i]], ['ev']] = chargingdemand*4
          parking_time.loc[[times_year[i]], ['parking']] = 1
          chargingdemand = 0
        if i == BEV_home.park_start[index]:
          parking_time.loc[[times_year[i]], ['parking']] = chargingdemand

  # 1 Woche = 672 * 15min
  EV_temp = EV_year.loc[times_year[0]:times_year[2*672-1]]
  EV_year = EV_temp

  parking_time_temp = parking_time.loc[times_year[0]:times_year[2*672-1]]
  parking_time = parking_time_temp

  charging_demand_temp = charging_demand.loc[times_year[0]:times_year[2*672-1]]
  charging_demand = charging_demand_temp

  for k in range(0,26):
    EV_year = EV_year.append(EV_temp, ignore_index=True)
    parking_time = parking_time.append(parking_time_temp, ignore_index=True)
    charging_demand = charging_demand.append(charging_demand_temp, ignore_index=True)

  EV_year = EV_year.iloc[0:len(times_year)]
  parking_time = parking_time.iloc[0:len(times_year)]
  charging_demand = charging_demand.iloc[0:len(times_year)]

  EV_year.index = times_year
  parking_time.index = times_year
  charging_demand.index = times_year

  EV_year = EV_year.resample('T').pad()
  parking_time = parking_time.resample('T').pad()
  charging_demand = charging_demand.resample('T').asfreq().fillna(0)

  return EV_year, parking_time, charging_demand

def get_share_of_charging_locations(BEV):
  share = pd.DataFrame(data=np.array([[0, 0, 0, 0, 0, 0, 0, 0]]), columns=['0_work', '1_business', '2_school', '3_shopping', '4_private/ridesharing', '5_leisure', '6_home', '7_charging_hub'])
  BEV = BEV[BEV.location != 'driving']
  for i in BEV.index:
    share[BEV.location[i]] += BEV.chargingdemand[i]
  return share
