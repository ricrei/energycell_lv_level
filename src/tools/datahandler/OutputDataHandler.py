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


class OutputDataHandler():

  def __init__(self):
    pass

  #########################
  ### create output_dir ###
  #########################
  def create_output_dir(self, net_name, scenario, time_scope):
        self.output_dir = os.path.join("./", "output-files/"+str(scenario)+"/"+str(net_name)+"/"+time_scope['start_time'][0:10]+"_"+time_scope['end_time'][0:10]+"_"+time_scope['t_freq']+"/")
        # Create output directory
        if os.path.isdir(self.output_dir):
          #print("Output directory: " + str(self.output_dir))
          pass
        else:
          try:
            os.makedirs(self.output_dir)
          except OSError:
            print("Error: Creation of output directory %s failed" % self.output_dir)
          else:
            print("Create outout directory %s" % self.output_dir)


  def create_output_dataframes(self, grid):
        self.vm_pu = pd.DataFrame(columns=grid.net.bus.index)
        self.li_lo = pd.DataFrame(columns=grid.net.line.index)
        self.tr_lo = pd.DataFrame(columns=grid.net.trafo.index)
        self.power = pd.DataFrame(columns=['load', 'pv', 'hp', 'ev'])
        self.reactive_power = pd.DataFrame(columns=grid.net.bus.index)
        self.active_power = pd.DataFrame(columns=grid.net.bus.index)
        self.vm_pu.index.name = 'timestamp'
        self.li_lo.index.name = 'timestamp'
        self.tr_lo.index.name = 'timestamp'
        self.power.index.name = 'timestamp'
        self.reactive_power.index.name  = 'timestamp'
        self.active_power.index.name = 'timestamp'

  def write_dataframe_to_csv(self, mode, header, grid):
        self.vm_pu.round(3).to_csv(self.output_dir + 'res_bus_vm_pu.csv',mode=mode, header=header, index = True)
        self.li_lo.round(1).to_csv(self.output_dir + 'res_line_load_percent.csv',mode=mode, header=header, index = True)
        self.tr_lo.round(1).to_csv(self.output_dir + 'res_trafo_load_percent.csv',mode=mode, header=header, index = True)
        self.power.round(6).to_csv(self.output_dir + 'power_total_MW.csv',mode=mode, header=header, index = True)
        self.reactive_power.round(6).to_csv(self.output_dir + 'reactive_power_MW.csv',mode=mode, header=header, index = True)
        self.active_power.round(6).to_csv(self.output_dir + 'active_power_MW.csv',mode=mode, header=header, index = True)

        self.create_output_dataframes(grid)

  def write_output_into_dataframe(self, grid, t):
        self.vm_pu.loc[t] = grid.net.res_bus.vm_pu
        self.li_lo.loc[t] = grid.net.res_line.loading_percent
        self.tr_lo.loc[t] = grid.net.res_trafo.loading_percent
        self.power.loc[t] = [grid.net.load.p_mw[grid.load_index].sum(),
                             grid.net.sgen.p_mw.sum(),
                             grid.net.load.p_mw[grid.hp_index].sum(),
                             grid.net.load.p_mw[grid.ev_index].sum()]
        self.reactive_power.loc[t] = grid.net.sgen['q_mvar']
        self.active_power.loc[t]   = grid.net.sgen['p_mw']





