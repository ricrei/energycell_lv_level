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
                           'greedy_charge_limit' : .8,
                           'linear_charge_limit' : .9}

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
          self.P_controller = EV_P_control_greedy(grid, self.ev_parameter, self.ev_charging_demand, self.ev_parking_time)
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

  def pcontrol(self, grid, d, t):
      grid.net.load.ev_parking.loc[grid.ev_index] = self.parking_time[grid.net.load.loc[grid.ev_index].type].loc[t].values
      grid.net.load.ev_soc.loc[grid.ev_index] -= (self.charging_demand[grid.net.load.loc[grid.ev_index].type].loc[t].values)/grid.net.load.ev_c_bat.loc[grid.ev_index]
      grid.net.load.p_mw.loc[grid.ev_index] = 0

      return grid


  def greedy_charge(self, grid, t, limit = 1.0):

      ev = grid.net.load.loc[grid.ev_index]
      
      soc_increase = (self.ev_parameter['charging_power'] * self.ev_parameter['charging_efficiency'] * self.intervall_in_seconds / 3600) *1000 / ev.ev_c_bat
      soc_increase[ev.ev_parking == 0] = 0
      soc_increase_ref = soc_increase
      soc_increase[(ev.ev_soc + soc_increase_ref > limit) & (ev.ev_soc < limit)] = limit - ev.ev_soc
      soc_increase[(ev.ev_soc + soc_increase_ref > limit) & (ev.ev_soc >= limit)] = 0

      ev.ev_soc += soc_increase
      ev.p_mw += soc_increase * ev.ev_c_bat / (self.ev_parameter['charging_efficiency'] * self.intervall_in_seconds / 3600) / 1000     

      grid.net.load.loc[grid.ev_index] = ev

      return grid

### no ev ###
class EV_P_control_no_ev(EV_P_control):

  def __init__(self, grid, ev_parameter, charging_demand, parking_time):
      super().__init__(grid, ev_parameter, charging_demand, parking_time)

  def pcontrol(self, grid, d, t):
      grid = EV_P_control.pcontrol(self, grid, d, t)
      return grid.net.load.p_mw.loc[grid.ev_index]*0#d.values*0

### greedy ###
class EV_P_control_greedy(EV_P_control):

  def __init__(self, grid, ev_parameter, charging_demand, parking_time):
      super().__init__(grid, ev_parameter, charging_demand, parking_time)

  def pcontrol(self, grid, d, t):
      EV_P_control.pcontrol(self, grid, d, t)
      grid = self.greedy_charge(grid, t, limit = 1.0)

      return grid.net.load.p_mw.loc[grid.ev_index]#d.values

### household-oriented_feed-in_damping ###
class EV_P_control_hh_fid(EV_P_control):

  def __init__(self, grid, ev_parameter, charging_demand, parking_time):
      #TODO
      print('Warning: EV household-oriented_feed-in_damping control is not implemented')
      super().__init__(grid, ev_parameter, charging_demand, parking_time)

  def pcontrol(self, grid, d, t):
      grid = EV_P_control.pcontrol(self, grid, d, t)
      grid = self.greedy_charge(grid, t, limit = self.ev_parameter['greedy_charge_limit'])
      grid = self.p_res_charge(grid, t, limit = 1.0)

      return grid.net.load.p_mw.loc[grid.ev_index]#d.values


  def p_res_charge(self, grid, t, limit = 1.0):

      self.p_res = -grid.get_residualload_p_per_household()

      ev = grid.net.load.loc[grid.ev_index]

      soc_increase_ref = (self.ev_parameter['charging_power'] * self.ev_parameter['charging_efficiency'] * self.intervall_in_seconds / 3600) *1000 / ev.ev_c_bat

      soc_increase = (self.p_res * self.ev_parameter['charging_efficiency'] * self.intervall_in_seconds / 3600) *1000 / ev.ev_c_bat
      soc_increase[self.p_res < 0] = 0
      soc_increase[soc_increase > soc_increase_ref] = soc_increase_ref
      soc_increase[ev.ev_parking == 0] = 0
      soc_increase[(ev.ev_soc + soc_increase > limit) & (ev.ev_soc < limit)] = limit - ev.ev_soc
      soc_increase[(ev.ev_soc + soc_increase > limit) & (ev.ev_soc >= limit)] = 0

      ev.ev_soc += soc_increase
      ev.p_mw += soc_increase * ev.ev_c_bat / (self.ev_parameter['charging_efficiency'] * self.intervall_in_seconds / 3600) / 1000     

      grid.net.load.loc[grid.ev_index] = ev

      return grid


### grid-oriented_feed-in_damping ###
class EV_P_control_grid_fid(EV_P_control):

  def __init__(self, ev_parameter, grid, charging_demand, parking_time):
      #TODO
      print('Warning: EV grid-oriented_feed-in_damping control is not implemented')
      super().__init__(grid, ev_parameter, charging_demand, parking_time)

  def pcontrol(self, grid, d, t):
      grid = EV_P_control.pcontrol(self, grid, d, t)
      grid = self.greedy_charge(grid, t, limit = self.ev_parameter['greedy_charge_limit'])
      #self.p_res = grid.get_residualload_p_per_household()

      return grid.net.load.p_mw.loc[grid.ev_index]#d.values
