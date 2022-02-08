import numpy as np
import pandas as pd
import datetime as dt
from tools.controller.HPstorages import HPstorages

class HPcontroller:

  def __init__(self, grid, control):
      self.control = control
      self.cos_phi = .95
      self.tan_phi = np.tan(np.arccos(self.cos_phi))
      
      if (self.control != None):
        if self.control == 'direct':
          self.P_controller = HP_P_control_direct(grid)
        elif self.control == 'household-oriented_feed-in_damping':
          self.P_controller = HP_P_control_hh_fid(grid)
        elif self.control == 'grid-oriented_feed-in_damping':
          self.P_controller = HP_P_control_grid_fid(grid)
        elif self.control == 'evu_lock':
          self.P_controller = HP_P_control_evu_lock(grid)
        elif self.control == 'residual_load_driven':
          self.P_controller = HP_P_control_resi_load_driven(grid)
      else:
        self.P_controller =  HP_P_control_no_hp(grid)

  def get_active_power(self, grid, d, t):
      return self.P_controller.pcontrol(grid, d, t)

  def get_active_power_direct_charge(self, grid, d, t):
      return self.P_controller.pcontrol(grid, d, t)

  def get_active_power_linear_charge(self, grid, d, t):
      return self.P_controller.pcontrol(grid, d, t)

  def get_active_power_trafo_charge(self, grid, d, t):
      return self.P_controller.get_q(grid, d, t, self.tan_phi)

  def get_reactive_power(self, grid, d, t):
      return self.P_controller.get_q(grid, d, t, self.tan_phi)

### Parent class HP_P-Controll ###
class HP_P_control:
  def __init__(self, grid):
      self.intervall_in_seconds = grid.time_scope['intervall_in_seconds']

  def pcontrol(self):
      pass

  def get_q(self, grid, d, t, tan_phi):
      return grid.net.load.loc[grid.hp_index, 'p_mw'] * tan_phi

### no HP ###
class HP_P_control_no_hp(HP_P_control):

  def __init__(self, grid):
      super().__init__(grid)

  def pcontrol(self, grid, d, t):
      HP_P_control.pcontrol(self)
      hp = grid.net.load.loc[grid.hp_index]
      hp.p_mw = 0
      return hp

### direct ###
class HP_P_control_direct(HP_P_control):

  def __init__(self, grid):
      super().__init__(grid)
      self.HP_storages = HPstorages()
      self.HP_storages.create_hp_storages(grid)

  def pcontrol(self, grid, d, t):
    
      '''
      ### Power an energy is measured in MW or MWh
      
      #residual_load positiv -> demand from grid
      #residual_load negativ -> feed into grid
      resi_load = grid.get_residualload_p_per_household() #array of float
      hp_soc_change = -resi_load * (self.intervall_in_seconds / 3600)
      hps = grid.net.load.loc[grid.hp_index]
      hp_el_demand = d.copy().values * (self.intervall_in_seconds / 3600)

      ### calculate amount of possible energy charge
      hp_soc_change[hp_soc_change > 0] = hp_soc_change[hp_soc_change > 0] - hp_el_demand[hp_soc_change > 0]
      ### calculate amount of possible energy discharge
      hp_soc_change[hp_soc_change <= 0] = -hp_el_demand[hp_soc_change <= 0]
      
      ### storage full
      #limit increase hp_soc untill [hp_soc + soc_change > hp_capacity]
      hp_soc_change[hps.hp_soc_kwh + hp_soc_change > hps.hp_el_capacity_kwh] = \
          hps.hp_el_capacity_kwh[hps.hp_soc_kwh + hp_soc_change > hps.hp_el_capacity_kwh] - \
            hps.hp_soc_kwh[hps.hp_soc_kwh + hp_soc_change > hps.hp_el_capacity_kwh]

      ### storage emtpy
      #decrease hp_soc untill [hp_soc + soc_change < 0]
      hp_soc_change[hps.hp_soc_kwh + hp_soc_change < 0] =\
          -hps.hp_soc_kwh[hps.hp_soc_kwh + hp_soc_change < 0]

      ### set power of hp additional the charge of storage
      hps.p_mw = (hp_el_demand + hp_soc_change) / (self.intervall_in_seconds / 3600)
      ### set soc of storage
      hps.hp_soc_kwh += hp_soc_change 
      
      grid.net.load.loc[grid.hp_index] = hps
      
      '''    
      hps = grid.net.load.loc[grid.hp_index]
      
      hp_el_demand = d.copy().values * (self.intervall_in_seconds / 3600)
      hps.p_mw = hp_el_demand / (self.intervall_in_seconds / 3600)
  
      return hps

### household-oriented_feed-in_damping ###
class HP_P_control_hh_fid(HP_P_control):

  def __init__(self, grid):
      #TODO
      print('Warning: HP household-oriented_feed-in_damping control is not well implemented')
      super().__init__(grid)
      self.HP_storages = HPstorages()
      self.HP_storages.create_hp_storages(grid)


  def pcontrol(self, grid, d, t):

      hp_el_demand = d.copy().values * (self.intervall_in_seconds / 3600)
      #residual_load positiv -> demand from grid
      #residual_load negativ -> feed into grid
      resi_load = grid.get_residualload_p_per_household() * (self.intervall_in_seconds / 3600) #array of float
      hp_soc_change_max = -resi_load - hp_el_demand
      hp_soc_change = hp_soc_change_max * 0
      hps = grid.net.load.loc[grid.hp_index]

      #get time information
      sunrise, sunset, timedelta_day_s, timedelta_sunrise_sunset_s = grid.get_timedelta(t)
      sunrise_next, sunset_next, timedelta_day_next_s, timedelta_sunrise_sunset_next_s = grid.get_timedelta(t + dt.timedelta(days = 1))

      print()
      print('######### Input #########')
      print(t, sunrise, sunset)
      print('timedelta_day_s: ',timedelta_day_s/3600)
      print('timedelta_sunrise_sunset_s: ',timedelta_sunrise_sunset_s/3600)
      print('resi_load: ',resi_load)
      print('hp_el_demand: ',hp_el_demand)
      print('hp_soc_change_max: ',hp_soc_change_max)

      time = t.tz_localize(None)

      ### calculate amount of possible energy charge (positiv hp_soc_change)
      #hp_soc_change[hp_soc_change > 0] = hp_soc_change[hp_soc_change > 0] - hp_el_demand[hp_soc_change > 0]
      ### calculate amount of possible energy discharge (negativ hp_soc_change)
      #hp_soc_change[hp_soc_change <= 0] = -hp_el_demand[hp_soc_change <= 0]

      #time of production
      if (time > sunrise and time < sunset):

        #calculate default linear charge
        p_mw_lin_ch = (hps.hp_el_capacity_mwh - hps.hp_soc_mwh) / (timedelta_day_s/3600)# mwh/h -> _s/3600
        print('charge: p_mw_lin_ch', p_mw_lin_ch.values)

        #charge with fid
        hp_soc_change[hp_soc_change_max > 0] = (p_mw_lin_ch[hp_soc_change_max > 0]) * (self.intervall_in_seconds / 3600)
        #limit hp_soc_change by hp_soc_change_max
        hp_soc_change[hp_soc_change > hp_soc_change_max] = hp_soc_change_max[hp_soc_change > hp_soc_change_max] 
        
        ### calculate amount of possible energy discharge
        hp_soc_change[hp_soc_change_max <= 0] = -hp_el_demand[hp_soc_change_max <= 0]

        print('hp_soc_change',hp_soc_change)

      #time of no production
      else:
        
        #calculate timedelta to next sunrise
        timedelta_nxt_sunrise_s = (sunrise_next - time).total_seconds()
        p_mw_lin_dch = (hps.hp_soc_mwh) / (timedelta_nxt_sunrise_s/3600)  # mwh/h -> _s/3600
        print('discharge: p_mw_lin_dch', p_mw_lin_dch.values)

        #set 
        #hp_soc_change[hp_soc_change <= 0] = -p_mw_lin_dch[hp_soc_change <= 0] * (self.intervall_in_seconds / 3600) #mwh -> mw * h
        hp_soc_change = -p_mw_lin_dch * (self.intervall_in_seconds / 3600) #mwh -> mw * h
        print('hp_soc_change', hp_soc_change.values)

        #hp_soc_change[hp_soc_change <= 0] = -hp_el_demand[hp_soc_change <= 0]

      ### storage full
      #limit increase hp_soc untill [hp_soc + soc_change > hp_capacity]
      hp_soc_change[hps.hp_soc_mwh + hp_soc_change > hps.hp_el_capacity_mwh] = \
          hps.hp_el_capacity_mwh[hps.hp_soc_mwh + hp_soc_change > hps.hp_el_capacity_mwh] - \
            hps.hp_soc_mwh[hps.hp_soc_mwh + hp_soc_change > hps.hp_el_capacity_mwh]

      ### storage emtpy
      #decrease hp_soc untill [hp_soc + soc_change < 0]
      hp_soc_change[hps.hp_soc_mwh + hp_soc_change < 0] =\
          -hps.hp_soc_mwh[hps.hp_soc_mwh + hp_soc_change < 0]

      ### set power of hp additional the charge of storage
      #hps.p_mw = (hp_el_demand + hp_soc_change) / (self.intervall_in_seconds / 3600)
      hps.p_mw = (hp_el_demand + hp_soc_change) / (self.intervall_in_seconds / 3600)
      ### set soc of storage
      hps.hp_soc_mwh += hp_soc_change

      print('hps.p_mw: ',hps.p_mw.values)

      grid.net.load.loc[grid.hp_index] = hps
      #HP_P_control.pcontrol(self)
      return grid.net.load.loc[grid.hp_index]

### grid-oriented_feed-in_damping ###
class HP_P_control_grid_fid(HP_P_control):

  def __init__(self, grid):
      #TODO
      print('Warning: HP grid-oriented_feed-in_damping control is not implemented')
      super().__init__(grid)

  def pcontrol(self, grid, d, t):
      HP_P_control.pcontrol(self)
      return d.values

### based EnWG $14a EVU-Lock  ###
class HP_P_control_evu_lock(HP_P_control):
  
    def __init__(self, grid):
        super().__init__(grid)
        self.HP_storages = HPstorages()
        self.HP_storages.create_hp_storages(grid)

    def pcontrol(self, grid, d, t):

        ### Power and energy is measured in MW or MWh
        
        #residual_load positiv -> demand from grid
        #residual_load negativ -> feed into grid
        resi_load = grid.get_residualload_p_per_household() #array of float
        #assign > hp_soc_change < per run with 0
        hp_soc_change = -resi_load * (self.intervall_in_seconds / 3600) * 0
        hps = grid.net.load.loc[grid.hp_index]
        hp_el_demand = d.copy().values * (self.intervall_in_seconds / 3600)
        evu_lock_active = False
        
        morningstart = dt.datetime(1970, 1, 1, 10, 45, 00)
        morningstop = dt.datetime(1970, 1, 1, 12, 15, 00)

        eveningstart = dt.datetime(1970, 1, 1, 17, 15, 00)
        eveningstop = dt.datetime(1970, 1, 1, 18, 45, 00)

        if((t.time() > morningstart.time()) & (t.time() < morningstop.time())) :
            evu_lock_active = True
        if((t.time() > eveningstart.time()) & (t.time() < eveningstop.time())) :
            evu_lock_active = True
        
        #set comfort_level to 
        comfort_soc = hps.hp_el_capacity_mwh * 0.7
        
        #when evu_lock active no demand from grid
        #feed_out from storage
        if(evu_lock_active) :
            #discharge storage based on demand
            hp_soc_change = -hp_el_demand
            
            #hp_el_demand[hps.hp_soc_mwh + hp_soc_change < 0] = hp_el_demand * 0
            
            hp_soc_change[hps.hp_soc_mwh + hp_soc_change < 0] =\
              -hps.hp_soc_mwh[hps.hp_soc_mwh + hp_soc_change < 0]
            
            

        #feed_in to storage until comfort_level
        #feed_in maximum 0.5kW
        if(evu_lock_active == False) :
            #set power to refill the storage
            hp_soc_change[hps.hp_soc_mwh < comfort_soc] = 0.0005 * (self.intervall_in_seconds / 3600)
            #limit soc -> fill untill comfort_level
            hp_soc_change[hps.hp_soc_mwh + hp_soc_change > comfort_soc] = \
              comfort_soc[hps.hp_soc_mwh + hp_soc_change > comfort_soc] - \
              hps.hp_soc_mwh[hps.hp_soc_mwh + hp_soc_change > comfort_soc]

        ### set power of hp additional the charge of storage
        hps.p_mw = (hp_el_demand + hp_soc_change) / (self.intervall_in_seconds / 3600)
        ### set soc of storage
        hps.hp_soc_mwh += hp_soc_change
        
        grid.net.load.loc[grid.hp_index] = hps

        #HP_P_control.pcontrol(self)

        return grid.net.load.loc[grid.hp_index]

### state of the art residual_load driven hp and storage ###
class HP_P_control_resi_load_driven(HP_P_control):

    def __init__(self, grid):
        super().__init__(grid)
        self.HP_storages = HPstorages()
        self.HP_storages.create_hp_storages(grid)

    def pcontrol(self, grid, d, t):

        ### Power and energy is measured in MW or MWh

        #residual_load positiv -> demand from grid
        #residual_load negativ -> feed into grid
        resi_load = grid.get_residualload_p_per_household() #array of float
        hp_soc_change = -resi_load * (self.intervall_in_seconds / 3600)
        hps = grid.net.load.loc[grid.hp_index]
        hp_el_demand = d.copy().values * (self.intervall_in_seconds / 3600)

        ### calculate amount of possible energy charge
        hp_soc_change[hp_soc_change > 0] = hp_soc_change[hp_soc_change > 0] - hp_el_demand[hp_soc_change > 0]
        ### calculate amount of possible energy discharge
        hp_soc_change[hp_soc_change <= 0] = -hp_el_demand[hp_soc_change <= 0]

        ### storage full
        #limit increase hp_soc untill [hp_soc + soc_change > hp_capacity]
        hp_soc_change[hps.hp_soc_mwh + hp_soc_change > hps.hp_el_capacity_mwh] = \
            hps.hp_el_capacity_mwh[hps.hp_soc_mwh + hp_soc_change > hps.hp_el_capacity_mwh] - \
              hps.hp_soc_mwh[hps.hp_soc_mwh + hp_soc_change > hps.hp_el_capacity_mwh]

        ### storage emtpy
        #decrease hp_soc untill [hp_soc + soc_change < 0]
        hp_soc_change[hps.hp_soc_mwh + hp_soc_change < 0] =\
            -hps.hp_soc_mwh[hps.hp_soc_mwh + hp_soc_change < 0]

        ### set power of hp additional the charge of storage
        hps.p_mw = (hp_el_demand + hp_soc_change) / (self.intervall_in_seconds / 3600)
        ### set soc of storage
        hps.hp_soc_mwh += hp_soc_change 

        grid.net.load.loc[grid.hp_index] = hps

        return grid.net.load.loc[grid.hp_index]
