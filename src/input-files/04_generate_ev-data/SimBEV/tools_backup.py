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

  # 1 Woche = 672 * 15min

  for k in range(0,26):# Für Datensatz mit 14 Tagen -> 26, 7 Tagen -> 52 
    for index in BEV_home.index:
      chargingdemand = BEV_home.chargingdemand[index]
      for i in range(BEV_home.park_start[index], BEV_home.park_end[index]+1):
        if i == BEV_home.park_start[index]:
          charging_demand.loc[[times_year[i+k*2*672]], ['charging_demand']] = chargingdemand
        if chargingdemand > max_charging_capacity/4:
          EV_year.loc[[times_year[i+k*2*672]], ['ev']] = max_charging_capacity
          chargingdemand -= max_charging_capacity/4
          parking_time.loc[[times_year[i+k*2*672]], ['parking']] = 1
        else:
          EV_year.loc[[times_year[i+k*2*672]], ['ev']] = chargingdemand*4
          parking_time.loc[[times_year[i+k*2*672]], ['parking']] = 1
          #chargingdemand = 0
          parking_time.loc[[times_year[BEV_home.park_end[index]+1+k*2*672]], ['parking']] = -1
          break

  p = parking_time['parking'].iloc[0]
  for i in parking_time.index:
    if parking_time['parking'].loc[i] != -1:
      if p == 1:
        parking_time['parking'].loc[i] == 1
      if p == 0:
        if parking_time['parking'].loc[i] == 1:
          p == 1
        else:
          parking_time['parking'].loc[i] == 0
    else:
      p = 0
      parking_time['parking'].loc[i] = 1

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
