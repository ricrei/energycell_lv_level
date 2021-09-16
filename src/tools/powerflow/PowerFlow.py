import time
import numpy as np
import pandapower as pp
import logging
import tools.tools as tt

from pandapower.plotting.plotly import pf_res_plotly
import pandas as pd

class PowerFlow:

  def __init__(self, output_dir):
      self.output_dir = output_dir

      # define logger
      self.logger = logging.getLogger('PowerFlow_Logger')
      self.logger.setLevel(logging.DEBUG)
      self.fh = logging.FileHandler('EnergyCell.log')
      self.fh.setLevel(logging.DEBUG)
      self.logger.addHandler(self.fh)
      self.formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - '+str(self.output_dir)+'- %(message)s')
      self.fh.setFormatter(self.formatter)
      self.logger.addHandler(self.fh)

  def run_power_flow_through_timeseries(self,
                                        df,
                                        grid,
                                        pv_controller,
                                        hp_controller,
                                        ev_controller,
                                        bss_controller,
                                        curtail_controller,
                                        energy_manager,
                                        output_data_handler):

      self.input_dict = self.create_input_dict(df, grid)

      output_data_handler.write_dataframe_to_csv(mode='w', header=True, grid=grid)

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

              grid.net = energy_manager.control_components(
                                                          input_dict=self.input_dict,
                                                          grid=grid,
                                                          pv_controller=pv_controller,
                                                          hp_controller=hp_controller,
                                                          ev_controller=ev_controller,
                                                          bss_controller=bss_controller,
                                                          curtail_controller=curtail_controller,
                                                          t=t)

              try:
                pp.runpp(grid.net, algorithm='nr', init='results')
              except:
                try:
                  pp.runpp(grid.net, algorithm='nr', max_iteration=30, tolerance_mva=1e-6)
                except:
                  print(tt.textred('Power Flow nr did not converge at ' + str(t)))
                  self.logger.error('Power Flow nr did not converge at ' + str(t))

              # write result into DataFrame
              output_data_handler.write_output_into_dataframe(grid, t)

              end = time.time()
              rest_time = int(round((end - start)*(self.timesteps - i), 0))
              i += 1
          # write results dataframe into csv
          output_data_handler.write_dataframe_to_csv(mode='a', header=False, grid=grid)

      tt.progress(1, 1, status=' Done ')
      print('')

      return grid

  def set_time_step_array(self, df):
      self.time_series = df['timestamp']
      self.timesteps = len(self.time_series)
      time_step_size = round(self.timesteps/10 + .5)
      time_delta = int((self.timesteps - self.timesteps%time_step_size)/time_step_size)
      self.time_step_array = 0*np.arange(time_delta + 1) + 1
      self.time_step_array = int((self.timesteps - self.timesteps%time_delta)/time_delta)*self.time_step_array
      self.time_step_array[time_delta] = int(self.timesteps%time_delta)

  ###############################
  ### create input dictionary ###
  ###############################
  def create_input_dict(self, df, grid):
        input_dict = {}
        input_dict['load_p'] = df[grid.label_load_p]
        input_dict['load_q'] = df[grid.label_load_q]
        input_dict['pv'] = df[grid.label_pv_p]
        input_dict['hp'] = df[grid.label_hp_p]
        input_dict['ev'] = df[grid.label_ev]
        input_dict['timestamp'] = df['timestamp']
        return input_dict
