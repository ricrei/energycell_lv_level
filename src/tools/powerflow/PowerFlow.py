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

class PowerFlow:

  def __init__(self):
    pass

  def get_df_and_grid(self, df, grid):
    self.df = df
    self.grid = grid

  def set_time_step_array(self, df):
    self.time_series = df['timestamp']
    self.timesteps = len(self.time_series)
    time_step_size = round(self.timesteps/10 + .5)
    time_delta = int((self.timesteps - self.timesteps%time_step_size)/time_step_size)
    self.time_step_array = 0*np.arange(time_delta + 1) + 1
    self.time_step_array = int((self.timesteps - self.timesteps%time_delta)/time_delta)*self.time_step_array
    self.time_step_array[time_delta] = int(self.timesteps%time_delta)

  def merge_df_and_grid_at_time_i(self, d, grid, pv_controller):

    grid.net.sgen['p_mw'] = d[grid.label_pv_p].values
    grid.net.sgen['q_mvar'] = pv_controller.get_reactive_power(grid)

    grid.net.load.loc[grid.load_index, 'p_mw'] = d[grid.label_load_p].values
    grid.net.load.loc[grid.load_index, 'q_mvar'] = d[grid.label_load_q].values

    grid.net.load.loc[grid.hp_index, 'p_mw'] = d[grid.label_hp_p].values
    grid.net.load.loc[grid.hp_index, 'q_mvar'] = d[grid.label_hp_q].values

    grid.net.load.loc[grid.ev_index, 'p_mw'] = d[grid.label_ev].values

    return grid.net

  def run_power_flow_through_timeseries(self,
                                        df,
                                        grid,
                                        pv_controller,
                                        output_data_handler):
      self.set_time_step_array(df)
      rest_time = ''
      i = 0
      ### main loop: try to avoid 'if', 'for', ... statments ###
      ###           Processing time is valuable!             ###
      for k in self.time_step_array:
          for j in range(k):
            start = time.time()
            tt.progress(i, self.timesteps, status=' %s s ' % rest_time)

            t = self.time_series[i]
            d = df.loc[t]

            grid.net = self.merge_df_and_grid_at_time_i(d=d,
                                                        grid=grid,
                                                        pv_controller=pv_controller)

            # run pandapower power flow
            pp.runpp(grid.net, max_iteration=30, tolerance_mva=1e-6)

            # write result into DataFrame
            output_data_handler.write_output_into_dataframe(grid, t)

            end = time.time()
            rest_time = int(round((end - start)*(self.timesteps - i), 0))
            i += 1
          output_data_handler.write_dataframe_to_csv(mode='a', header=False, grid=grid)

      tt.progress(1, 1, status=' Done ')
      print('')
