import numpy as np
import pandas as pd
import tools.tools as tt

import datetime
import pytz

class BSScontroller:

  def __init__(self, grid, control):
      self.set_bss = (grid.scenario[0] in [6, 8])
      self.intervall_in_seconds = grid.time_scope['intervall_in_seconds']
      self.busses_num = len(grid.component_buses.index)
      self.bss_num = len(grid.net.storage) #raus

      if (control=='direct'): #simple
        self.control = control
      elif (control=='feed_in_damping'):
        self.control = control
      elif control == 'household-oriented_feed-in_damping':
        self.control = control#'simple'
        #raise ValueError('household-oriented_feed-in_damping control is not implemented.')
      elif control == 'grid-oriented_feed-in_damping':
        self.control = control#'simple'
        #raise ValueError('grid-oriented_feed-in_damping control is not implemented.')
      else:
        raise ValueError('The entered BSS control is not a valid option.')

      if self.set_bss == True:
        if self.control == 'direct': #simple
          self.P_controller = BSS_control_direct(grid, \
                                                 self.intervall_in_seconds, \
                                                 self.busses_num)
        elif self.control == 'household-oriented_feed-in_damping': # 'feed_in_damping'  #BSS_control_feed_in_damping
          self.P_controller = BSS_P_control_hh_fid(grid, \
                                                 self.intervall_in_seconds, \
                                                 self.busses_num)
              
        elif self.control == 'grid-oriented_feed-in_damping':
          self.P_controller = BSS_P_control_grid_fid(grid, \
                                                 self.intervall_in_seconds, \
                                                 self.busses_num)
        elif self.control == ' ':
          raise ValueError('BSS control is not implemented.')
        elif self.control == ' ':
          raise ValueError('BSS control is not implemented.')
      else:
        self.P_controller = BSS_control_no_bss(grid, self.intervall_in_seconds, self.busses_num)

  #def get_active_power(self, grid, t): #t
      #return self.P_controller.pcontrol(grid, t) #t
  
  def get_active_power_direct_charge(self, grid, t):
      return self.P_controller.pcontrol_direct_charge(grid, t) 
  
  def get_active_power_linear_charge(self, grid, t):
      return self.P_controller.pcontrol_linear_charge(grid, t)
  
  def get_active_power_linear_charge_cbss(self, grid, t): # später raus
      return self.P_controller.pcontrol_linear_charge_cbss(grid, t)
  ###
  def get_active_power_trafo_charge(self, grid, t):
      return self.P_controller.pcontrol_trafo_charge(grid, t) #
  
  def get_e_mwh(self, grid):
      return self.P_controller.e_mwh_start
  
  def get_soc(self, grid):
      return self.P_controller.soc_new
 
# Parent
class BSS_control:
  def __init__(self, grid, intervall_in_seconds, bss_num): 
      self.intervall = intervall_in_seconds
      self.bss_num = len(grid.net.storage)# bss_num
      self.soc_start = grid.net.storage.soc_percent 
      self.e_mwh_start = self.soc_start/100 * grid.net.storage.max_e_mwh 
      self.soc_new = self.soc_start  
      pass

  #def pcontrol(self, grid, t):#???
      #return grid.net.storage#???
  '''  
  def get_active_power_direct_charge(self, grid, t):
      return grid.net.storage
  
  def get_active_power_linear_charge(self, grid, t):
      return grid.net.storage
  
  def get_active_power_trafo_charge(self, grid, t):
      return grid.net.storage
  '''  
  def pcontrol_direct_charge(self, grid, t):
      #BSS_control.pcontrol(self, grid, t)
      return grid.net.storage
  
  def pcontrol_linear_charge(self, grid, t):
      #BSS_control.pcontrol(self, grid, t)
      return grid.net.storage

  def pcontrol_trafo_charge(self, grid, t):
      #BSS_control.pcontrol(self, grid, t)
      return grid.net.storage
  
  def state_of_charge(self, grid): 
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
      soc = (self.e_mwh_start / grid.net.storage.max_e_mwh) * 100 # [%]
      return soc
 
  def stored_energy(self, grid, p_mw_bss):
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
      e_mwh = self.e_mwh_start # [MWh]
      p_mw_dch = np.copy(p_mw_bss)
      p_neg = np.less(p_mw_dch,np.zeros(self.bss_num))
      p_mw_dch[p_neg] = p_mw_dch[p_neg] \
                          / (grid.net.storage.efficiency_storage[p_neg] \
                             * grid.net.storage.efficiency_inverter[p_neg])
      
      self.e_mwh_start = e_mwh + (p_mw_dch * self.intervall / 3600) # [MWh] nicht intervall in seconds?
      return e_mwh

  # Ricardo:
  def get_solar_load_excess(self, grid):

      p_mw_bss = -grid.get_residualload_p_per_household() # evtl ersetzen

      get_soc=self.state_of_charge(grid)
      self.soc_new = get_soc

      get_e_mwh=self.e_mwh_start
      
      free_capacity = grid.net.storage.max_e_mwh - get_e_mwh

      needed_capacity = p_mw_bss * self.intervall / 3600
     # needed_capacity = (p_mw_bss/(grid.net.storage.efficiency_storage * grid.net.storage.efficiency_inverter)) * self.intervall / 3600

      solar_excess_1 = (p_mw_bss > 0) & \
                       (get_soc < 100) & \
                       (free_capacity < needed_capacity)

      solar_excess_2 = (p_mw_bss > 0) & \
                       (get_soc >= 100)

      load_excess_1 = (p_mw_bss < 0) & \
                      (get_soc > 0) & \
                      (get_e_mwh < -needed_capacity/(grid.net.storage.efficiency_storage * grid.net.storage.efficiency_inverter))
                      #(get_e_mwh < -needed_capacity)
                      
      load_excess_2 = (p_mw_bss < 0) & \
                      (get_soc <= 0)

      return solar_excess_1, solar_excess_2, load_excess_1, load_excess_2
  
  def residual_load_per_bus(self, grid): # muss vielleicht für cbss bleiben
      residual_load_per_bus = grid.net.load.loc[grid.load_index, 'p_mw'].values + \
                              grid.net.load.loc[grid.hp_index, 'p_mw'].values + \
                              grid.net.load.loc[grid.ev_index, 'p_mw'].values - \
                              grid.net.sgen['p_mw'].values
      return residual_load_per_bus

  '''
  def get_solar_load_excess(self, grid):
      
      p_mw_bss = -grid.get_residualload_p_per_household()

      get_soc=self.state_of_charge(grid)
      self.soc_new = get_soc
           
      get_e_mwh=self.e_mwh_start
     
      free_capacity = grid.net.storage.max_e_mwh - get_e_mwh

      needed_capacity = p_mw_bss * self.intervall / 3600

      solar_excess_1 = (p_mw_bss > 0) & \
                       (get_soc < 100) & \
                       (free_capacity < needed_capacity)

      solar_excess_2 = (p_mw_bss > 0) & \
                       (get_soc >= 100)

      load_excess_1 = (p_mw_bss < 0) & \
                      (get_soc > 0) & \
                      (get_e_mwh < -needed_capacity/(grid.net.storage.efficiency_storage * grid.net.storage.efficiency_inverter))

      load_excess_2 = (p_mw_bss < 0) & \
                      (get_soc <= 0)

      return solar_excess_1, solar_excess_2, load_excess_1, load_excess_2
  '''
  
  def get_solar_load_excess_cbss(self, grid):

      s_res, p_res = grid.get_residualload_s_sum()
      p_mw_bss_total = - p_res
      
     # p_mw_bss_hh = -self.residual_load_per_bus(grid)  #grid.get_residualload_p_per_household()
     # p_mw_bss_total = p_mw_bss_hh.sum()

      get_soc=self.state_of_charge(grid)
      self.soc_new = get_soc
           
      get_e_mwh=self.e_mwh_start
     
      free_capacity = grid.net.storage.max_e_mwh - get_e_mwh
      
      # Distribution of residual load over CBSS: 
      bss_num = len(grid.net.storage) 
      
      if free_capacity.sum() == 0:
          distribution_factor_ch = np.zeros(bss_num)
      else:
          distribution_factor_ch = free_capacity/free_capacity.sum()
          distribution_factor_ch = distribution_factor_ch.fillna(0)
      '''
      distribution_factor_ch = free_capacity / free_capacity.sum()
      distribution_factor_ch = distribution_factor_ch.fillna(0) # befüllt alle inf, -inf bzw NaN mit 0   
      '''
      distribution_factor_dch = get_e_mwh / get_e_mwh.sum()
      distribution_factor_dch = distribution_factor_dch.fillna(0) # befüllt alle inf, -inf bzw NaN mit 0 
      
      if p_mw_bss_total > 0:
          p_mw_bss = (p_mw_bss_total * distribution_factor_ch) * np.ones(bss_num)
      
      elif p_mw_bss_total < 0:
          p_mw_bss = (p_mw_bss_total * distribution_factor_dch) * np.ones(bss_num)
      
      needed_capacity = p_mw_bss * self.intervall / 3600 #

      solar_excess_1 = (p_mw_bss > 0) & \
                       (get_soc < 100) & \
                       (free_capacity < needed_capacity)

      solar_excess_2 = (p_mw_bss > 0) & \
                       (get_soc >= 100)

      load_excess_1 = (p_mw_bss < 0) & \
                      (get_soc > 0) & \
                      (get_e_mwh < -needed_capacity/(grid.net.storage.efficiency_storage * grid.net.storage.efficiency_inverter))

      load_excess_2 = (p_mw_bss < 0) & \
                      (get_soc <= 0)

      return solar_excess_1, solar_excess_2, load_excess_1, load_excess_2

class BSS_control_no_bss(BSS_control):
  def __init__(self, grid, intervall_in_seconds, busses_num):
      super().__init__(grid, intervall_in_seconds, busses_num)

### DIRECT ###
class BSS_control_direct(BSS_control): #simple
  def __init__(self, grid, intervall_in_seconds, bss_num): 
      super().__init__(grid, intervall_in_seconds, bss_num)
      
  def pcontrol_direct_charge(self, grid, t): 
  #def pcontrol(self, grid, t):
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
      
      #BSS_control.pcontrol(self, grid, t) #warum wird eigtl pcontrol aufgerufen?
      bss = grid.net.storage
      
      # Residual load at each bus and resulting charging/discharging power:
      residual_load_per_bus = grid.net.load.loc[grid.load_index, 'p_mw'].values + \
                              grid.net.load.loc[grid.hp_index, 'p_mw'].values + \
                              grid.net.load.loc[grid.ev_index, 'p_mw'].values - \
                              grid.net.sgen['p_mw'].values                           
      p_mw_bss = -residual_load_per_bus      
     
      # Current parameters of BSS:  
      get_soc=self.state_of_charge(grid) # state of charge [%]    
      self.soc_new = get_soc # soc to dataframe ?
      bss.soc_percent = get_soc    
      get_e_mwh=self.e_mwh_start # energy content [MWh]
      bss.e_mwh = get_e_mwh
      free_capacity = grid.net.storage.max_e_mwh - get_e_mwh # difference between surrent and maximum energy content [MWh]
      needed_capacity = p_mw_bss * self.intervall / 3600 # 

      # Test cases for determination of charging/discharging power:
      solar_excess_1, solar_excess_2, load_excess_1, load_excess_2 = \
          self.get_solar_load_excess(grid) 
        
      # Excess in solar power:
      p_mw_bss[solar_excess_1] = free_capacity[solar_excess_1] * 3600 \
                                  / self.intervall
      p_mw_bss[solar_excess_2] = 0 
      
      # Excess in load: # später soc_min integrieren statt zeros ?
      p_mw_bss[load_excess_1] = - get_e_mwh[load_excess_1] \
                                  * grid.net.storage.efficiency_storage[load_excess_1]  \
                                  * grid.net.storage.efficiency_inverter[load_excess_1] \
                                  * 3600 \
                                  / self.intervall
      p_mw_bss[load_excess_2] = 0
      
      # Limitation by maximum power: 
      p_mw_bss[bss.max_p_mw < p_mw_bss] = bss.max_p_mw[bss.max_p_mw < p_mw_bss]
      p_mw_bss[-bss.max_p_mw > p_mw_bss] = - bss.max_p_mw[-bss.max_p_mw > p_mw_bss]
          
      # New energy content of BSS:
      get_e_mwh = self.stored_energy(grid, p_mw_bss) 

      ###grid.net.storage['soc_percent'] = bss_controller.get_soc(grid)
      bss.p_mw = p_mw_bss
      
      grid.net.storage = bss
      return grid.net.storage


### FEED IN DAMPING ###

### household-oriented_feed-in_damping ###
class BSS_P_control_hh_fid(BSS_control):

  def __init__(self, grid, intervall_in_seconds, bss_num):
      #TODO
      #print('Warning: BSS household-oriented_feed-in_damping control is not implemented.')
      super().__init__(grid, intervall_in_seconds, bss_num)
      
      self.trafo_sn_mva = grid.net.trafo.sn_mva.sum()

  def pcontrol_linear_charge(self, grid, t):
      #BSS_control.pcontrol(self, grid, t)
      #BSS_P_control.pcontrol(self)
      bss = grid.net.storage
      
      p_mw_bss = - self.residual_load_per_bus(grid) 
      
      # Current parameters of BSS:
      get_soc=self.state_of_charge(grid)
      self.soc_new = get_soc
      bss.soc_percent = get_soc 
      get_e_mwh = self.e_mwh_start  
      bss.e_mwh = get_e_mwh
      #get_e_mwh[get_e_mwh < 0] = 0 # sollte eigtl Rechenfehler abfangen
      free_capacity = grid.net.storage.max_e_mwh - get_e_mwh
      
      #LINEAR CHARGING:
      
      # Temporal parameters:
      sunrise, sunset, timedelta_day_s, timedelta_sunrise_sunset_s = grid.get_timedelta(t) 
      sunrise_next, sunset_next, timedelta_day_next_s, timedelta_sunrise_sunset_next_s = grid.get_timedelta(t + datetime.timedelta(days = 1))       
      t = t.tz_localize(None)
      timedelta_night_d1_s = abs((sunrise_next - t).total_seconds())
      timedelta_night_d2_s = abs((sunrise - t).total_seconds())

      # power and test cases for linear charging and discharging: 
      p_mw_lin_ch = (free_capacity * 3600)/ timedelta_day_s # hier läuft was verkehrt!!!
      #get_e_mwh = get_e_mwh.fillna(0) # alterntive für negative Werte
      #p_mw_lin_dch_night = -(get_e_mwh * 3600)/ timedelta_night_s # kann später raus
      case_lin_ch = (p_mw_lin_ch < p_mw_bss) #& (p_mw_bss > 0)# 
      #case_lin_dch = (p_mw_lin_dch > p_mw_bss) & (p_mw_bss < 0) # <0 wichtig für Rechenfehler # rausnehmen
             
      # test cases for solar excess and load excess:
      solar_excess_1, solar_excess_2, load_excess_1, load_excess_2 = \
          self.get_solar_load_excess(grid)    

      # Excess in solar power:(wie bei simple)
      p_mw_bss[solar_excess_1] = free_capacity[solar_excess_1] * 3600 \
                                  / self.intervall
      p_mw_bss[solar_excess_2] = 0 

      # Excess in load:(wie bei simple) # später soc_min integrieren statt zeros
      p_mw_bss[load_excess_1] = - get_e_mwh[load_excess_1] \
                                  * grid.net.storage.efficiency_storage[load_excess_1]  \
                                  * grid.net.storage.efficiency_inverter[load_excess_1] \
                                  * 3600 \
                                  / self.intervall
      p_mw_bss[load_excess_2] = 0
      
      # Linear charging and discharging:
      p_mw_bss[case_lin_ch] = p_mw_lin_ch[case_lin_ch]
      
      time = t.tz_localize(None)
      if time <= sunrise or time >= sunset:
          if timedelta_sunrise_sunset_s < (12*3600):
              if (sunset - t).total_seconds() > 0: # nach Mitternacht
                  timedelta_night_s = timedelta_night_d2_s
              else: #vor Mitternacht
                  timedelta_night_s = timedelta_night_d1_s   
              p_mw_lin_dch = -(get_e_mwh * 3600)/ timedelta_night_s
              case_lin_dch = (p_mw_lin_dch > p_mw_bss) & (p_mw_bss < 0)
              p_mw_bss[case_lin_dch] = p_mw_lin_dch[case_lin_dch]                
     
      # Limitation by maximum power:
      p_mw_bss[bss.max_p_mw < p_mw_bss] = bss.max_p_mw[bss.max_p_mw < p_mw_bss]
      p_mw_bss[-bss.max_p_mw > p_mw_bss] = - bss.max_p_mw[-bss.max_p_mw > p_mw_bss]
      
      bss.p_mw = p_mw_bss
      grid.net.storage = bss
      
      # calculate new energy content:
      get_e_mwh = self.stored_energy(grid, p_mw_bss) 
      
      return grid.net.storage


### grid-oriented_feed-in_damping ###
class BSS_P_control_grid_fid(BSS_control):
  def __init__(self, grid, intervall_in_seconds, busses_num): 
      super().__init__(grid, intervall_in_seconds, busses_num)
      
      self.trafo_sn_mva = grid.net.trafo.sn_mva.sum() # oder grid.s_trafo_power ()ist das gleiche
    
  def pcontrol_linear_charge(self, grid, t): #pcontrol_linear_charge_cbss
      
      bss = grid.net.storage
      
      s_res, p_res = grid.get_residualload_s_sum()
      p_mw_bss_total = - p_res 
      
      # Current parameters of BSS:             
      get_soc=self.state_of_charge(grid)
      self.soc_new = get_soc
      bss.soc_percent = get_soc 
      get_e_mwh = self.e_mwh_start  

      free_capacity = grid.net.storage.max_e_mwh - get_e_mwh  
      
      # Distribution of residual load over CBSS: muss auch in solar_load_excess() !!!     
      if free_capacity.sum() == 0.0:
          distribution_factor_ch = np.zeros(len(bss)) 
      else:
          distribution_factor_ch = free_capacity/free_capacity.sum()
          distribution_factor_ch = distribution_factor_ch.fillna(0)
      
      '''
      #alt:
      distribution_factor_ch = free_capacity / free_capacity.sum()
      #print('type distribution factor: ' + str(type(distribution_factor_ch)))
      distribution_factor_ch = distribution_factor_ch.fillna(0) # befüllt alle inf, -inf bzw NaN mit 0 auch gür HBSS!!!
      '''
      '''
      distribution_factor_ch = (free_capacity.divide(free_capacity.sum()))#.replace(np.inf, 0)
      distribution_factor_ch = distribution_factor_ch.fillna(0)
      '''
      
      distribution_factor_dch = get_e_mwh / get_e_mwh.sum()
      distribution_factor_dch = distribution_factor_dch.fillna(0) # befüllt alle inf, -inf bzw NaN mit 0 
      distribution_factor_dch [distribution_factor_dch < 0] = 0 
      
      if p_mw_bss_total >= 0: # 0 muss auch noch abgefangen werden!!!
          p_mw_bss = (p_mw_bss_total * distribution_factor_ch) #* np.ones(bss_num)
      
      elif p_mw_bss_total < 0:
          p_mw_bss = (p_mw_bss_total * distribution_factor_dch) #* np.ones(bss_num)
      
      # needed capacity:
      needed_capacity = p_mw_bss * self.intervall / 3600 #
      
      #DIRECT CHARGING:
      
      # Temporal parameters:    
      sunrise, sunset, timedelta_day_s, timedelta_sunrise_sunset_s = grid.get_timedelta(t) 
      sunrise_next, sunset_next, timedelta_day_next_s, timedelta_sunrise_sunset_next_s = grid.get_timedelta(t + datetime.timedelta(days = 1))       
      t = t.tz_localize(None)
      timedelta_night_d1_s = abs((sunrise_next - t).total_seconds())
      timedelta_night_d2_s = abs((sunrise - t).total_seconds())
      
      # test cases for solar excess and load excess:
      solar_excess_1, solar_excess_2, load_excess_1, load_excess_2 = \
          self.get_solar_load_excess_cbss(grid) 
      
      
      # Excess in solar power:(wie bei simple)
      p_mw_bss[solar_excess_1] = free_capacity[solar_excess_1] * 3600 \
                                  / self.intervall
      p_mw_bss[solar_excess_2] = 0 

      # Excess in load:(wie bei simple) # später soc_min integrieren statt zeros
      p_mw_bss[load_excess_1] = - get_e_mwh[load_excess_1] \
                                  * grid.net.storage.efficiency_storage[load_excess_1]  \
                                  * grid.net.storage.efficiency_inverter[load_excess_1] \
                                  * 3600 \
                                  / self.intervall
      p_mw_bss[load_excess_2] = 0
      
      
      #LINEAR CHARGING AND DISCHARGING:
          
      # power and test cases for linear charging and discharging:              
      p_mw_lin_ch = (free_capacity * 3600)/ timedelta_day_s 
      #p_mw_lin_dch = p_mw_lin_dch.fillna(0) # evtl garnicht benötigt
      case_lin_ch = (p_mw_lin_ch < p_mw_bss)
      #case_lin_dch = (p_mw_lin_dch > p_mw_bss) #nochmal testen

      # Adjustment of power to linear charging:
      p_mw_bss[case_lin_ch] = p_mw_lin_ch[case_lin_ch]

     # Adjustment of power to linear discharging:
      time = t.tz_localize(None)
      if time <= sunrise or time >= sunset:
          if timedelta_sunrise_sunset_s < (12*3600):
              if (sunset - t).total_seconds() > 0: # nach Mitternacht
                  timedelta_night_s = timedelta_night_d2_s
              else: #vor Mitternacht
                  timedelta_night_s = timedelta_night_d1_s   
              p_mw_lin_dch = -(get_e_mwh * 3600)/ timedelta_night_s

              case_lin_dch = (p_mw_lin_dch > p_mw_bss) & (p_mw_bss < 0)
              p_mw_bss[case_lin_dch] = p_mw_lin_dch[case_lin_dch]
              
      # Limitation by maximum power:     neu
      p_mw_bss[bss.max_p_mw < p_mw_bss] = bss.max_p_mw[bss.max_p_mw < p_mw_bss]
      p_mw_bss[-bss.max_p_mw > p_mw_bss] = - bss.max_p_mw[-bss.max_p_mw > p_mw_bss]
      
      bss.p_mw = p_mw_bss
      grid.net.storage = bss
      
      # calculate new energy content:
      get_e_mwh = self.stored_energy(grid, p_mw_bss)
          
      return grid.net.storage
   
  def pcontrol_trafo_charge(self, grid, t): #pcontrol(self, grid, t): #t
  
      bss = grid.net.storage

      p_mw_bss = bss.p_mw
      p_mw_bss_copy = np.copy(p_mw_bss)
     
      # Current parameters of BSS:
      get_soc = self.state_of_charge(grid)
      get_e_mwh = self.e_mwh_start 
      free_capacity = grid.net.storage.max_e_mwh - get_e_mwh 

      #FEED-IN DAMPING:
               
      #-----------------ev
      s_res, p_res = grid.get_residualload_s_sum() #residual_load_trafo_s_mva
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
              damping_faktor = np.zeros(len(bss)) # np.zeros[len()]
          else:
              damping_faktor = free_capacity / (free_capacity.sum())
              damping_faktor = damping_faktor.fillna(0)
              
          ''' #alt:
          damping_faktor = free_capacity / (free_capacity.sum())
          damping_faktor = damping_faktor.fillna(0)
          '''
          p_mw_damped = damping_faktor * p_total_bss
         
          needed_capacity = p_mw_damped * self.intervall / 3600 # oder needed_capacity = p_mw_damped + p_mw_bss / ... ? nein
         
          solar_excess_fid_1 = (get_soc < 100) & \
                      (needed_capacity <= free_capacity)
          solar_excess_fid_2 = (get_soc < 100) & \
                      (needed_capacity > free_capacity)
          solar_test = (get_soc <= 0)

          p_mw_damped[solar_excess_fid_2] = (free_capacity[solar_excess_fid_2] * 3600 \
                                         / self.intervall)
          p_mw_damped[solar_test] = 0
          
      elif grid.s_trafo_power < s_res: # Fall Trafoüberlastung bei Netzbezug
          q_res_to_the_power_of_2 = s_res**2 - p_res**2
          if q_res_to_the_power_of_2 < grid.s_trafo_power**2: 
              p_trafo_max = (grid.s_trafo_power**2 - q_res_to_the_power_of_2)**(.5)
          else:
              p_trafo_max = 0
          p_total_bss = p_res + p_trafo_max

         
          # damping:
          if free_capacity.sum() == 0.0:
              damping_faktor = np.zeros(len(bss)) # np.zeros[len()]
          else:
              damping_faktor = free_capacity / (free_capacity.sum())
              damping_faktor = damping_faktor.fillna(0)
              
          ''' #alt:
          damping_faktor = free_capacity / (free_capacity.sum())
          damping_faktor = damping_faktor.fillna(0)
          '''
          p_mw_damped = damping_faktor * p_total_bss
         
          needed_capacity = p_mw_damped * self.intervall / 3600 # oder needed_capacity = p_mw_damped + p_mw_bss / ... ? nein
         
          solar_excess_fid_1 = (get_soc < 100) & \
                      (needed_capacity <= free_capacity)
          solar_excess_fid_2 = (get_soc < 100) & \
                      (needed_capacity > free_capacity)
          solar_test = (get_soc <= 0)

          p_mw_damped[solar_excess_fid_2] = (free_capacity[solar_excess_fid_2] * 3600 \
                                         / self.intervall)
          p_mw_damped[solar_test] = 0

      else: 
          p_mw_damped = np.zeros(len(grid.net.storage))

      '''    
      #--------alt-----------------------------------------
      p_mw_bss = p_mw_bss + p_mw_damped
      bss.p_mw = p_mw_bss
      grid.net.storage = bss    
      
      # calculate new energy content:
      get_e_mwh = self.stored_energy(grid, p_mw_damped)
       
      #----------------------------------------------------
      ''' 
      #---------------neu----------------------------------
      p_mw_bss = p_mw_bss + p_mw_damped
      
      # Limitation by maximum power:     
      p_mw_bss[bss.max_p_mw < p_mw_bss] = bss.max_p_mw[bss.max_p_mw < p_mw_bss]
      p_mw_bss[-bss.max_p_mw > p_mw_bss] = - bss.max_p_mw[-bss.max_p_mw > p_mw_bss]
      bss.p_mw = p_mw_bss
      
      grid.net.storage = bss    
  
      # calculate new energy content:
      p_mw_stored = p_mw_bss - p_mw_bss_copy#bss.p_mw
      get_e_mwh = self.stored_energy(grid, p_mw_stored) 
      #----------------------------------------------------
         
      #bss.p_mw = p_mw_bss # darf hier erst nach get_e_mwh stehen!
      return grid.net.storage


