import pandapower as pp

import tools.tools as tt

class EVcreator:

  def __init__(self):

        self.ev_para = {'ev_types' : ['ev_1_120', 'ev_2_120', 'ev_3_120', 'ev_4_120', 'ev_5_120', 'ev_6_120', 'ev_7_120', 'ev_8_120', 'ev_9_120', 'ev_10_120', 'ev_11_100', 'ev_12_100', 'ev_13_100', 'ev_14_100', 'ev_15_100', 'ev_16_100', 'ev_17_100', 'ev_18_100', 'ev_19_100', 'ev_20_100', 'ev_21_70', 'ev_22_70', 'ev_23_70', 'ev_24_70', 'ev_25_70', 'ev_26_70', 'ev_27_70', 'ev_28_70', 'ev_29_70', 'ev_30_70']}
        self.ev_data_file = 'input-files/14_ev_short.pbz2'


  ###########################################
  ### Create Loads at each bus for all HP ###
  ###########################################
  def create_ev_load_at_each_bus(self, grid):
      # create hp-loads at each bus 
      for index in grid.component_buses.index:
          # calculate distribution of e-vehicles
          pp.create_load(grid.net, grid.net.load.loc[index, "bus"], 0.0, name='ev_'+str(grid.net.load.loc[index, "bus"]), type=self.ev_para['ev_types'][index%len(self.ev_para['ev_types'])])

      return grid

  ##########################################
  ### load genearation and load profiles ###
  ##########################################
  def load_ev_profiles(self, df):
        ### load ev profile ###
        ev = tt.decompress_pickle(self.ev_data_file)
        for ev_type in self.ev_para['ev_types']:
              df[ev_type] = ev[ev_type]/1000 # normalized to MW
        return df
