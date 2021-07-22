import numpy as np
import pandas as pd

import tools.tools as tt

class EVcontroller:

  def __init__(self, grid, control='greedy'):
      self.set_ev = (grid.scenario[0] in [2, 4, 5, 6, 7, 8])
      if (control=='greedy' or control=='household-oriented_feed-in_damping' or control=='grid-oriented_feed-in_damping'):
        self.control = control
      else:
        raise ValueError('The entered EV control is not a valid option.')

      self.ev_parameter = {'charging_power' : .011,
                           'charging_efficiency' : .9,
                           'greedy_charge_limit' : .7,
                           'linear_charge_limit' : .8}

      if (grid.category == 'rural') or (grid.category == 'village'):
        self.ev_data_file_charging_demand = 'input-files/14_ev_short_rural_charging_demand.pbz2'
        self.ev_data_file_parking_time    = 'input-files/14_ev_short_rural_parking_time.pbz2'
      elif (grid.category == 'suburban'):
        self.ev_data_file_charging_demand = 'input-files/14_ev_short_suburban_charging_demand.pbz2'
        self.ev_data_file_parking_time    = 'input-files/14_ev_short_suburban_parking_time.pbz2'
      elif (grid.category == 'urban'):
        self.ev_data_file_charging_demand = 'input-files/14_ev_short_urban_charging_demand.pbz2'
        self.ev_data_file_parking_time    = 'input-files/14_ev_short_urban_parking_time.pbz2'
      else:
          raise ValueError('No valid grid.category defined. Not able to choose EV type.')

      self.ev_charging_demand = tt.decompress_pickle(self.ev_data_file_charging_demand)
      self.ev_parking_time = tt.decompress_pickle(self.ev_data_file_parking_time)

      if self.set_ev == True:
        if self.control == 'greedy':
          self.P_controller = EV_P_control_greedy(grid)
        elif self.control == 'household-oriented_feed-in_damping':
          self.P_controller = EV_P_control_hh_fid(grid, self.ev_parameter, self.ev_charging_demand, self.ev_parking_time)
        elif self.control == 'grid-oriented_feed-in_damping':
          self.P_controller = EV_P_control_grid_fid(grid, self.ev_parameter, self.ev_charging_demand, self.ev_parking_time)
      else:
        self.P_controller = EV_P_control_no_ev(grid)

  def get_active_power(self, grid, d, t):
      return self.P_controller.pcontrol(grid, d, t)


class EV_P_control:
  def __init__(self, grid, ev_parameter, charging_demand=np.nan, parking_time=np.nan):
      self.charging_demand = charging_demand
      self.parking_time = parking_time
      self.ev_parameter = ev_parameter
      self.intervall_in_seconds = grid.time_scope['intervall_in_seconds']

  def pcontrol(self):
      pass

### no ev ###
class EV_P_control_no_ev(EV_P_control):

  def __init__(self, grid):
      super().__init__(grid)

  def pcontrol(self, grid, d, t):
      EV_P_control.pcontrol(self)
      return d.values*0

### greedy ###
class EV_P_control_greedy(EV_P_control):

  def __init__(self, grid):
      super().__init__(grid)

  def pcontrol(self, grid, d):
      EV_P_control.pcontrol(self)
      return d.values

### household-oriented_feed-in_damping ###
class EV_P_control_hh_fid(EV_P_control):

  def __init__(self, grid, ev_parameter, charging_demand, parking_time):
      #TODO
      print('Warning: EV household-oriented_feed-in_damping control is not implemented')
      super().__init__(grid, ev_parameter, charging_demand, parking_time)

  def pcontrol(self, grid, d, t):
      EV_P_control.pcontrol(self)

      self.p_res = grid.get_residualload_p_per_household()

      grid = self.greedy_charge(grid, t)

      return grid.net.load.p_mw.loc[grid.ev_index]#d.values

  def greedy_charge(self, grid, t):

      ev = grid.net.load.loc[grid.ev_index]
      ev.loc[ev.ev_soc >= self.ev_parameter['greedy_charge_limit'], 'p_mw'] = 0

      ev.ev_parking = self.parking_time[ev.type].loc[t].values
      
      ev.loc[(ev.ev_soc < self.ev_parameter['greedy_charge_limit']) & (ev.ev_parking > 0), 'p_mw'] = self.ev_parameter['charging_power']
      ev.loc[(ev.ev_soc < self.ev_parameter['greedy_charge_limit']) & (ev.ev_parking > 0), 'ev_soc'] += (self.ev_parameter['charging_power'] * self.ev_parameter['charging_efficiency'] * self.intervall_in_seconds / 3600) *1000 / ev.loc[ev.ev_soc < self.ev_parameter['greedy_charge_limit'], 'ev_c_bat']

      grid.net.load.loc[grid.ev_index] = ev


      return grid


### grid-oriented_feed-in_damping ###
class EV_P_control_grid_fid(EV_P_control):

  def __init__(self, ev_parameter, grid, charging_demand, parking_time):
      #TODO
      print('Warning: EV grid-oriented_feed-in_damping control is not implemented')
      super().__init__(grid, ev_parameter, charging_demand, parking_time)

  def pcontrol(self, grid, d):
      EV_P_control.pcontrol(self)
      return d.values
