import pandapower as pp
import numpy as np

import tools.tools as tt

class EVcreator:

  def __init__(self):
    self.usable_c_bat = 1 # 0-1
    self.ev_start_soc = .5 # 0-1


  ###########################################
  ### Create Loads at each bus for all HP ###
  ###########################################
  def create_ev_load_at_each_bus(self, grid):
      if (grid.category == 'rural') or (grid.category == 'village'):
        self.ev_data_file = 'input-files/14_ev_short_rural.pbz2'
      elif (grid.category == 'suburban'):
        self.ev_data_file = 'input-files/14_ev_short_suburban.pbz2'
      elif (grid.category == 'urban'):
        self.ev_data_file = 'input-files/14_ev_short_urban.pbz2'
      else:
          raise ValueError('No valid grid.category defined. Not able to choose EV type.')

      self.ev = tt.decompress_pickle(self.ev_data_file)
      self.ev_para = {'ev_types' : self.ev.columns}

      grid.net.load['ev_c_bat'] = np.nan
      grid.net.load['ev_soc'] = np.nan
      grid.net.load['ev_parking'] = np.nan

      # create hp-loads at each bus 
      for index in grid.component_buses.index:
          # calculate distribution of e-vehicles
          index_ev = pp.create_load(net = grid.net,
                         bus = grid.net.load.loc[index, "bus"],
                         p_mw = 0.0,
                         name='ev_'+str(grid.net.load.loc[index, "bus"]),
                         type=self.ev_para['ev_types'][index%len(self.ev_para['ev_types'])],
                         )


          grid.net.load['ev_c_bat'].loc[index_ev] = int(grid.net.load.type[index_ev][7:10])*self.usable_c_bat
          grid.net.load['ev_soc'].loc[index_ev] = self.ev_start_soc

      return grid

  ##########################################
  ### load genearation and load profiles ###
  ##########################################
  def load_ev_profiles(self, df):
        for ev_type in self.ev_para['ev_types']:
              df[ev_type] = self.ev[ev_type]/1000 # normalized to MW
        return df
