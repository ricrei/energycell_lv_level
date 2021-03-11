import os
import csv
import time
import numpy as np
import pandas as pd
import pandapower as pp
import pandapower.networks as pn
import pandapower.toolbox as tb
import simbench as sb
import tools.progress as prog
import tools.tools as tt

import bz2
import _pickle as cPickle

class EVcreator:

  def __init__(self, set_ev):
        self.set_ev = set_ev
        self.ev_para = {'ev_types' : ['ev_1_120', 'ev_2_120', 'ev_3_120', 'ev_4_120', 'ev_5_120', 'ev_6_120', 'ev_7_120', 'ev_8_120', 'ev_9_120', 'ev_10_120', 'ev_11_100', 'ev_12_100', 'ev_13_100', 'ev_14_100', 'ev_15_100', 'ev_16_100', 'ev_17_100', 'ev_18_100', 'ev_19_100', 'ev_20_100', 'ev_21_70', 'ev_22_70', 'ev_23_70', 'ev_24_70', 'ev_25_70', 'ev_26_70', 'ev_27_70', 'ev_28_70', 'ev_29_70', 'ev_30_70']}



  ###########################################
  ### Create Loads at each bus for all HP ###
  ###########################################
  def create_ev_load_at_each_bus(self, grid):
      if self.set_ev == True:
        # create hp-loads at each bus 
        for index in grid.net.load.index:
          # calculate distribution of e-vehicles
          pp.create_load(grid.net, grid.net.load.loc[index, "bus"], 0.0, name='ev_'+str(grid.net.load.loc[index, "bus"]), type=self.ev_para['ev_types'][index%len(self.ev_para['ev_types'])])

      return grid

  ##########################################
  ### load genearation and load profiles ###
  ##########################################
  def load_ev_profiles(self, df, ev_data_file):
        ### load ev profile ###
        if self.set_ev == True:
            ev = tt.decompress_pickle(ev_data_file)
            for ev_type in self.ev_para['ev_types']:
              df[ev_type] = ev[ev_type]/1000 # normalized to MW
        return df
