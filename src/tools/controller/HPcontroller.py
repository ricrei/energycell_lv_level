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
      return self.P_controller.pcontrol_direct_charge(grid, d, t)

  def get_active_power_linear_charge(self, grid, d, t):
      return self.P_controller.pcontrol_linear_charge(grid, d, t)

  def get_active_power_trafo_charge(self, grid, d, t):
      return self.P_controller.pcontrol_trafo_charge(grid, d, t)

  def get_reactive_power(self, grid, d, t):
      return self.P_controller.get_q(grid, d, t, self.tan_phi)

### Parent class HP_P-Controll ###
class HP_P_control:
  def __init__(self, grid):
      self.intervall_in_seconds = grid.time_scope['intervall_in_seconds']
      self.HP_storages = HPstorages(grid)
      self.HP_storages.create_hp_storages(grid)

  def pcontrol(self):
      pass
    
  def pcontrol_direct_charge(self, grid, d, t):
      grid.net.load['hp_demand_th'].loc[grid.hp_index] = d.values
      return grid.net.load.loc[grid.hp_index] 

  def pcontrol_linear_charge(self, grid, d, t):
      return grid.net.load.loc[grid.hp_index] 
  
  def pcontrol_trafo_charge(self, grid, d, t):
      return grid.net.load.loc[grid.hp_index]

  def get_q(self, grid, d, t, tan_phi):
      return grid.net.load.loc[grid.hp_index, 'p_mw'] * tan_phi
    
  def get_cop(self, grid, d, t):
      hps = grid.net.load.loc[grid.hp_index]
      #set current ambient temprature locate by timestamp t
      t_source = grid.df_t_amb.loc[t].ta
      #set static sink-temprature und calc delta_T
      t_sink = 45     ###buidling-side
      delta_T = t_sink - t_source
      #calc cop for air-sourced HPs
      hps.hp_cop[hps.type.str.contains('Air')] = \
        6.81 - 0.121 * delta_T + 0.00063 * delta_T**2
      #calc cop for ground-sourced HPs
      hps.hp_cop[hps.type.str.contains('Ground')] = \
        8.77 - 0.15 * delta_T + 0.000734 * delta_T**2
        
      ### -> Optimierung bei Init ermittelte 
      ### Werte in den df d für hp_th_demand und cop
      return hps

  def write_th_data_to_df(self, hps, hp_soc_change):
      hps['hp_hp_th'] = hps.p_mw * hps.hp_cop
      hps['hp_tes_th'] = hp_soc_change / (self.intervall_in_seconds / 3600)
      return hps

### no HP ###
class HP_P_control_no_hp(HP_P_control):

  def __init__(self, grid):
      super().__init__(grid)

  def pcontrol(self, grid, d, t):
      HP_P_control.pcontrol(self)
      hps = grid.net.load.loc[grid.hp_index]
      hps.p_mw = 0
      # write thermal output/input power of HP and TES to hps
      hps = self.write_th_data_to_df(hps, hp_soc_change=0)
      return hps

### direct ###
class HP_P_control_direct(HP_P_control):

  def __init__(self, grid):
      super().__init__(grid)

  def pcontrol_direct_charge(self, grid, d, t):
      super().pcontrol_direct_charge(grid, d, t)
      #get hps with current cop per hp      
      hps = self.get_cop(grid, d, t)
      hps.p_mw = d.copy().values / hps.hp_cop
      # write thermal output/input power of HP and TES to hps
      hps = self.write_th_data_to_df(hps, hp_soc_change=0)
      return hps
  

### household-oriented_feed-in_damping ###
class HP_P_control_hh_fid(HP_P_control):

  def __init__(self, grid):
      super().__init__(grid)
            
  def pcontrol_linear_charge(self, grid, d, t):
      
      #self.HP_storages.hp_stor_para['hp_loss_per_s']
      
      #get thermal demand from timeseries
      hp_th_demand = d.copy().values * (self.intervall_in_seconds / 3600)
      #residual_load positiv -> demand from grid
      #residual_load negativ -> feed into grid
      resi_load = grid.get_residualload_p_per_household() * (self.intervall_in_seconds / 3600) #array of float
      
      #get hps with current cop per hp due t_ambient
      hps = self.get_cop(grid, d, t)
      #set loss in storage
      hps = self.HP_storages.set_loss(hps)
      
      #set value for max-change and initiate hp_soc_change
      hp_soc_change_max = -resi_load * hps.hp_cop - hp_th_demand
      hp_soc_change = hp_soc_change_max * 0

      #get time information
      sunrise, sunset, timedelta_day_s, timedelta_sunrise_sunset_s = grid.get_timedelta(t)
      sunrise_next, sunset_next, timedelta_day_next_s, timedelta_sunrise_sunset_next_s = grid.get_timedelta(t + dt.timedelta(days = 1))
      time = t.tz_localize(None)

      #### time of production
      if (time > sunrise and time < sunset):

        #calculate default linear charge
        p_mw_lin_ch = (hps.hp_max_capacity_mwh - hps.hp_soc_mwh) / (timedelta_day_s/3600) #mwh/h -> _s/3600

        #set charge with fid in case of feed_in
        hp_soc_change[resi_load < 0] = (p_mw_lin_ch[resi_load < 0]) * (self.intervall_in_seconds / 3600)
        #limit hp_soc_change by hp_soc_change_max
        hp_soc_change[hp_soc_change > hp_soc_change_max] = hp_soc_change_max[hp_soc_change > hp_soc_change_max]

        ### calculate amount of possible energy discharge
        hp_soc_change[resi_load >= 0] = -hp_th_demand[resi_load >= 0]

      #### time of no production
      else:
        
        ### handle with new next sunrise pre / post midnight
        # post midnight
        if (sunrise - time).total_seconds() > 0:  
          timedelta_nxt_sunrise_s = (sunrise - time).total_seconds()
        # pre midnight
        else:
          timedelta_nxt_sunrise_s = (sunrise_next - time).total_seconds()

        #calculate timedelta to next sunrise
        #timedelta_nxt_sunrise_s = (sunrise_next - time).total_seconds()
        p_mw_lin_dch = (hps.hp_soc_mwh) / (timedelta_nxt_sunrise_s/3600)  # mwh/h -> _s/3600

        #set discharge with fid
        hp_soc_change = -p_mw_lin_dch * (self.intervall_in_seconds / 3600) #mwh -> mw * h
        #limit hp_soc_change to hp_el_demand -> no feed_in of hot water to grid..
        hp_soc_change[hp_soc_change + hp_th_demand <= 0] = -hp_th_demand[hp_soc_change + hp_th_demand <= 0]

      ### limit to maximum or minimum of capacity
      hps = self.HP_storages.set_limits(hps, hp_soc_change)
      
      #convert soc_change to additonal el_load
      th_soc_to_el_p = hp_soc_change / hps.hp_cop
      hp_el_demand = hp_th_demand / hps.hp_cop 
      ### set power of hp additional the charge of storage
      hps.p_mw = (hp_el_demand + th_soc_to_el_p) / (self.intervall_in_seconds / 3600)
      ### set soc of storage
      hps.hp_soc_mwh += hp_soc_change
      # write thermal output/input power of HP and TES to hps
      hps = self.write_th_data_to_df(hps, hp_soc_change)

      return hps

### grid-oriented_feed-in_damping ###
class HP_P_control_grid_fid(HP_P_control):

  def __init__(self, grid):
      super().__init__(grid)
      self.hps_capacity_backup_factor = 1.0
      

  def pcontrol_trafo_charge(self, grid, d, t):
      
      #get thermal demand from timeseries
      hp_th_demand = d.copy().values * (self.intervall_in_seconds / 3600)
      #residual_load positiv -> demand from grid
      #residual_load negativ -> feed into grid
      resi_load = grid.get_residualload_p_per_household() * (self.intervall_in_seconds / 3600) #array of float
      #s, resi_load = grid.get_residualload_s_sum() * (self.intervall_in_seconds / 3600) #array of float

      #get hps with current cop per hp due t_ambient
      hps = self.get_cop(grid, d, t)
      #set loss in storage
      hps = self.HP_storages.set_loss(hps)

      #set value for max-change and initiate hp_soc_change
      hp_soc_change_max = -resi_load * hps.hp_cop - hp_th_demand
      hp_soc_change = hp_soc_change_max * 0

      #get time information
      sunrise, sunset, timedelta_day_s, timedelta_sunrise_sunset_s = grid.get_timedelta(t)
      sunrise_next, sunset_next, timedelta_day_next_s, timedelta_sunrise_sunset_next_s = grid.get_timedelta(t + dt.timedelta(days = 1))
      time = t.tz_localize(None)

      ### Ricky's Routine zur Signalisierung Trafoüberlastung
      s_res, p_res = grid.get_residualload_s_sum()
      p_res = -p_res
      
      ### if s_trafo less than feed_in from PV
      if grid.s_trafo_power < -s_res:
          # calculate q²
          q_res_to_the_power_of_2 = s_res**2 - p_res**2
          # if q_trafo² less than s_trafo²
          if q_res_to_the_power_of_2 < grid.s_trafo_power**2:
            # calculate p_trafo_max due to q_residual²
            p_trafo_max = (grid.s_trafo_power**2 - q_res_to_the_power_of_2)**(.5)
          else:
            # otherwise set p_trafo_max to zero
            p_trafo_max = 0
      else:
          # set p_trafo_max to p_residual
          p_trafo_max = p_res
      
      p_total_hp = p_res - p_trafo_max


      #### time of production
      if (time > sunrise and time < sunset):
        
        #calculate free capacitiy exclusive trafo_charge_backup_capacity
        if grid.s_trafo_power > -s_res:
          #calculate default linear charge with backup factor due to trafo charge
          p_mw_lin_ch = ((hps.hp_max_capacity_mwh * self.hps_capacity_backup_factor) - hps.hp_soc_mwh) / (timedelta_day_s/3600)# mwh/h -> _s/3600
          
          #avoid negative p_mw_lin_ch values (can exist if soc > capacity * backup_factor)
          p_mw_lin_ch[p_mw_lin_ch < 0] = 0 
          #set charge with fid
          hp_soc_change[resi_load < 0] = (p_mw_lin_ch[resi_load < 0]) * (self.intervall_in_seconds / 3600)
          #limit hp_soc_change by hp_soc_change_max
          hp_soc_change[hp_soc_change > hp_soc_change_max] = hp_soc_change_max[hp_soc_change > hp_soc_change_max]

        else:
          # distribute power equal to every HP
          p_mw_trafo_ch = (hps.hp_soc_mwh * 0) + (p_total_hp / hps.shape[0]) * hps.hp_cop
          #set hp_soc_change by 
          hp_soc_change = p_mw_trafo_ch * (self.intervall_in_seconds / 3600)
          #limit hp_soc_change by hp_soc_change_max
          hp_soc_change[hp_soc_change > hp_soc_change_max] = hp_soc_change_max[hp_soc_change > hp_soc_change_max]

        ### calculate amount of possible energy discharge
        hp_soc_change[resi_load >= 0] = -hp_th_demand[resi_load >= 0]

      #### time of no production
      else:
        
        ### handle with new next sunrise pre / post midnight
        # post midnight
        if (sunrise - time).total_seconds() > 0:  
          timedelta_nxt_sunrise_s = (sunrise - time).total_seconds()
        # pre midnight
        else:
          timedelta_nxt_sunrise_s = (sunrise_next - time).total_seconds()

        #calculate timedelta to next sunrise
        #timedelta_nxt_sunrise_s = (sunrise_next - time).total_seconds()
        p_mw_lin_dch = (hps.hp_soc_mwh) / (timedelta_nxt_sunrise_s/3600)  # mwh/h -> _s/3600
        #print('discharge: p_mw_lin_dch', p_mw_lin_dch.values)

        #set discharge with fid
        hp_soc_change = -p_mw_lin_dch * (self.intervall_in_seconds / 3600) #mwh -> mw * h
        #limit hp_soc_change to hp_th_demand -> no feed_in of hot water to grid..
        hp_soc_change[hp_soc_change + hp_th_demand <= 0] = -hp_th_demand[hp_soc_change + hp_th_demand <= 0]

      ### limit to maximum or minimum of capacity
      self.HP_storages.set_limits(hps, hp_soc_change)
      
      #convert soc_change to additonal el_load
      th_soc_to_el_p = hp_soc_change / hps.hp_cop
      hp_el_demand = hp_th_demand / hps.hp_cop 
      ### set power of hp additional the charge of storage
      hps.p_mw = (hp_el_demand + th_soc_to_el_p) / (self.intervall_in_seconds / 3600)
      ### set soc of storage
      hps.hp_soc_mwh += hp_soc_change
      # write thermal output/input power of HP and TES to hps
      hps = self.write_th_data_to_df(hps, hp_soc_change)

      return hps

### based EnWG $14a EVU-Lock  ###
class HP_P_control_evu_lock(HP_P_control):
  
    def __init__(self, grid):
        super().__init__(grid)

    def pcontrol_direct_charge(self, grid, d, t):
        super().pcontrol_direct_charge(grid, d, t)
        ### Power and energy is measured in MW or MWh
        
        #residual_load positiv -> demand from grid
        #residual_load negativ -> feed into grid
        resi_load = grid.get_residualload_p_per_household() #array of float
        #assign > hp_soc_change < per run with 0
        hp_soc_change = -resi_load * (self.intervall_in_seconds / 3600) * 0
        hps = grid.net.load.loc[grid.hp_index]
        evu_lock_active = False
        
        #get hps with current cop per hp and calc th, el demand
        hps = self.get_cop(grid, d, t)
        #set loss in storage
        hps = self.HP_storages.set_loss(hps)
        
        hp_th_demand = d.copy().values * (self.intervall_in_seconds / 3600) 
        hp_el_demand = hp_th_demand / hps.hp_cop
        
        morningstart = dt.datetime(1970, 1, 1, 10, 45, 00)
        morningstop = dt.datetime(1970, 1, 1, 12, 15, 00)

        eveningstart = dt.datetime(1970, 1, 1, 17, 15, 00)
        eveningstop = dt.datetime(1970, 1, 1, 18, 45, 00)

        if((t.time() > morningstart.time()) & (t.time() < morningstop.time())) :
            evu_lock_active = True
        if((t.time() > eveningstart.time()) & (t.time() < eveningstop.time())) :
            evu_lock_active = True
        
        #set comfort_level to 
        comfort_soc = hps.hp_max_capacity_mwh * 0.7
        
        #when evu_lock active no demand from grid
        #feed_out from storage
        if(evu_lock_active) :
            #discharge storage based on demand
            hp_soc_change = -hp_th_demand
            #limit soc if storage empty
            hp_soc_change[hps.hp_soc_mwh + hp_soc_change < 0] =\
              -hps.hp_soc_mwh[hps.hp_soc_mwh + hp_soc_change < 0]
            
        #feed_in to storage until comfort_level
        #feed_in maximum 0.7kW_th
        if(evu_lock_active == False) :
            #set power to refill the storage
            hp_soc_change[hps.hp_soc_mwh < comfort_soc] = 0.0006 * (self.intervall_in_seconds / 3600)
            #limit soc -> fill untill comfort_level
            hp_soc_change[hps.hp_soc_mwh + hp_soc_change > comfort_soc] = \
              comfort_soc[hps.hp_soc_mwh + hp_soc_change > comfort_soc] - \
              hps.hp_soc_mwh[hps.hp_soc_mwh + hp_soc_change > comfort_soc]
        
        additional_el_demand = hp_soc_change / hps.hp_cop
        ### set power of hp additional the charge of storage
        hps.p_mw = (hp_el_demand + additional_el_demand) / (self.intervall_in_seconds / 3600)
        ### set soc of storage
        hps.hp_soc_mwh += hp_soc_change
        # write thermal output/input power of HP and TES to hps
        hps = self.write_th_data_to_df(hps, hp_soc_change)
        
        #grid.net.load.loc[grid.hp_index] = hps
        #HP_P_control.pcontrol(self)
        #return grid.net.load.loc[grid.hp_index]
        return hps

### state of the art residual_load driven hp and storage ###
class HP_P_control_resi_load_driven(HP_P_control):

    def __init__(self, grid):
        super().__init__(grid)

    def pcontrol_direct_charge(self, grid, d, t):
        super().pcontrol_direct_charge(grid, d, t)
        ### Power and energy is measured in MW or MWh
        #residual_load positiv -> demand from grid
        #residual_load negativ -> feed into grid
        #normalized to 1h
        resi_load = grid.get_residualload_p_per_household() \
          * (self.intervall_in_seconds / 3600)

        #get hps with current cop per hp due t_ambient
        hps = self.get_cop(grid, d, t)
        #set loss in storage
        hps = self.HP_storages.set_loss(hps)
        
        # get thermal demand from timeseries normalized to 1h
        hp_th_demand = d.copy().values * (self.intervall_in_seconds / 3600) 

        #set with el surplus/demand possible amount of th_energy to storage
        hp_soc_change = -resi_load * hps.hp_cop 

        ### calculate amount of possible energy charge
        hp_soc_change[hp_soc_change > 0] = hp_soc_change[hp_soc_change > 0] - hp_th_demand[hp_soc_change > 0]
        ### calculate amount of possible energy discharge
        hp_soc_change[hp_soc_change <= 0] = -hp_th_demand[hp_soc_change <= 0]
        ### limit to maximum or minimum of capacity
        self.HP_storages.set_limits(hps, hp_soc_change)

        #convert soc_change to additonal el_load
        th_soc_to_el_p = hp_soc_change / hps.hp_cop
        hp_el_demand = hp_th_demand / hps.hp_cop 
        ### set power of hp additional the charge of storage
        hps.p_mw = (hp_el_demand + th_soc_to_el_p) / (self.intervall_in_seconds / 3600)
        ### set soc of storage
        hps.hp_soc_mwh += hp_soc_change
        # write thermal output/input power of HP and TES to hps
        hps = self.write_th_data_to_df(hps, hp_soc_change)

        return hps
