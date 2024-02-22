import csv
import pandas as pd
import sys

import tools.tools as tt


class InputDataHandler():

  def __init__(self, time_scope, scenario):
    self.scenario = scenario
    self.folder = 'input-files/'
    self.inputfolder = self.folder
    if 'name' in time_scope.keys():
      if time_scope['name'] in ['summer','winter','autumn','spring']:
        self.season = time_scope['name']
      else:
        self.season = None
    else:
      self.season = None

  ##############################
  ### Adjustment of Datasets ###
  ##############################
  def adjust_input_dataset(self, time_scope):

      def shorted_data(data):
        data_shorted = data.loc[start_time:end_time]
        data_shorted = data_shorted.resample(t_freq).mean()
        data_shorted = data_shorted.round(4)

        return data_shorted

      def shorted_data_sum(data):
        data_shorted = data.loc[start_time:end_time]
        data_shorted = data_shorted.resample(t_freq).sum()
        data_shorted = data_shorted.round(4)

        return data_shorted

      def data_processing(input_file, method, output_file, time_df = 0):
         data = tt.decompress_pickle(self.folder + input_file)
         if method == 'mean':
           data_shorted = shorted_data(data)
         elif method == 'sum':
           data_shorted = shorted_data_sum(data)
         else:
           raise ValueError('Inputdatahandler: data short method is not valid.')
         tt.compress_pickle(self.folder + output_file, data_shorted)
         if time_df == 1:
           time = self.get_time_df(data_shorted)
           tt.compress_pickle(self.folder + '10_time_short.pbz2', time)

      self.dates = time_scope['start_time'] + ' ' + time_scope['end_time'] + ' ' + time_scope['t_freq']

      with open(self.folder + 'daterange.csv') as daterange:
         csv_daterange = csv.reader(daterange)
         for row in csv_daterange:
            dates_old = str(row[0])

      dates_old = dates_old.strip('[')
      dates_old = dates_old.strip(']')
      dates_old = dates_old.strip('\'')


        
      if self.season != None:
          if self.scenario[0] in ['A','B','C','D','E','F','G']:
            self.inputfolder += 'YY_inputdata_BEVinLV/'
          if self.season == 'summer':
            self.inputfolder = self.inputfolder + 'XX_inputdata_summer/'
          elif self.season == 'winter':
            self.inputfolder = self.inputfolder + 'XX_inputdata_winter/'
          elif self.season == 'autumn':
            self.inputfolder = self.inputfolder + 'XX_inputdata_autumn/'
          elif self.season == 'spring':
            self.inputfolder = self.inputfolder + 'XX_inputdata_spring/'
          else:
            raise ValueError('Season in time_scope is invailed!') 
        
      elif self.season == None:

        if self.dates != dates_old:
        
          print('Adjust input datasets ...')

          start_time = pd.to_datetime(time_scope['start_time'], format='%Y-%m-%d %H:%M:%S')
          end_time = pd.to_datetime(time_scope['end_time'], format='%Y-%m-%d %H:%M:%S')
          t_freq = time_scope['t_freq']

          data_processing('01_p0_load.pbz2', 'mean', '11_p0_short.pbz2')
          data_processing('01_q0_load.pbz2', 'mean', '11_q0_short.pbz2')
          data_processing('02_pv_gen.pbz2',  'mean', '12_pv_short.pbz2', time_df = 1)
          data_processing('03_hp_load.pbz2', 'mean', '13_hp_short.pbz2')
          data_processing('04_ev_load_rural.pbz2',    'mean', '14_ev_short_rural.pbz2')
          data_processing('04_ev_load_suburban.pbz2', 'mean', '14_ev_short_suburban.pbz2')
          data_processing('04_ev_load_urban.pbz2',    'mean', '14_ev_short_urban.pbz2')
          data_processing('04_ev_charging_demand_rural.pbz2',    'sum', '14_ev_short_rural_charging_demand.pbz2')
          data_processing('04_ev_charging_demand_suburban.pbz2', 'sum', '14_ev_short_suburban_charging_demand.pbz2')
          data_processing('04_ev_charging_demand_urban.pbz2',    'sum', '14_ev_short_urban_charging_demand.pbz2')
          data_processing('04_ev_parking_time_rural.pbz2',    'mean', '14_ev_short_rural_parking_time.pbz2')
          data_processing('04_ev_parking_time_suburban.pbz2', 'mean', '14_ev_short_suburban_parking_time.pbz2')
          data_processing('04_ev_parking_time_urban.pbz2',    'mean', '14_ev_short_urban_parking_time.pbz2')
          data_processing('05_temperature_ambient.pbz2', 'mean', '15_temperature_ambient_short.pbz2')

          f = open(self.folder + 'daterange.csv','w')
          f.write(self.dates)
          f.close()
          #print('FINISH!')
          #sys.exit(0)

  def get_time_df(self, df):
        return df.index

  def create_empty_df(self, time_scope):
        # Define timeseries
        self.time_series = tt.decompress_pickle(self.inputfolder + '10_time_short.pbz2')
        self.time_series = pd.DataFrame(self.time_series)
        self.time_series.index = self.time_series['timestamp']
        # define dataframe for all data
        df = pd.DataFrame(range(0,len(self.time_series)), index=self.time_series)
        df = self.time_series
        df.index.freq = time_scope['t_freq']

        return df

