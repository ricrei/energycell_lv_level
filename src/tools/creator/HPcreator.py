import numpy as np
import pandapower as pp

import tools.tools as tt

class HPcreator:

  def __init__(self):
        self.hp_data_file = 'input-files/13_hp_short.pbz2'
        self.hp = tt.decompress_pickle(self.hp_data_file)
        self.hp_para = {}
        self.hp_para['hp_types'] = self.hp.columns[self.hp.columns.str.contains('Demand_el_')]
        self.hp_para['cos_phi'] = .95
        self.hp_para['tan_phi'] = np.tan(np.arccos(self.hp_para['cos_phi']))
        self.hp_para['hp_max_p_kw'] = 10
        self.hp_para['hp_cop'] = 4


  ###########################################
  ### Create Loads at each bus for all HP ###
  ###########################################
  def create_hp_load_at_each_bus(self, grid):
      if (grid.category == 'rural') or (grid.category == 'village') or (grid.category == 'suburban'):
          self.hp_para['hp_types'] = self.hp_para['hp_types'][self.hp_para['hp_types'].str.contains('DE_HEF')]
      elif (grid.category == 'urban'):
          self.hp_para['hp_types'] = self.hp_para['hp_types'][self.hp_para['hp_types'].str.contains('DE_HMF')]
      else:
          raise ValueError('No valid grid.category defined. Not able to choose HP type.')

      #create columns for HPs grid.net.load
      grid.net.load['hp_el_capacity_kwh'] = 10
      grid.net.load['hp_soc_kwh'] = 0.005
      grid.net.load['hp_self_dis_per_day'] = 0.1
      grid.net.load['hp_max_p_kw'] = 10
      grid.net.load['hp_cop'] = 4

      # create hp-loads at each bus
      for index in grid.component_buses.index:
          # calculate distribution of heatpump types and building types within the grid
          pp.create_load(grid.net, grid.net.load.loc[index, "bus"], 0.0, \
                         name='hp_'+str(grid.net.load.loc[index, "bus"]), \
                             type='hp_'+self.hp_para['hp_types'][index%len(self.hp_para['hp_types'])])

      return grid

  ##########################################
  ### load genearation and load profiles ###
  ##########################################
  def load_hp_profiles(self, df):
        for hp_type in self.hp_para['hp_types']:
            df['hp_'+hp_type+'_p'] = self.hp[hp_type]/1000 # normalized to MW
        return df
