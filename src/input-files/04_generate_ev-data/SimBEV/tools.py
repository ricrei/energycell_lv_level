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

  for k in range(0,52):
    for index in BEV_home.index:
      chargingdemand = BEV_home.chargingdemand[index]
      for i in range(BEV_home.charge_start[index], BEV_home.charge_end[index]+1):
        if chargingdemand > max_charging_capacity/4:
          EV_year.loc[[times_year[i+k*672]], ['ev']] = max_charging_capacity
          chargingdemand -= max_charging_capacity/4
        else:
          EV_year.loc[[times_year[i+k*672]], ['ev']] = chargingdemand*4
          break

  EV_year = EV_year.resample('T').pad()

  return EV_year

def get_share_of_charging_locations(BEV):
  share = pd.DataFrame(data=np.array([[0, 0, 0, 0, 0, 0, 0]]), columns=['0_work', '1_business', '2_school', '3_shopping', '4_private/ridesharing', '5_leisure', '6_home'])
  for i in BEV.index:
    share[BEV.location[i]] += BEV.chargingdemand[i]
  return share
