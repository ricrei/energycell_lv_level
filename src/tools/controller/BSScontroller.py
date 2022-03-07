import numpy as np
import pandas as pd
import tools.tools as tt

import datetime
import pytz

class BSScontroller:

  def __init__(self, grid, control):      
      #Choice of temporal parameters and reserved soc for linear charge:
      self.timedelta_charging_delay = 0.125#2 #[h] Sommer 12 %
      self.timedelta_charging_delay_winter = 0.125#1 #[h] Versuch: %
      self.timedelta_early_discharge = 0.25#2 #[-]
      self.soc_reserve_percent = 20#20 #[%]
      
      self.intervall_in_seconds = grid.time_scope['intervall_in_seconds']
      self.busses_num = len(grid.component_buses.index)
      self.bss_num = len(grid.net.storage) #raus     
      self.efficiency_charge = grid.net.storage.efficiency_AC2Bat * grid.net.storage.efficiency_storage**0.5 
      self.efficiency_discharge = grid.net.storage.efficiency_Bat2AC * grid.net.storage.efficiency_storage**0.5

      self.control = control

      '''
      if (control=='direct'):
        self.control = control
      elif (control=='feed_in_damping'):
        self.control = control
      elif control == 'household-oriented_feed-in_damping':
        self.control = control
      elif control == 'grid-oriented_feed-in_damping':
        self.control = control
      else:
        raise ValueError('The entered BSS control is not a valid option.')
      '''

      if (self.control != None):
        if self.control == 'direct': 
          self.P_controller = BSS_control_direct(grid, \
                                                 self.intervall_in_seconds, \
                                                 self.busses_num, \
                                                 self.timedelta_charging_delay, \
                                                 self.timedelta_charging_delay_winter, \
                                                 self.timedelta_early_discharge, \
                                                 self.efficiency_charge, \
                                                 self.efficiency_discharge, \
                                                 self.soc_reserve_percent)
        elif self.control == 'household-oriented_feed-in_damping': 
          self.P_controller = BSS_P_control_hh_fid(grid, \
                                                 self.intervall_in_seconds, \
                                                 self.busses_num, \
                                                 self.timedelta_charging_delay, \
                                                 self.timedelta_charging_delay_winter, \
                                                 self.timedelta_early_discharge, \
                                                 self.efficiency_charge, \
                                                 self.efficiency_discharge, \
                                                 self.soc_reserve_percent)
              
        elif (self.control == 'grid-oriented_feed-in_damping_HH') or \
             (self.control == 'grid-oriented_feed-in_damping_LVbus') or \
             (self.control == 'grid-oriented_feed-in_damping_feeder'):
          self.P_controller = BSS_P_control_grid_fid(grid, \
                                                 self.intervall_in_seconds, \
                                                 self.busses_num, \
                                                 self.timedelta_charging_delay,\
                                                 self.timedelta_charging_delay_winter, \
                                                 self.timedelta_early_discharge, \
                                                 self.efficiency_charge, \
                                                 self.efficiency_discharge, \
                                                 self.soc_reserve_percent)
        elif self.control == ' ':
          raise ValueError('BSS control is not implemented.')
        elif self.control == ' ':
          raise ValueError('BSS control is not implemented.')
      else:
        self.P_controller = BSS_control_no_bss(grid, self.intervall_in_seconds, self.busses_num, self.timedelta_charging_delay, self.timedelta_charging_delay_winter, self.timedelta_early_discharge, self.efficiency_charge, self.efficiency_discharge, self.soc_reserve_percent)
  
  def get_active_power_direct_charge(self, grid, t):
      return self.P_controller.pcontrol_direct_charge(grid, t) 
  
  def get_active_power_linear_charge(self, grid, t):
      return self.P_controller.pcontrol_linear_charge(grid, t)
  
  def get_active_power_linear_charge_cbss(self, grid, t): # später raus
      return self.P_controller.pcontrol_linear_charge_cbss(grid, t)

  def get_active_power_trafo_charge(self, grid, t):
      return self.P_controller.pcontrol_trafo_charge(grid, t) #
  
  def get_e_mwh(self, grid):
      return self.P_controller.e_mwh_start
  
  def get_soc(self, grid):
      return self.P_controller.soc_new
 
# Parent
class BSS_control:
  def __init__(self, grid, intervall_in_seconds, bss_num, timedelta_charging_delay, timedelta_charging_delay_winter, timedelta_early_discharge, efficiency_charge, efficiency_discharge, soc_reserve_percent): 
      self.intervall = intervall_in_seconds#self.intervall_in_seconds #?????? neu 20.10
      self.bss_num = len(grid.net.storage)# bss_num
      #self.soc_new = self.soc_start  
      self.timedelta_charging_delay = timedelta_charging_delay
      self.timedelta_charging_delay_winter = timedelta_charging_delay_winter
      self.timedelta_early_discharge = timedelta_early_discharge
      self.efficiency_charge = efficiency_charge
      self.efficiency_discharge = efficiency_discharge
      self.soc_reserve_percent = soc_reserve_percent
      pass

  def pcontrol_direct_charge(self, grid, t):
      return grid.net.storage
  
  def pcontrol_linear_charge(self, grid, t):
      return grid.net.storage

  def pcontrol_trafo_charge(self, grid, t):
      return grid.net.storage

  def calculate_stored_energy(self, grid, p_mw_bss):
      """
      Calculation of the energy content of the BSS:
      For the discharging power the efficiency of the BSS and the inverter are
      considered. In order to meet the power demand more energy is taken from 
      the storage than used.
      Parameters
      ----------
      grid : TYPE
          network
      p_mw_bss : numpy.ndarray
          power change at bus due to BSS [MW]
      Returns
      -------
      e_mwh : pandas.Series
          energy content of the BSS [MWh]
      """
      e_mwh = grid.net.storage.e_mwh #self.e_mwh_start # [MWh] 
      p_mw_dch = np.copy(p_mw_bss)
      p_neg = np.less(p_mw_dch,np.zeros(self.bss_num))
      p_pos = np.greater(p_mw_dch,np.zeros(self.bss_num))
      p_mw_dch[p_neg] = p_mw_dch[p_neg] / self.efficiency_discharge[p_neg]
      p_mw_dch[p_pos] = p_mw_dch[p_pos] * self.efficiency_charge[p_pos]

      e_mwh = e_mwh + (p_mw_dch * self.intervall / 3600) # [MWh]

      return e_mwh

  def calculate_soc(self, grid, e_mwh):
      """    
      Calculation of the state of charge (SOC)
      
      Parameters
      ----------
      grid : TYPE
          network
      Returns
      -------
      soc : pandas.Series
          state of charge [%]
      """
      soc = (e_mwh / grid.net.storage.max_e_mwh) * 100 # [%]

      return soc

  
  def residual_load_per_bus(self, grid): # muss vielleicht für cbss bleiben
      residual_load_per_bus = grid.net.load.loc[grid.load_index, 'p_mw'].values + \
                              grid.net.load.loc[grid.hp_index, 'p_mw'].values + \
                              grid.net.load.loc[grid.ev_index, 'p_mw'].values - \
                              grid.net.sgen['p_mw'].values
      return residual_load_per_bus
  
  def direct_charge(self, grid, p_mw_bss): 

      get_soc = grid.net.storage.soc_percent #self.state_of_charge(grid)
      get_e_mwh = grid.net.storage.e_mwh #self.e_mwh_start
      
      free_capacity = grid.net.storage.max_e_mwh - get_e_mwh
      needed_capacity = p_mw_bss * self.intervall / 3600 

      solar_excess_1 = (p_mw_bss > 0) & \
                       (get_soc < 100) & \
                       (free_capacity < needed_capacity * self.efficiency_charge)

      solar_excess_2 = (p_mw_bss > 0) & \
                       (get_soc >= 100)

      load_excess_1 = (p_mw_bss < 0) & \
                      (get_soc > 0) & \
                      (get_e_mwh < -needed_capacity / self.efficiency_discharge)
                      
      load_excess_2 = (p_mw_bss < 0) & \
                      (get_soc <= 0)
                      
      # Excess in solar power:
      p_mw_bss[solar_excess_1] = free_capacity[solar_excess_1] * 3600 \
                                  / (self.intervall \
                                     * self.efficiency_charge[solar_excess_1])                                   
      p_mw_bss[solar_excess_2] = 0 
      
      # Excess in load: # später soc_min integrieren statt zeros ?
      p_mw_bss[load_excess_1] = - get_e_mwh[load_excess_1] \
                                  * self.efficiency_discharge[load_excess_1]  \
                                  * 3600 \
                                  / self.intervall
      p_mw_bss[load_excess_2] = 0

      return p_mw_bss
 
  def linear_charge(self, grid, t, p_mw_bss, get_e_mwh, free_capacity, timedelta_charging_delay, timedelta_charging_delay_winter, timedelta_early_discharge, soc_reserve_percent):
      
      #soc_reserve_percent = 20
      soc_reserve = soc_reserve_percent/100
      
      time = t.tz_localize(None)
      sunrise, sunset, timedelta_day_s, timedelta_sunrise_sunset_s = grid.get_timedelta(t) 
      sunrise_next, sunset_next, timedelta_day_next_s, timedelta_sunrise_sunset_next_s = grid.get_timedelta(t + datetime.timedelta(days = 1))
      
      timedelta_charging_delay_winter_h = timedelta_charging_delay_winter * timedelta_sunrise_sunset_s / 3600 #[h]
      timedelta_charging_delay_summer_h = timedelta_charging_delay * timedelta_sunrise_sunset_s / 3600 #[h]
      timedelta_early_discharge = timedelta_early_discharge * timedelta_sunrise_sunset_s / 3600 #[h]

      t_start_linear_charge_summer = sunrise + datetime.timedelta(hours = timedelta_charging_delay_summer_h)
      t_start_linear_charge_winter = sunrise + datetime.timedelta(hours = timedelta_charging_delay_winter_h)
      t_end_linear_charge_summer = sunset - datetime.timedelta(hours = timedelta_charging_delay_summer_h)
      t_end_linear_charge_winter = sunset - datetime.timedelta(hours = timedelta_charging_delay_winter_h)

      t_start_linear_discharge = sunset - datetime.timedelta(hours = self.timedelta_early_discharge)
      timedelta_lin_ch_summer_s = abs((t_end_linear_charge_summer - time).total_seconds())
      timedelta_lin_ch_winter_s = abs((t_end_linear_charge_winter - time).total_seconds())
      timedelta_lin_dch_day1_s = abs((sunrise_next - time).total_seconds())
      timedelta_lin_dch_day2_s = abs((sunrise - time).total_seconds())
      timedelta_lin_dch_winter_day_s = abs((t_start_linear_discharge - time).total_seconds())
      #print('timedelta_lin_ch_winter: ' + str(timedelta_lin_ch_winter_s))
      
      # Winter - Temporal parameters and discharge:
      if timedelta_sunrise_sunset_s < (12*3600):  #winter
      
          #charge:
          if time >= t_start_linear_charge_winter and time <= t_end_linear_charge_winter: 
              p_mw_lin_ch = (free_capacity * 3600)/ (timedelta_lin_ch_winter_s * self.efficiency_charge) 
          else:
              p_mw_lin_ch = np.zeros(len(grid.net.storage))
          
          #discharge
          if (sunrise - time).total_seconds() > 0: # nach Mitternacht vor Tagesanbruch
              timedelta_night_s = timedelta_lin_dch_day2_s
              if timedelta_night_s < self.intervall:  
                  timedelta_night_s = self.intervall  
          else: #vor Mitternacht
              timedelta_night_s = timedelta_lin_dch_day1_s
                  
          p_mw_lin_dch = -((get_e_mwh - soc_reserve * grid.net.storage.max_e_mwh) * self.efficiency_discharge * 3600)/ timedelta_night_s
          case_lin_dch = (p_mw_lin_dch > p_mw_bss) & (p_mw_bss < 0) & (get_e_mwh >= soc_reserve * grid.net.storage.max_e_mwh)
          case_lin_dch2 = (p_mw_bss < 0) & (get_e_mwh < soc_reserve * grid.net.storage.max_e_mwh)#<0 wichtig für Rechenfehler
          p_mw_bss[case_lin_dch] = p_mw_lin_dch[case_lin_dch]    
          p_mw_bss[case_lin_dch2] = 0
              
      # Summer - Temoral parameters
      else:
          if time >= t_start_linear_charge_summer and time <= t_end_linear_charge_summer: 
              p_mw_lin_ch = (free_capacity * 3600)/ (timedelta_lin_ch_summer_s * self.efficiency_charge)
          else:
              p_mw_lin_ch = np.zeros(len(grid.net.storage))
      
      # Linear charge in summer and winter:
      case_lin_ch = (p_mw_lin_ch < p_mw_bss) #& (p_mw_bss > 0)# 
      p_mw_bss[case_lin_ch] = p_mw_lin_ch[case_lin_ch] 

      return p_mw_bss

### no BSS ###
class BSS_control_no_bss(BSS_control):
  def __init__(self, grid, intervall_in_seconds, busses_num, timedelta_charging_delay, timedelta_charging_delay_winter, timedelta_early_discharge, efficiency_charge, efficiency_discharge, soc_reserve_percent):
      super().__init__(grid, intervall_in_seconds, busses_num, timedelta_charging_delay, timedelta_charging_delay_winter, timedelta_early_discharge, efficiency_charge, efficiency_discharge, soc_reserve_percent)

### DIRECT ###
class BSS_control_direct(BSS_control): #simple
  def __init__(self, grid, intervall_in_seconds, bss_num, timedelta_charging_delay, timedelta_charging_delay_winter, timedelta_early_discharge, efficiency_charge, efficiency_discharge, soc_reserve_percent): 
      super().__init__(grid, intervall_in_seconds, bss_num, timedelta_charging_delay, timedelta_charging_delay_winter, timedelta_early_discharge, efficiency_charge, efficiency_discharge, soc_reserve_percent)
      
  def pcontrol_direct_charge(self, grid, t): 
      '''
      Calculation of the change of residual laod caused by the BSS at each bus
      Parameters
      ----------
      grid : TYPE
          network
      Returns
      -------
      p_mw_bss : numpy.ndarray
          power change at bus due to BSS [MW]
      '''
      
      bss = grid.net.storage
      
      # Residual load at each household and resulting charging/discharging power:
      residual_load_per_bus = self.residual_load_per_bus(grid)
      p_mw_bss = -residual_load_per_bus      
     
      # Current parameters of BSS:  
      get_soc = bss.soc_percent #self.state_of_charge(grid) # state of charge [%]
      get_e_mwh = bss.e_mwh #self.e_mwh_start # energy content [MWh]
      
      # Write parameters of bss into dataframe:
      bss.e_mwh = get_e_mwh
      bss.soc_percent = get_soc

      # DIRECT CHARGE:        
      p_mw_bss = self.direct_charge(grid, p_mw_bss)
      
      # Limitation by maximum power: 
      p_mw_bss[bss.max_p_mw < p_mw_bss] = bss.max_p_mw[bss.max_p_mw < p_mw_bss]
      p_mw_bss[-bss.max_p_mw > p_mw_bss] = - bss.max_p_mw[-bss.max_p_mw > p_mw_bss]

      # Write parameters of bss into dataframe:
      bss.e_mwh = self.calculate_stored_energy(grid, p_mw_bss)
      bss.soc_percent = self.calculate_soc(grid, bss.e_mwh)
      bss.p_mw = p_mw_bss
      grid.net.storage = bss
      
      # New energy content of BSS:
      #grid = self.stored_energy(grid, p_mw_bss)
      
      return grid.net.storage


### FEED IN DAMPING ###

### household-oriented_feed-in_damping ###
class BSS_P_control_hh_fid(BSS_control):

  def __init__(self, grid, intervall_in_seconds, bss_num, timedelta_charging_delay,timedelta_charging_delay_winter, timedelta_early_discharge, efficiency_charge, efficiency_discharge, soc_reserve_percent):
      super().__init__(grid, intervall_in_seconds, bss_num, timedelta_charging_delay, timedelta_charging_delay_winter, timedelta_early_discharge, efficiency_charge, efficiency_discharge, soc_reserve_percent)

  def pcontrol_linear_charge(self, grid, t):
      
      bss = grid.net.storage
      
      p_mw_bss = - self.residual_load_per_bus(grid) 
      
      # Current parameters of BSS:
      get_soc = bss.soc_percent #self.state_of_charge(grid)
      get_e_mwh = bss.e_mwh #self.e_mwh_start  
      
      # Write parameters of bss into dataframe:
      bss.e_mwh = get_e_mwh
      bss.soc_percent = get_soc
      
      free_capacity = grid.net.storage.max_e_mwh - get_e_mwh
      
      # DIRECT CHARGE:        
      p_mw_bss = self.direct_charge(grid, p_mw_bss)
  
      #LINEAR CHARGING:     
      p_mw_bss = self.linear_charge(grid, t, p_mw_bss, get_e_mwh, free_capacity, self.timedelta_charging_delay, self.timedelta_charging_delay_winter, self.timedelta_early_discharge, self.soc_reserve_percent)
      
      # Limitation by maximum power:
      p_mw_bss[bss.max_p_mw < p_mw_bss] = bss.max_p_mw[bss.max_p_mw < p_mw_bss]
      p_mw_bss[-bss.max_p_mw > p_mw_bss] = - bss.max_p_mw[-bss.max_p_mw > p_mw_bss]
      
      # Write parameters of bss into dataframe:
      bss.e_mwh = self.calculate_stored_energy(grid, p_mw_bss)
      bss.soc_percent = self.calculate_soc(grid, bss.e_mwh)
      bss.p_mw = p_mw_bss
      grid.net.storage = bss
      
      # calculate new energy content:
      #grid = self.stored_energy(grid, p_mw_bss) 
      
      return grid.net.storage


### grid-oriented_feed-in_damping ###
class BSS_P_control_grid_fid(BSS_control):
  def __init__(self, grid, intervall_in_seconds, busses_num, timedelta_charging_delay, timedelta_charging_delay_winter, timedelta_early_discharge, efficiency_charge, efficiency_discharge, soc_reserve_percent): 
      super().__init__(grid, intervall_in_seconds, busses_num, timedelta_charging_delay, timedelta_charging_delay_winter, timedelta_early_discharge, efficiency_charge, efficiency_discharge, soc_reserve_percent)
      
      #self.trafo_sn_mva = grid.net.trafo.sn_mva.sum() # oder grid.s_trafo_power ()ist das gleiche
  
  def pcontrol_linear_charge(self, grid, t): #pcontrol_linear_charge_cbss
  
      bss = grid.net.storage
      s_res, p_res = grid.get_residualload_s_sum()
      p_mw_bss_total = - p_res
        
      # Current parameters of BSS:             
      get_soc = bss.soc_percent #self.state_of_charge(grid)
      get_e_mwh = bss.e_mwh #self.e_mwh_start    
      free_capacity = grid.net.storage.max_e_mwh - get_e_mwh
      
      # Distribution of residual load over storages: 
      if free_capacity.sum() <= 0:
          distribution_factor_ch = np.zeros(len(bss))
      else:
          distribution_factor_ch = free_capacity/free_capacity.sum()
          distribution_factor_ch = distribution_factor_ch.fillna(0)
      '''
      distribution_factor_ch = free_capacity / free_capacity.sum()
      distribution_factor_ch = distribution_factor_ch.fillna(0) # befüllt alle inf, -inf bzw NaN mit 0   
      '''

      get_e_mwh[get_e_mwh<0]= 0
      distribution_factor_dch = get_e_mwh / get_e_mwh.sum()
      distribution_factor_dch = distribution_factor_dch.fillna(0) # befüllt alle inf, -inf bzw NaN mit 0 

      if p_mw_bss_total >= 0: 
          p_mw_bss = (p_mw_bss_total * distribution_factor_ch) 

      elif p_mw_bss_total < 0:
          p_mw_bss = (p_mw_bss_total * distribution_factor_dch) #* np.ones(bss_num)

      #DIRECT CHARGING:
      p_mw_bss = self.direct_charge(grid, p_mw_bss)
      
      #LINEAR CHARGING AND DISCHARGING:
      p_mw_bss = self.linear_charge(grid, t, p_mw_bss, get_e_mwh, free_capacity, self.timedelta_charging_delay, self.timedelta_charging_delay_winter, self.timedelta_early_discharge, self.soc_reserve_percent)
       
      # Limitation by maximum power:     
      p_mw_bss[bss.max_p_mw < p_mw_bss] = bss.max_p_mw[bss.max_p_mw < p_mw_bss]
      p_mw_bss[-bss.max_p_mw > p_mw_bss] = - bss.max_p_mw[-bss.max_p_mw > p_mw_bss]
      
      # Write parameters of bss into dataframe: (Das sind die Parameter am Anfang des aktuellen Zeitstempels --> nicht in fid überschreiben)
      bss.e_mwh = self.calculate_stored_energy(grid, p_mw_bss)
      bss.soc_percent = self.calculate_soc(grid, bss.e_mwh)
      bss.p_mw = p_mw_bss
      grid.net.storage = bss
      
      # calculate new energy content:
      #grid = self.stored_energy(grid, p_mw_bss)    

      return grid.net.storage  
   
  def pcontrol_trafo_charge(self, grid, t): #pcontrol(self, grid, t): #t
  
      bss = grid.net.storage

      p_mw_bss = bss.p_mw
     
      # Current parameters of BSS:
      get_e_mwh = bss.e_mwh #self.e_mwh_start
      get_e_mwh[get_e_mwh <0] =0 ###? nochmal überlegen und vielleicht mit Ricardo besprechen
      get_soc = bss.soc_percent #self.state_of_charge(grid)
   
      free_capacity = grid.net.storage.max_e_mwh - get_e_mwh 

      #FEED-IN AND LOAD DAMPING:               
      s_res, p_res = grid.get_residualload_s_sum() 
      p_res = -p_res 

      if grid.s_trafo_power < -s_res: # Fall Trafoüberlastung bei Solarüberschuss
          q_res_to_the_power_of_2 = s_res**2 - p_res**2
          if q_res_to_the_power_of_2 < grid.s_trafo_power**2: 
              p_trafo_max = (grid.s_trafo_power**2 - q_res_to_the_power_of_2)**(.5)
          else:
              p_trafo_max = 0  
  
          p_total_bss = p_res - p_trafo_max
         
          # damping:
          if free_capacity.sum() == 0.0:
              damping_faktor = np.zeros(len(bss)) 
          else:
              damping_faktor = free_capacity / (free_capacity.sum())
              damping_faktor = damping_faktor.fillna(0)
              
          p_mw_damped = damping_faktor * p_total_bss
         
          needed_capacity = p_mw_damped * self.intervall / 3600 # oder needed_capacity = p_mw_damped + p_mw_bss / ... ? nein
          
          solar_excess_fid_1 = (get_soc < 100) & \
                               (needed_capacity * self.efficiency_charge <= free_capacity)
          solar_excess_fid_2 = (get_soc < 100) & \
                               (needed_capacity * self.efficiency_charge > free_capacity)
          solar_test = (get_soc <= 0)
          
          p_mw_damped[solar_excess_fid_2] = free_capacity[solar_excess_fid_2] * 3600 \
                                         / (self.intervall * self.efficiency_charge[solar_excess_fid_2])
          p_mw_damped[solar_test] = 0

      elif grid.s_trafo_power < s_res: # Fall Trafoüberlastung bei Netzbezug
          
          # Calculate Trafo Overload:
          q_res_to_the_power_of_2 = s_res**2 - p_res**2
          if q_res_to_the_power_of_2 < grid.s_trafo_power**2: 
              p_trafo_max = (grid.s_trafo_power**2 - q_res_to_the_power_of_2)**(.5)
          else:
              p_trafo_max = 0 
              
          p_total_bss = p_res + p_trafo_max
                 
          # load damping:
          get_e_mwh[get_e_mwh <0] = 0
          damping_factor = get_e_mwh / get_e_mwh.sum()
          damping_factor = damping_factor.fillna(0) # befüllt alle inf, -inf bzw NaN mit 0 

          p_mw_damped = damping_factor * p_total_bss       
          needed_capacity = - p_mw_damped * self.intervall / 3600 # oder needed_capacity = p_mw_damped + p_mw_bss / ... ? nein
            
          load_excess_fid_2 = (get_soc > 0) & \
                               (get_e_mwh < needed_capacity / self.efficiency_discharge)
          load_test = (get_soc <= 0)

          p_mw_damped[load_excess_fid_2] = -(get_e_mwh[load_excess_fid_2] * 3600 * self.efficiency_discharge[load_excess_fid_2] \
                                         / self.intervall)
          p_mw_damped[load_test] = 0

      else: 
          p_mw_damped = np.zeros(len(grid.net.storage))
      
      # Calculate new charging or discharging power:
      p_mw_bss = p_mw_bss + p_mw_damped
      
      # Limitation by maximum power:     
      p_mw_bss[bss.max_p_mw < p_mw_bss] = bss.max_p_mw[bss.max_p_mw < p_mw_bss]
      p_mw_bss[-bss.max_p_mw > p_mw_bss] = - bss.max_p_mw[-bss.max_p_mw > p_mw_bss]
      
      # Write parameters of bss into dataframe:
      # e_mwh und soc werden nur zu Angang eines Zeitspempels an df übergeben (hier bereits in lin getan)
      # eine weitere Übergabe würdie Daten verfälschen
  
      # calculate new energy content:
      p_mw_stored = p_mw_bss - bss.p_mw # - p_mw_bss_copy statt - bss.p_mw
      #grid_helper = self.stored_energy(grid, p_mw_stored) 
      #get_e_mwh = grid_helper.net.storage.e_mwh

      # Write parameters of bss into dataframe:
      bss.e_mwh = self.calculate_stored_energy(grid, p_mw_stored)
      bss.soc_percent = self.calculate_soc(grid, bss.e_mwh)
      bss.p_mw = p_mw_bss   # darf hier erst nach get_e_mwh stehen!
      grid.net.storage = bss
      #grid.net.storage.e_mwh = get_e_mwh

      return grid.net.storage


