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

class HHLcreator:

  def __init__(self):
        self.load_p_data_file = 'input-files/11_p0_short.pbz2'
        self.load_q_data_file = 'input-files/11_q0_short.pbz2'

  ###########################################
  ### Create Loads at each bus for all HP ###
  ###########################################
  def create_hh_load_at_each_bus(self, grid):
      # create hp-loads at each bus 
      for index in grid.net.load.index:
          grid.net.load.name.loc[index] = 'load_'+str(grid.net.load.loc[index, "bus"])
          grid.net.load.type.loc[index] = 'load_'+str(index%74)
          #grid.net.load.type[index] = 'load_'+str(index%74)

      return grid

  ##########################################
  ### load genearation and load profiles ###
  ##########################################
  def load_hhl_profiles(self, df):
        ### load load profiles ###
        p0 = tt.decompress_pickle(self.load_p_data_file)
        q0 = tt.decompress_pickle(self.load_q_data_file)
        for i in range(0,74):
            df['load_'+str(i)+'_p'] = p0["p"+str(i)]/1000	# normalized to MW
            df['load_'+str(i)+'_q'] = q0["q"+str(i)]/1000	# normalized to MW

        return df
