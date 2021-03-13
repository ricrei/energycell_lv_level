import os
import csv
import time
import numpy as np
import pandas as pd
import pandapower as pp
import pandapower.networks as pn
import pandapower.toolbox as tb
import simbench as sb
import tools.tools as tt

import bz2
import _pickle as cPickle


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
        ev = tt.decompress_pickle('input-files/04_ev_load.pbz2')

        p0_shorted = shorted_data(p0, start_time, end_time, t_freq)
        q0_shorted = shorted_data(q0, start_time, end_time, t_freq)
        pv_shorted = shorted_data(pv, start_time, end_time, t_freq)
        hp_shorted = shorted_data(hp, start_time, end_time, t_freq)
        ev_shorted = shorted_data(ev, start_time, end_time, t_freq)

        time = self.get_time_df(pv_shorted)

        tt.compress_pickle('input-files/10_time_short.pbz2', time)
        tt.compress_pickle('input-files/11_p0_short.pbz2', p0_shorted)
        tt.compress_pickle('input-files/11_q0_short.pbz2', q0_shorted)
        tt.compress_pickle('input-files/12_pv_short.pbz2', pv_shorted)
        tt.compress_pickle('input-files/13_hp_short.pbz2', hp_shorted)
        tt.compress_pickle('input-files/14_ev_short.pbz2', ev_shorted)

        f = open('input-files/daterange.csv','w')
        f.write(self.dates)
        f.close()

  def get_time_df(self, df):
        return df.index

