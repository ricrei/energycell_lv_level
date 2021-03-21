import numpy as np
import pandapower as pp

import tools.tools as tt

class HPcreator:

  def __init__(self):

        self.hp_para = {'hp_types' : ['DE_HEF33_Air', 'DE_HEF34_Air', 'DE_HEF33_Ground', 'DE_HEF34_Ground'],
                        'cos_phi' : .95}
        self.hp_para['tan_phi'] = np.tan(np.arccos(self.hp_para['cos_phi']))
        self.hp_data_file = 'input-files/13_hp_short.pbz2'


  ###########################################
  ### Create Loads at each bus for all HP ###
  ###########################################
  def create_hp_load_at_each_bus(self, grid):

      # create hp-loads at each bus 
      for index in grid.component_buses.index:
          # calculate distribution of heatpump types and building types within the grid
          pp.create_load(grid.net, grid.net.load.loc[index, "bus"], 0.0, name='hp_'+str(grid.net.load.loc[index, "bus"]), type='hp_'+self.hp_para['hp_types'][index%len(self.hp_para['hp_types'])])

      return grid

  ##########################################
  ### load genearation and load profiles ###
  ##########################################
  def load_hp_profiles(self, df):
        ### load heatpump profile ###
        hp = tt.decompress_pickle(self.hp_data_file)
        for hp_type in self.hp_para['hp_types']:
            df['hp_'+hp_type+'_p'] = hp['Demand_el_'+hp_type]/1000 # normalized to MW
        return df
