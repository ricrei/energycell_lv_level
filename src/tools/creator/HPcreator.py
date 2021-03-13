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

class HPcreator:

  def __init__(self, scenario):
        self.set_hp = (scenario == 2) | (scenario == 4)
        self.hp_para = {'hp_types' : ['DE_HEF33_Air', 'DE_HEF34_Air', 'DE_HEF33_Ground', 'DE_HEF34_Ground'],
                        'cos_phi' : .95}
        self.hp_para['tan_phi'] = np.tan(np.arccos(self.hp_para['cos_phi']))
        self.hp_data_file = 'input-files/13_hp_short.pbz2'


  ###########################################
  ### Create Loads at each bus for all HP ###
  ###########################################
  def create_hp_load_at_each_bus(self, grid):
      if self.set_hp == True:
        # create hp-loads at each bus 
        for index in grid.net.load.index:
          # calculate distribution of heatpump types and building types within the grid
          pp.create_load(grid.net, grid.net.load.loc[index, "bus"], 0.0, name='hp_'+str(grid.net.load.loc[index, "bus"]), type='hp_'+self.hp_para['hp_types'][index%len(self.hp_para['hp_types'])])

      return grid

  ##########################################
  ### load genearation and load profiles ###
  ##########################################
  def load_hp_profiles(self, df):
        ### load heatpump profile ###
        if self.set_hp == True:
          hp = tt.decompress_pickle(self.hp_data_file)
          for hp_type in self.hp_para['hp_types']:
            df['hp_'+hp_type+'_p'] = hp['Demand_el_'+hp_type]/1000 # normalized to MW
            # TODO: cos_phi Berechnung anpassen
            df['hp_'+hp_type+'_q'] = hp['Demand_el_'+hp_type]*self.hp_para['tan_phi']/1000 # normalized to MW
        return df
