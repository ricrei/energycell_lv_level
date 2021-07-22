import csv
import pandas as pd

import tools.tools as tt


class InputDataHandler():

  def __init__(self):
    #self.adjust_input_dataset(time_scope)
    pass


  ##############################
  ### Adjustment of Datasets ###
  ##############################
  def adjust_input_dataset(self, time_scope):

      def shorted_data(data, start_time, end_time, t_freq):
        data_shorted = data.loc[start_time:end_time]
        data_shorted = data_shorted.resample(t_freq).mean()
        data_shorted = data_shorted.round(4)

        return data_shorted

      def shorted_data_sum(data, start_time, end_time, t_freq):
        data_shorted = data.loc[start_time:end_time]
        data_shorted = data_shorted.resample(t_freq).sum()
        data_shorted = data_shorted.round(4)

        return data_shorted

      self.dates = time_scope['start_time'] + ' ' + time_scope['end_time'] + ' ' + time_scope['t_freq']

      with open('input-files/daterange.csv') as daterange:
         csv_daterange = csv.reader(daterange)
         for row in csv_daterange:
            dates_old = str(row[0])

      dates_old = dates_old.strip('[')
      dates_old = dates_old.strip(']')
      dates_old = dates_old.strip('\'')

      if self.dates != dates_old:
        
        print('Adjust input datasets ...')

        start_time = pd.to_datetime(time_scope['start_time'], format='%Y-%m-%d %H:%M:%S')
        end_time = pd.to_datetime(time_scope['end_time'], format='%Y-%m-%d %H:%M:%S')
        t_freq = time_scope['t_freq']

        p0 = tt.decompress_pickle('input-files/01_p0_load.pbz2')
        q0 = tt.decompress_pickle('input-files/01_q0_load.pbz2')
        pv = tt.decompress_pickle('input-files/02_pv_gen.pbz2')
        hp = tt.decompress_pickle('input-files/03_hp_load.pbz2')
        ev_rural    = tt.decompress_pickle('input-files/04_ev_load_rural.pbz2')
        ev_suburban = tt.decompress_pickle('input-files/04_ev_load_suburban.pbz2')
        ev_urban    = tt.decompress_pickle('input-files/04_ev_load_urban.pbz2')
        ev_rural_charging_demand    = tt.decompress_pickle('input-files/04_ev_charging_demand_rural.pbz2')
        ev_suburban_charging_demand = tt.decompress_pickle('input-files/04_ev_charging_demand_suburban.pbz2')
        ev_urban_charging_demand    = tt.decompress_pickle('input-files/04_ev_charging_demand_urban.pbz2')
        ev_rural_parking_time    = tt.decompress_pickle('input-files/04_ev_parking_time_rural.pbz2')
        ev_suburban_parking_time = tt.decompress_pickle('input-files/04_ev_parking_time_suburban.pbz2')
        ev_urban_parking_time    = tt.decompress_pickle('input-files/04_ev_parking_time_urban.pbz2')
        ta = tt.decompress_pickle('input-files/05_temperature_ambient.pbz2')

        p0_shorted = shorted_data(p0, start_time, end_time, t_freq)
        q0_shorted = shorted_data(q0, start_time, end_time, t_freq)
        pv_shorted = shorted_data(pv, start_time, end_time, t_freq)
        hp_shorted = shorted_data(hp, start_time, end_time, t_freq)

        ev_shorted_rural    = shorted_data(ev_rural, start_time, end_time, t_freq)
        ev_shorted_suburban = shorted_data(ev_suburban, start_time, end_time, t_freq)
        ev_shorted_urban    = shorted_data(ev_urban, start_time, end_time, t_freq)
        ev_shorted_rural_charging_demand    = shorted_data(ev_rural_charging_demand, start_time, end_time, t_freq)
        ev_shorted_suburban_charging_demand = shorted_data(ev_suburban_charging_demand, start_time, end_time, t_freq)
        ev_shorted_urban_charging_demand    = shorted_data(ev_urban_charging_demand, start_time, end_time, t_freq)
        ev_shorted_rural_parking_time    = shorted_data(ev_rural_parking_time, start_time, end_time, t_freq)
        ev_shorted_suburban_parking_time = shorted_data(ev_suburban_parking_time, start_time, end_time, t_freq)
        ev_shorted_urban_parking_time    = shorted_data(ev_urban_parking_time, start_time, end_time, t_freq)


        ta_shorted = shorted_data(ta, start_time, end_time, t_freq)

        time = self.get_time_df(pv_shorted)

        tt.compress_pickle('input-files/10_time_short.pbz2', time)
        tt.compress_pickle('input-files/11_p0_short.pbz2', p0_shorted)
        tt.compress_pickle('input-files/11_q0_short.pbz2', q0_shorted)
        tt.compress_pickle('input-files/12_pv_short.pbz2', pv_shorted)
        tt.compress_pickle('input-files/13_hp_short.pbz2', hp_shorted)
        tt.compress_pickle('input-files/14_ev_short_rural.pbz2', ev_shorted_rural)
        tt.compress_pickle('input-files/14_ev_short_suburban.pbz2', ev_shorted_suburban)
        tt.compress_pickle('input-files/14_ev_short_urban.pbz2', ev_shorted_urban)
        tt.compress_pickle('input-files/14_ev_short_rural_charging_demand.pbz2', ev_shorted_rural_charging_demand)
        tt.compress_pickle('input-files/14_ev_short_suburban_charging_demand.pbz2', ev_shorted_suburban_charging_demand)
        tt.compress_pickle('input-files/14_ev_short_urban_charging_demand.pbz2', ev_shorted_urban_charging_demand)
        tt.compress_pickle('input-files/14_ev_short_rural_parking_time.pbz2', ev_shorted_rural_parking_time)
        tt.compress_pickle('input-files/14_ev_short_suburban_parking_time.pbz2', ev_shorted_suburban_parking_time)
        tt.compress_pickle('input-files/14_ev_short_urban_parking_time.pbz2', ev_shorted_urban_parking_time)
        tt.compress_pickle('input-files/15_temperature_ambient_short.pbz2', ta_shorted)

        f = open('input-files/daterange.csv','w')
        f.write(self.dates)
        f.close()

  def get_time_df(self, df):
        return df.index

  def create_empty_df(self, time_scope):
        # Define timeseries
        self.time_series = tt.decompress_pickle('input-files/10_time_short.pbz2')
        self.time_series = pd.DataFrame(self.time_series)
        self.time_series.index = self.time_series['timestamp']
        # define dataframe for all data
        df = pd.DataFrame(range(0,len(self.time_series)), index=self.time_series)
        df = self.time_series
        df.index.freq = time_scope['t_freq']

        return df

