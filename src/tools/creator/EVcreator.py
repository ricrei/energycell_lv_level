import pandapower as pp
import numpy as np

import tools.tools as tt

class EVcreator:

  def __init__(self, inputfolder, control_parameter):
    self.inputfolder = inputfolder
    self.control_parameter = control_parameter
    self.usable_c_bat = control_parameter['EV_usable_c_bat']#100 # in %
    self.ev_start_soc = control_parameter['EV_start_soc']#100 # in %

  ###########################################
  ### Create Loads at each bus for all HP ###
  ###########################################
  def create_ev_load_at_each_bus(self, grid):
      if grid.scenario[4] == 4:
        charging_strategy = 'gre'
      elif grid.scenario[4] == 5:
        charging_strategy = 'bal'
      elif grid.scenario[4] == 6:
        charging_strategy = 'mar'
      elif grid.scenario[4] == 7:
        charging_strategy = 'res'
      else:
        charging_strategy = 'gre'

      if grid.scenario[0] in ['A','B','C']:
        self.ev_data_file = self.inputfolder + '14_ev_load_'+str(grid.category)+'_'+grid.time_scope['name']+'_'+charging_strategy+'.pbz2'

      else:
        if (grid.category == 'rural') or (grid.category == 'village'):
          self.ev_data_file = self.inputfolder + '14_ev_short_rural.pbz2'
        elif (grid.category == 'suburban'):
          self.ev_data_file = self.inputfolder + '14_ev_short_suburban.pbz2'
        elif (grid.category == 'urban'):
          self.ev_data_file = self.inputfolder + '14_ev_short_urban.pbz2'
        else:
          raise ValueError('No valid grid.category defined. Not able to choose EV type.')

      self.ev = tt.decompress_pickle(self.ev_data_file)
      self.ev['ev_000_000kWh_rural'] = 0
      self.ev_para = {'ev_types' : self.ev.columns}

      grid.net.load['ev_c_bat'] = np.nan
      grid.net.load['ev_soc'] = np.nan
      grid.net.load['ev_parking'] = np.nan
      grid.net.load['ev_amount'] = 0

      if grid.scenario[0] in ['A','B','C']:
        x = round(len(self.ev.columns) / len(grid.component_buses.index))
      else:
        x = 1

      share = 0 # share of bev in net
      n_ev = 0
      n_noev = 0

      share_double = 0 # share of hh with two bevs
      n_ev_double = 0

      # create ev-loads at each bus 
      for index in grid.component_buses.index:
       if self.control_parameter['NEP']['ev'] != 0.:
        if share <= self.control_parameter['NEP']['ev']:
          n_ev += 1
          # calculate distribution of e-vehicles
          index_ev = pp.create_load(net = grid.net,
                         bus = grid.net.load.loc[index, "bus"],
                         p_mw = 0.0,
                         name='ev_'+str(grid.net.load.loc[index, "bus"]),
                         type=self.ev_para['ev_types'][(index*x)%len(self.ev_para['ev_types'])],
                         )
          grid.net.load['ev_c_bat'].loc[index_ev] = int(grid.net.load.type[index_ev][7:10])*self.usable_c_bat/100
          grid.net.load['ev_soc'].loc[index_ev] = self.ev_start_soc
          if share_double < self.control_parameter['NEP']['ev'] - 1:
            grid.net.load['ev_amount'].loc[index_ev] = 2
            n_ev_double += 1
          else:
            grid.net.load['ev_amount'].loc[index_ev] = 1

          share_double = n_ev_double / (n_ev + n_noev)

          share = n_ev / (n_ev + n_noev)

        elif share > self.control_parameter['NEP']['ev']:
          n_noev += 1
          # calculate distribution of e-vehicles
          index_ev = pp.create_load(net = grid.net,
                         bus = grid.net.load.loc[index, "bus"],
                         p_mw = 0.0,
                         name='ev_'+str(grid.net.load.loc[index, "bus"]),
                         type='ev_000_000kWh_xxxxx',
                         )

          share = n_ev / (n_ev + n_noev)

      grid.net.load['p_mw_flex'] = 0

      return grid

  ##########################################
  ### load genearation and load profiles ###
  ##########################################
  def load_ev_profiles(self, df):
        for ev_type in self.ev_para['ev_types']:
              df[ev_type] = self.ev[ev_type]/1000 # normalized to MW
        return df
