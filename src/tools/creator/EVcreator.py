import pandapower as pp

import tools.tools as tt

class EVcreator:

  def __init__(self):
        self.ev_data_file = 'input-files/14_ev_short.pbz2'
        self.ev = tt.decompress_pickle(self.ev_data_file)        
        self.ev_para = {'ev_types' : self.ev.columns.values}

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
        for ev_type in self.ev_para['ev_types']:
              df[ev_type] = self.ev[ev_type]/1000 # normalized to MW
        return df
