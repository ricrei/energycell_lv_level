import numpy as np
import pandas as pd

import tools.tools as tt

class EVcontroller:

  def __init__(self, grid, control='direct', inputfolder=None):
      self.inputfolder = inputfolder
      self.control = control
      ### define ev parameter ###
      self.ev_parameter = {'charging_power' : .011,     # in MW
                           'charging_efficiency' : .9,  # 0-1
                           'direct_charge_limit' : 80,  # in %
                           'linear_charge_limit' : 90}  # in %

      if 'name' in grid.time_scope.keys():
        if grid.time_scope['name'] == 'summer':
          self.ev_parameter['linear_charge_limit'] = 80 # in %

      ### load input data ###
      if (grid.category == 'rural') or (grid.category == 'village'):
        self.ev_data_file_charging_demand = self.inputfolder + '14_ev_short_rural_charging_demand.pbz2'
        self.ev_data_file_parking_time    = self.inputfolder + '14_ev_short_rural_parking_time.pbz2'
      elif (grid.category == 'suburban'):
        self.ev_data_file_charging_demand = self.inputfolder + '14_ev_short_suburban_charging_demand.pbz2'
        self.ev_data_file_parking_time    = self.inputfolder + '14_ev_short_suburban_parking_time.pbz2'
      elif (grid.category == 'urban'):
        self.ev_data_file_charging_demand = self.inputfolder + '14_ev_short_urban_charging_demand.pbz2'
        self.ev_data_file_parking_time    = self.inputfolder + '14_ev_short_urban_parking_time.pbz2'
      else:
        raise ValueError('No valid grid.category defined. Not able to choose EV type.')

      self.ev_charging_demand = tt.decompress_pickle(self.ev_data_file_charging_demand)
      self.ev_parking_time = tt.decompress_pickle(self.ev_data_file_parking_time)

      ### initilize controller ###
      if (self.control != None):
        if self.control == 'direct':
          self.P_controller = EV_P_control_direct(grid, self.ev_parameter, self.ev_charging_demand, self.ev_parking_time)
        elif self.control == 'household-oriented_feed-in_damping':
          self.P_controller = EV_P_control_hh_fid(grid, self.ev_parameter, self.ev_charging_demand, self.ev_parking_time)
        elif self.control == 'grid-oriented_feed-in_damping':
          self.P_controller = EV_P_control_grid_fid(grid, self.ev_parameter, self.ev_charging_demand, self.ev_parking_time)
      else:
        self.P_controller = EV_P_control_no_ev(grid, self.ev_parameter, self.ev_charging_demand, self.ev_parking_time)

  def get_active_power_direct_charge(self, grid, t):
      return self.P_controller.pcontrol_direct_charge(grid, t, limit = self.P_controller.limit_direct)

  def get_active_power_p_res_charge(self, grid, t):
      return self.P_controller.pcontrol_p_res_charge(grid, t, limit = self.P_controller.limit_p_res)

  def get_active_power_trafo_charge(self, grid, t):
      return self.P_controller.pcontrol_trafo_charge(grid, t, limit = self.P_controller.limit_trafo)


### Parent class EV_P_control ###
class EV_P_control:
  def __init__(self, grid, ev_parameter, charging_demand=np.nan, parking_time=np.nan):
      self.charging_demand = charging_demand
      self.parking_time = parking_time
      self.ev_parameter = ev_parameter
      self.intervall_in_seconds = grid.time_scope['intervall_in_seconds']

  def pcontrol(self, grid, t):
      grid.net.load.ev_parking.loc[grid.ev_index] = self.parking_time[grid.net.load.loc[grid.ev_index].type].loc[t].values
      grid.net.load.ev_soc.loc[grid.ev_index] -= (self.charging_demand[grid.net.load.loc[grid.ev_index].type].loc[t].values)/grid.net.load.ev_c_bat.loc[grid.ev_index]*100
      grid.net.load.p_mw.loc[grid.ev_index] = 0

      self.check_soc_p_mw(grid)

      return grid.net.load.loc[grid.ev_index]


  def pcontrol_direct_charge(self, grid, t, limit):

      EV_P_control.pcontrol(self, grid, t)

      ev = grid.net.load.loc[grid.ev_index]
      
      soc_increase = (self.ev_parameter['charging_power'] * self.ev_parameter['charging_efficiency'] * self.intervall_in_seconds / 3600) * 1000 / ev.ev_c_bat * 100 # 1000 -> (MW->kW), 100 -> in %
      soc_increase[ev.ev_parking == 0] = 0
      soc_increase_ref = soc_increase
      soc_increase[(ev.ev_soc + soc_increase_ref > limit) & (ev.ev_soc < limit)] = limit - ev.ev_soc
      soc_increase[(ev.ev_soc + soc_increase_ref > limit) & (ev.ev_soc >= limit)] = 0

      ev.ev_soc += soc_increase
      ev.p_mw += soc_increase * ev.ev_c_bat / (self.ev_parameter['charging_efficiency'] * self.intervall_in_seconds / 3600) / 1000 / 100 # 1000 -> (kW->MW), 100 -> in %

      grid.net.load.loc[grid.ev_index] = ev

      self.check_soc_p_mw(grid)

      return grid.net.load.loc[grid.ev_index]

  def pcontrol_p_res_charge(self, grid, t, limit = 1.):
      return grid.net.load.loc[grid.ev_index]

  def pcontrol_trafo_charge(self, grid, t, limit = 1.):
      return grid.net.load.loc[grid.ev_index]

  def check_soc_p_mw(self, grid):
      ev = grid.net.load.loc[grid.ev_index]
      if (ev.p_mw.round(3) > self.ev_parameter['charging_power']).any():
         print('Warning: p_mw of ev exceeds max. charging power! ' + str(max(ev.p_mw)))
      if (ev.p_mw < 0).any():
         print('Warning: ev p_mw is below 0! ' + str(min(ev.p_mw)))
      if (ev.ev_soc > 100).any():
         print('Warning: ev soc exceeds 1! ' + str(max(ev.ev_soc)))
      if (ev.ev_soc < 0).any():
         print('Warning: ev soc is below 0! ' + str(min(ev.ev_soc)))

### no ev ###
class EV_P_control_no_ev(EV_P_control):

  def __init__(self, grid, ev_parameter, charging_demand, parking_time):
      super().__init__(grid, ev_parameter, charging_demand, parking_time)
      self.limit_direct = 0.
      self.limit_p_res = 0.
      self.limit_trafo = 0.

  def pcontrol_direct_charge(self, grid, t, limit):
      ev = grid.net.load.loc[grid.ev_index]
      ev.p_mw = 0
      return ev

### direct ###
class EV_P_control_direct(EV_P_control):

  def __init__(self, grid, ev_parameter, charging_demand, parking_time):
      super().__init__(grid, ev_parameter, charging_demand, parking_time)
      self.limit_direct = 100
      self.limit_p_res = 0.
      self.limit_trafo = 0.

### household-oriented_feed-in_damping ###
class EV_P_control_hh_fid(EV_P_control):

  def __init__(self, grid, ev_parameter, charging_demand, parking_time):
      super().__init__(grid, ev_parameter, charging_demand, parking_time)
      self.limit_direct = self.ev_parameter['direct_charge_limit']
      self.limit_p_res = 100
      self.limit_trafo = 0.

  def pcontrol_p_res_charge(self, grid, t, limit):

      self.p_res = -grid.get_residualload_p_per_household()

      ev = grid.net.load.loc[grid.ev_index]

      # max. increase of soc
      soc_increase_ref = ((self.ev_parameter['charging_power'] - ev.p_mw) * self.ev_parameter['charging_efficiency'] * self.intervall_in_seconds / 3600) * 1000 / ev.ev_c_bat * 100 # 1000 -> (MW->kW), 100 -> in %

      # soc increase due to surplus pv
      soc_increase = (self.p_res * self.ev_parameter['charging_efficiency'] * self.intervall_in_seconds / 3600) * 1000 / ev.ev_c_bat * 100 # 1000 -> (MW->kW), 100 -> in %

      # no surplus pv power leads to no soc increase
      soc_increase[self.p_res < 0] = 0
      # soc increase couldn't be higher than max. soc increase due to max. charging power
      soc_increase[soc_increase > soc_increase_ref] = soc_increase_ref
      # no parking ev no charging
      soc_increase[ev.ev_parking == 0] = 0
      # soc increase until 'limit' is reached
      soc_increase[(ev.ev_soc + soc_increase > limit) & (ev.ev_soc < limit)] = limit - ev.ev_soc
      # soc increase above 'limit' leads to no soc increase
      soc_increase[(ev.ev_soc + soc_increase > limit) & (ev.ev_soc >= limit)] = 0

      ev.ev_soc += soc_increase
      ev.p_mw   += soc_increase * ev.ev_c_bat / (self.ev_parameter['charging_efficiency'] * self.intervall_in_seconds / 3600) / 1000 / 100 # 1000 -> (MW->kW), 100 -> in %

      grid.net.load.loc[grid.ev_index] = ev

      self.check_soc_p_mw(grid)

      return grid.net.load.loc[grid.ev_index]


### grid-oriented_feed-in_damping ###
class EV_P_control_grid_fid(EV_P_control):

  def __init__(self, grid, ev_parameter, charging_demand, parking_time):
      super().__init__(grid, ev_parameter, charging_demand, parking_time)
      self.limit_direct = self.ev_parameter['direct_charge_limit']
      self.limit_p_res = self.ev_parameter['linear_charge_limit']
      self.limit_trafo = 100

  def pcontrol_p_res_charge(self, grid, t, limit):
      s_res, p_res = grid.get_residualload_s_sum()
      p_res = -p_res

      ev = grid.net.load.loc[grid.ev_index]

      # max. increase of soc
      soc_increase_ref = ((self.ev_parameter['charging_power'] - ev.p_mw) * self.ev_parameter['charging_efficiency'] * self.intervall_in_seconds / 3600) * 1000 / ev.ev_c_bat * 100 # 1000 -> (MW->kW), 100 -> in %

      ev_available = (ev.ev_parking == True) & (ev.ev_soc < limit)
      available_capacity = (limit - ev.ev_soc)*ev.ev_c_bat # in kWh
      available_capacity[ev_available == False] = 0
      available_capacity[available_capacity > 0] = available_capacity/available_capacity.sum() # in %

      # soc increase due to surplus pv
      soc_increase = (p_res * available_capacity * self.ev_parameter['charging_efficiency'] * self.intervall_in_seconds / 3600) * 1000 / ev.ev_c_bat * 100 # 1000 -> (MW->kW), 100 -> in %
      # no surplus pv power leads to no soc increase
      soc_increase[soc_increase < 0] = 0
      # soc increase couln't be higher than max. soc increase due to max. charging power
      soc_increase[soc_increase > soc_increase_ref] = soc_increase_ref
      # no parking ev no charging
      soc_increase[ev.ev_parking == 0] = 0
      # soc increase until 'limit' is reached
      soc_increase[(ev.ev_soc + soc_increase > limit) & (ev.ev_soc < limit)] = limit - ev.ev_soc
      # soc increase above 'limit' leads to no soc increase
      soc_increase[(ev.ev_soc + soc_increase > limit) & (ev.ev_soc >= limit)] = 0

      ev.ev_soc += soc_increase
      ev.p_mw   += soc_increase * ev.ev_c_bat / (self.ev_parameter['charging_efficiency'] * self.intervall_in_seconds / 3600) / 1000 / 100 # 1000 -> (MW->kW), 100 -> in %

      grid.net.load.loc[grid.ev_index] = ev

      self.check_soc_p_mw(grid)

      return grid.net.load.loc[grid.ev_index]

  def pcontrol_trafo_charge(self, grid, t, limit):
      s_res, p_res = grid.get_residualload_s_sum()
      p_res = -p_res

      if grid.s_trafo_power < -s_res:
         q_res_to_the_power_of_2 = s_res**2 - p_res**2
         if q_res_to_the_power_of_2 < grid.s_trafo_power**2:
            p_trafo_max = (grid.s_trafo_power**2 - q_res_to_the_power_of_2)**(.5)
         else:
            p_trafo_max = 0
      else:
         p_trafo_max = p_res

      p_total_ev = p_res - p_trafo_max

      ev = grid.net.load.loc[grid.ev_index]

      # max. increase of soc
      soc_increase_ref = ((self.ev_parameter['charging_power'] - ev.p_mw) * self.ev_parameter['charging_efficiency'] * self.intervall_in_seconds / 3600) * 1000 / ev.ev_c_bat * 100 # 1000 -> (MW->kW), 100 -> in %

      ev_available = (ev.ev_soc < limit) & (ev.ev_parking == True)
      available_capacity = (limit - ev.ev_soc)*ev.ev_c_bat # in kWh
      available_capacity[ev_available == False] = 0
      available_capacity[available_capacity > 0] = available_capacity/available_capacity.sum() # in %

      # soc increase due to surplus pv
      soc_increase = (p_total_ev * available_capacity * self.ev_parameter['charging_efficiency'] * self.intervall_in_seconds / 3600) * 1000 / ev.ev_c_bat * 100 # 1000 -> (MW->kW), 100 -> in %
      # no surplus pv power leads to no soc increase
      soc_increase[soc_increase < 0] = 0
      # soc increase couln't be higher than max. soc increase due to max. charging power
      soc_increase[soc_increase > soc_increase_ref] = soc_increase_ref
      # no parking ev no charging
      soc_increase[ev.ev_parking == 0] = 0
      # soc increase until 'limit' is reached
      soc_increase[(ev.ev_soc + soc_increase > limit) & (ev.ev_soc < limit)] = limit - ev.ev_soc
      # soc increase above 'limit' leads to no soc increase
      soc_increase[(ev.ev_soc + soc_increase > limit) & (ev.ev_soc >= limit)] = 0

      ev.ev_soc += soc_increase
      ev.p_mw   += soc_increase * ev.ev_c_bat / (self.ev_parameter['charging_efficiency'] * self.intervall_in_seconds / 3600) / 1000 / 100 # 1000 -> (MW->kW), 100 -> in %

      grid.net.load.loc[grid.ev_index] = ev

      self.check_soc_p_mw(grid)

      return grid.net.load.loc[grid.ev_index]
