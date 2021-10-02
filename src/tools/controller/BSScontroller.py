import numpy as np
import pandas as pd
import tools.tools as tt

import datetime
import pytz

class BSScontroller:

  def __init__(self, grid, control):
      self.set_bss = (grid.scenario[0] in [6,8])

      #self.intervall=pd.to_timedelta(time_scope['t_freq']) # converts offset alias to time_delta object
      #self.intervall_in_seconds = self.intervall.total_seconds() # converts time_delta object to time in seconds
      self.intervall_in_seconds = grid.time_scope['intervall_in_seconds']
      #self.sunrise = grid.time_scope['time solar'].sunrise
      self.busses_num = len(grid.component_buses.index)
      self.bss_num = len(grid.net.storage) #raus

      if (control=='simple'):
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
        if self.control == 'simple':
          self.P_controller = BSS_control_simple(grid, \
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

  def pcontrol(self, grid, t):#???
      return grid.net.storage#???
  
  def get_active_power_direct_charge(self, grid, t):
      return grid.net.storage
  
  def get_active_power_linear_charge(self, grid, t):
      return grid.net.storage
  
  def get_active_power_trafo_charge(self, grid, t):
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
  
  def power_simple(self, grid, p_mw_bss, get_e_mwh, get_soc):
      '''
      get_soc=self.state_of_charge(grid)
      #get_soc=get_soc.fillna(0) # befüllt alle inf, -inf bzw NaN mit 0
      self.soc_new = get_soc # wofür wird das nochmal gebraucht?
            
      get_e_mwh=self.e_mwh_start
      '''
      free_capacity = grid.net.storage.max_e_mwh - get_e_mwh
      needed_capacity = p_mw_bss * self.intervall / 3600
      
      # test cases
      solar_excess_1 = np.greater(p_mw_bss,np.zeros(self.busses_num)) & \
                       np.less(get_soc,np.ones(self.busses_num)*100) & \
                       np.less(free_capacity, needed_capacity)
      solar_excess_2 = np.greater(p_mw_bss,np.zeros(self.busses_num)) & \
                       np.greater_equal(get_soc,np.ones(self.busses_num)*100)

      load_excess_1 = np.less(p_mw_bss,np.zeros(self.busses_num)) & \
                      np.greater(get_soc,np.zeros(self.busses_num)) & \
                      np.less(get_e_mwh,-needed_capacity \
                              / (grid.net.storage.efficiency_storage \
                                * grid.net.storage.efficiency_inverter))
      load_excess_2 = np.less(p_mw_bss,np.zeros(self.busses_num)) & \
                      np.less_equal(get_soc,np.zeros(self.busses_num))
      
      # Excess in solar power:
      p_mw_bss[solar_excess_1] = free_capacity[solar_excess_1] * 3600 \
                                  / self.intervall
      p_mw_bss[solar_excess_2] = 0 
      
      # Excess in load: # später soc_min integrieren statt zeros
      p_mw_bss[load_excess_1] = - get_e_mwh[load_excess_1] \
                                  * grid.net.storage.efficiency_storage[load_excess_1]  \
                                  * grid.net.storage.efficiency_inverter[load_excess_1] \
                                  * 3600 \
                                  / self.intervall
      p_mw_bss[load_excess_2] = 0

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

  def pcontrol_direct_charge(self, grid, t):
      BSS_control.pcontrol(self, grid, t)
      return grid.net.storage
  
  def pcontrol_linear_charge(self, grid, t):
      BSS_control.pcontrol(self, grid, t)
      return grid.net.storage

  def pcontrol_trafo_charge(self, grid, t):
      BSS_control.pcontrol(self, grid, t)
      return grid.net.storage

### SIMPLE ###
class BSS_control_simple(BSS_control): 
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
      
      BSS_control.pcontrol(self, grid, t) #warum wird eigtl pcontrol aufgerufen?
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
      print('e_mwh:' + str(bss.e_mwh))
      ###grid.net.storage['soc_percent'] = bss_controller.get_soc(grid)
      bss.p_mw = p_mw_bss
      
      grid.net.storage = bss
      return grid.net.storage
  
  def pcontrol_linear_charge(self, grid, t):
      BSS_control.pcontrol(self, grid, t)
      return grid.net.storage
 
  def pcontrol_trafo_charge(self, grid, t):
      BSS_control.pcontrol(self, grid, t)
      return grid.net.storage


### FEED IN DAMPING ###
class BSS_P_control_grid_fid2(BSS_control):#BSS_control_feed_in_damping(BSS_control): 
  def __init__(self, grid, intervall_in_seconds, busses_num): 
      super().__init__(grid, intervall_in_seconds, busses_num)
      
      self.trafo_sn_mva = grid.net.trafo.sn_mva.sum() # .sum()?
      self.trafo_load_percent = grid.net.res_trafo.loading_percent
  

  def pcontrol(self, grid, t):

        #case trafo overload grid supply (richtig rum?)
     # c_trafo_ol_gs = np.greater(-residual_load_trafo_s_mva, self.trafo_sn_mva) #case: trafo overload grid supply
     # c_trafo_ol_fi = np.greater(residual_load_trafo_s_mva, self.trafo_sn_mva)#case: trafo overload feed-in
      
     ### p_mw_bss[c_trafo_ol_fi] = (diff_trafo * np.ones(self.busses_num))[c_trafo_ol_fi]
     ### p_mw_bss[c_trafo_ol_fi] = (diff_trafo * np.ones(self.busses_num))[c_trafo_ol_fi] p_mw_bss[c_trafo_ol_gs] = (diff_trafo * np.ones(self.busses_num))[c_trafo_ol_gs]
      
      if (-residual_load_trafo_s_mva[0] > self.trafo_sn_mva) :
          
          needed_capacity = p_mw_bss * self.intervall / 3600
      
      # test cases
          solar_excess_1 = np.greater(p_mw_bss,np.zeros(self.busses_num)) & \
                       np.less(get_soc,np.ones(self.busses_num)*100) & \
                       np.less(free_capacity, needed_capacity)
          solar_excess_2 = np.greater(p_mw_bss,np.zeros(self.busses_num)) & \
                       np.greater_equal(get_soc,np.ones(self.busses_num)*100)

          load_excess_1 = np.less(p_mw_bss,np.zeros(self.busses_num)) & \
                      np.greater(get_soc,np.zeros(self.busses_num)) & \
                      np.less(get_e_mwh,-needed_capacity \
                              / (grid.net.storage.efficiency_storage \
                                * grid.net.storage.efficiency_inverter))
          load_excess_2 = np.less(p_mw_bss,np.zeros(self.busses_num)) & \
                      np.less_equal(get_soc,np.zeros(self.busses_num))  
          
          p_mw_bss[solar_excess_1] = free_capacity[solar_excess_1] * 3600 \
                                  / self.intervall
          p_mw_bss[solar_excess_2] = 0 
         # p_mw_bss = (diff_trafo * np.ones(self.busses_num))/200
      #if (res_s > self.trafo_power*self.sf_load): dieser Fall muss noch beprochen werden
      
      #self.define_scenarios(grid, p_mw_bss) #?

     # print(type(residual_load_trafo_s_mva))
     # print(type(self.trafo_sn_mva))
      #print((residual_load_trafo_s_mva > self.trafo_sn_mva).item())
      
      #if residual_load_trafo_s_mva > self.trafo_sn_mva:
         # print('Überlastung')
      else: #LINEAR CHARGING
          #linear charging:  
          daylight_s = 12*3600 #nur bis sunrise und sunset umgesetzt
          p_mw_lin = (grid.net.storage.max_e_mwh * 3600)/ daylight_s #Cannot divide float64 data by TimedeltaArray

          case_lin = np.less(p_mw_lin, p_mw_bss) # & Scheinliestung kleiner Scheinleistung_nenn
          needed_capacity = p_mw_bss * self.intervall / 3600
          p_mw_bss[case_lin] = p_mw_lin[case_lin]
          needed_capacity_lin = p_mw_bss * self.intervall / 3600
          
          solar_excess_1 = np.greater(p_mw_bss,np.zeros(self.busses_num)) & \
                       np.less(get_soc,np.ones(self.busses_num)*100) & \
                       np.less(free_capacity, needed_capacity_lin)
          solar_excess_2 = np.greater(p_mw_bss,np.zeros(self.busses_num)) & \
                       np.greater_equal(get_soc,np.ones(self.busses_num)*100)

          load_excess_1 = np.less(p_mw_bss,np.zeros(self.busses_num)) & \
                      np.greater(get_soc,np.zeros(self.busses_num)) & \
                      np.less(get_e_mwh,-needed_capacity \
                              / (grid.net.storage.efficiency_storage \
                                * grid.net.storage.efficiency_inverter))
          load_excess_2 = np.less(p_mw_bss,np.zeros(self.busses_num)) & \
                      np.less_equal(get_soc,np.zeros(self.busses_num))  
            
          # Excess in solar power:
          p_mw_bss[solar_excess_1] = free_capacity[solar_excess_1] * 3600 \
                                  / self.intervall
          p_mw_bss[solar_excess_2] = 0 
      
          # Excess in load: # später soc_min integrieren statt zeros
          p_mw_bss[load_excess_1] = - get_e_mwh[load_excess_1] \
                                  * grid.net.storage.efficiency_storage[load_excess_1]  \
                                  * grid.net.storage.efficiency_inverter[load_excess_1] \
                                  * 3600 \
                                  / self.intervall
          p_mw_bss[load_excess_2] = 0


      
      return p_mw_bss

### household-oriented_feed-in_damping ###
class BSS_P_control_hh_fid(BSS_control):

  def __init__(self, grid, intervall_in_seconds, bss_num):
      #TODO
      #print('Warning: BSS household-oriented_feed-in_damping control is not implemented.')
      super().__init__(grid, intervall_in_seconds, bss_num)
      
      self.trafo_sn_mva = grid.net.trafo.sn_mva.sum()
      
  def pcontrol_direct_charge(self, grid, t):
      BSS_control.pcontrol(self, grid, t)
      return grid.net.storage

  #def pcontrol(self, grid, t): #d?
  def pcontrol_linear_charge(self, grid, t):
      BSS_control.pcontrol(self, grid, t)
      #BSS_P_control.pcontrol(self)
      bss = grid.net.storage
      
      p_mw_bss = - self.residual_load_per_bus(grid) 
      
      # Current parameters of BSS:
      get_soc=self.state_of_charge(grid)
      self.soc_new = get_soc
      get_e_mwh = self.e_mwh_start  
      bss.e_mwh = get_e_mwh
      #get_e_mwh[get_e_mwh < 0] = 0 # sollte eigtl Rechenfehler abfangen
      free_capacity = grid.net.storage.max_e_mwh - get_e_mwh
      
      #LINEAR CHARGING:
      
      # Temporal parameters:
      sunrise, sunset, timedelta_day_s, timedelta_night_s, timedelta_sunrise_sunset_s = grid.get_timedelta(t)

      # power and test cases for linear charging and discharging: 
      p_mw_lin_ch = (free_capacity * 3600)/ timedelta_day_s # hier läuft was verkehrt!!!
      #get_e_mwh = get_e_mwh.fillna(0) # alterntive für negative Werte
      p_mw_lin_dch_night = -(get_e_mwh * 3600)/ timedelta_night_s # kann später raus
      p_mw_lin_dch = -(get_e_mwh * 3600)/ timedelta_night_s
      case_lin_ch = (p_mw_lin_ch < p_mw_bss) #& (p_mw_bss > 0)# 
      case_lin_dch = (p_mw_lin_dch > p_mw_bss) & (p_mw_bss < 0) # <0 wichtig für Rechenfehler # rausnehmen
             
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
              case_lin_dch = (p_mw_lin_dch > p_mw_bss) & (p_mw_bss < 0) # muss hier stehen !!!, klappt sonst nicht
              p_mw_bss[case_lin_dch] = p_mw_lin_dch[case_lin_dch]                 
     
      # Limitation by maximum power:
      p_mw_bss[bss.max_p_mw < p_mw_bss] = bss.max_p_mw[bss.max_p_mw < p_mw_bss]
      p_mw_bss[-bss.max_p_mw > p_mw_bss] = - bss.max_p_mw[-bss.max_p_mw > p_mw_bss]
      
      bss.p_mw = p_mw_bss
      grid.net.storage = bss
      
      # calculate new energy content:
      get_e_mwh = self.stored_energy(grid, p_mw_bss) 
      
      return grid.net.storage

  def pcontrol_trafo_charge(self, grid, t):
      BSS_control.pcontrol(self, grid, t)
      return grid.net.storage


### grid-oriented_feed-in_damping ###
class BSS_P_control_grid_fid(BSS_control):
  def __init__(self, grid, intervall_in_seconds, busses_num): 
      super().__init__(grid, intervall_in_seconds, busses_num)
      
      self.trafo_sn_mva = grid.net.trafo.sn_mva.sum() # oder grid.s_trafo_power ()ist das gleiche

  '''  
  def __init__(self, grid):
      #TODO
      print('Warning: EV grid-oriented_feed-in_damping control is not implemented.')
      super().__init__(grid)
  '''
 
  def pcontrol_direct_charge(self, grid, t):
      BSS_control.pcontrol(self, grid, t)
      return grid.net.storage
  
  def pcontrol_linear_charge(self, grid, t): #pcontrol(self, grid, t): #t

      BSS_control.pcontrol(self, grid, t)
      #BSS_P_control.pcontrol(self)
      bss = grid.net.storage
      
      s_res, p_res = grid.get_residualload_s_sum()
      p_mw_bss_total = - p_res
      print('type p_mw_bss_total: '+ str(type(p_mw_bss_total)))
   
      # Current parameters of BSS:
      get_soc=self.state_of_charge(grid)
      self.soc_new = get_soc
      get_e_mwh = self.e_mwh_start  
      print('type get_e_mwh: ' + str(type(get_e_mwh)))
      free_capacity = grid.net.storage.max_e_mwh - get_e_mwh
      
      #LINEAR CHARGING:
      
      # Temporal parameters:    
      sunrise, sunset, timedelta_day_s, timedelta_night_s, \
          timedelta_sunrise_sunset_s = grid.get_timedelta(t)

      # power and test cases for linear charging and discharging: 
      print('timedelta_day_s: '+ str(timedelta_day_s))
      p_mw_lin_ch_total = (free_capacity.sum() * 3600)/ timedelta_day_s
     ###p_mw_lin_dch_total = -(get_e_mwh.sum() * 3600)/ timedelta_night_s
      #p_mw_lin_ch = p_mw_lin_ch_total * free_capacity/free_capacity.sum()
      #p_mw_lin_dch = p_mw_lin_dch_total * get_e_mwh/get_e_mwh.sum()
      #case_lin_ch = np.less(p_mw_lin_ch, p_mw_bss) # & Scheinliestung kleiner Scheinleistung_nenn
      #case_lin_dch = np.greater(p_mw_lin_dch, p_mw_bss) 
      
      if free_capacity.sum() == 0:
          distribution_factor_ch = 0.0 # np.zeros[len()]
      else:
          distribution_factor_ch = free_capacity/free_capacity.sum()
          distribution_factor_ch = distribution_factor_ch.fillna(0)
      '''
      #distribution_factor_ch = (free_capacity/free_capacity.sum()).fillna(0)
      distribution_factor_ch = free_capacity/(free_capacity.sum())###
      #print('distribution_factor_ch: ' + str(distribution_factor_ch))
      distribution_factor_ch = distribution_factor_ch.fillna(0)
      #distribution_factor_ch = distribution_factor_ch.replace(np.nan,0)
      '''
      print('distribution_factor_ch2: ' + str(distribution_factor_ch))
      print('type distribution_factor_ch: ' + str(type(distribution_factor_ch)))
      if (p_mw_bss_total > 0) and (p_mw_bss_total >= p_mw_lin_ch_total) :
          p_mw_bss_total = p_mw_lin_ch_total
          p_mw_lin_ch = p_mw_bss_total * distribution_factor_ch
          p_mw_bss = p_mw_lin_ch
      elif (p_mw_bss_total > 0) and (p_mw_bss_total < p_mw_lin_ch_total) :
          p_mw_lin_ch = p_mw_bss_total * distribution_factor_ch
          p_mw_bss = p_mw_lin_ch
      elif (p_mw_bss_total < 0): #direkt
          distribution_factor_dch = get_e_mwh/get_e_mwh.sum()
          distribution_factor_dch = distribution_factor_dch.fillna(0) # befüllt alle inf, -inf bzw NaN mit 0
          p_mw_dch = p_mw_bss_total * distribution_factor_dch
          print('p_mw_dch: '+ str(p_mw_dch))
          p_mw_bss = p_mw_dch
      else:
          p_mw_bss = get_e_mwh * 0
      print('type p_mw_bss: '+ str(type(p_mw_bss)))  
      '''
      elif (p_mw_bss_total < 0): #direkt
          #p_mw_lin_dch_total = -(get_e_mwh.sum() * 3600)/ timedelta_night_s
          p_mw_bss_total = p_mw_lin_dch_total
          p_mw_lin_dch = p_mw_bss_total * get_e_mwh/get_e_mwh.sum()
          p_mw_bss = p_mw_lin_dch
      
      elif (p_mw_bss_total < 0) and (p_mw_bss_total < p_mw_lin_dch_total):
          #p_mw_lin_dch_total = -(get_e_mwh.sum() * 3600)/ timedelta_night_s
          p_mw_bss_total = p_mw_lin_dch_total
          p_mw_lin_dch = p_mw_bss_total * get_e_mwh/get_e_mwh.sum()
          p_mw_bss = p_mw_lin_dch
      '''

      #print('p_mw_bss_total_end: ' + str(p_mw_bss_total))
           
      # needed capacity:
      needed_capacity = p_mw_bss * self.intervall / 3600 #
      
      #DIRECT CHARGING:
      
      # Temporal parameters:    
      sunrise, sunset, timedelta_day_s, timedelta_night_s, timedelta_sunrise_sunset_s = grid.get_timedelta(t)    
      
      # test cases for solar excess and load excess:
      solar_excess_1, solar_excess_2, load_excess_1, load_excess_2 = \
          self.get_solar_load_excess_cbss(grid) 
      '''    # wird nicht gbraucht, da durch lin ch. von anfang an gedeckelt wird 
      # Excess in solar power:(wie bei simple) brauch ich das?
      p_mw_bss[solar_excess_1] = free_capacity[solar_excess_1] * 3600 \
                                  / self.intervall
      p_mw_bss[solar_excess_2] = 0 
      '''
      
      print('type p_mw_bss: '+ str(type(p_mw_bss)))
      print('type get_e_mwh: '+ str(type(get_e_mwh)))
      print('type grid.net.storage.efficiency_inverter: '+ str(type(grid.net.storage.efficiency_inverter)))
      #distribution_factor_ch = distribution_factor_ch(np.nan,0)
      
      # Excess in load:(wie bei simple) # später soc_min integrieren statt zeros
      p_mw_bss[load_excess_1] = - get_e_mwh[load_excess_1] \
                                  * grid.net.storage.efficiency_storage[load_excess_1]  \
                                  * grid.net.storage.efficiency_inverter[load_excess_1] \
                                  * 3600 \
                                  / self.intervall
      p_mw_bss[load_excess_2] = 0
      
     # Adjustment of power to linear discharging:
      time = t.tz_localize(None)
      if time <= sunrise or time >= sunset:
          print('Nacht')
          if timedelta_sunrise_sunset_s < (12*3600):
              p_mw_lin_dch = p_mw_bss_total * get_e_mwh/get_e_mwh.sum()
              p_mw_lin_dch = p_mw_lin_dch.fillna(0)
              case_lin_dch = (p_mw_lin_dch > p_mw_bss) & (p_mw_bss < 0)
              p_mw_bss[case_lin_dch] = p_mw_lin_dch[case_lin_dch]
      
      
      bss.p_mw = p_mw_bss
      grid.net.storage = bss    
      
      # calculate new energy content:
      get_e_mwh = self.stored_energy(grid, p_mw_bss) #- self.stored_energy(grid, p_mw_bss)
      #grid.net.storage['e_mwh'] = get_e_mwh #nochmal anders aufschreiben
      print(grid.net.storage.p_mw)
      #return p_mw_bss
      return grid.net.storage
  
    
  
  def pcontrol_linear_charge_cbss(self, grid, t): #pcontrol_linear_charge_cbss
      
      BSS_control.pcontrol(self, grid, t)
      #BSS_P_control.pcontrol(self)
      bss = grid.net.storage
      
      s_res, p_res = grid.get_residualload_s_sum()
      p_mw_bss_total = - p_res # so fehlerhafte darstellung
      
      print('Current parameters of BSS')
      # Current parameters of BSS:             
      get_soc=self.state_of_charge(grid)
      self.soc_new = get_soc
      get_e_mwh = self.e_mwh_start  
      free_capacity = grid.net.storage.max_e_mwh - get_e_mwh  
      
      print('Distribution of residual load over CBSS')
      # Distribution of residual load over CBSS: muss auch in solar_load_excess() !!!
      bss_num = len(bss) 
      
      if free_capacity.sum() == 0.0:
          distribution_factor_ch = np.zeros(len(bss)) # np.zeros[len()]
      else:
          distribution_factor_ch = free_capacity/free_capacity.sum()
          distribution_factor_ch = distribution_factor_ch.fillna(0)
      
      '''
      #alt:
      distribution_factor_ch = free_capacity / free_capacity.sum()
      print('type distribution factor: ' + str(type(distribution_factor_ch)))
      distribution_factor_ch = distribution_factor_ch.fillna(0) # befüllt alle inf, -inf bzw NaN mit 0 auch gür HBSS!!!
      '''
      '''
      distribution_factor_ch = (free_capacity.divide(free_capacity.sum()))#.replace(np.inf, 0)
      distribution_factor_ch = distribution_factor_ch.fillna(0)
      '''
      
      distribution_factor_dch = get_e_mwh / get_e_mwh.sum()
      distribution_factor_dch = distribution_factor_dch.fillna(0) # befüllt alle inf, -inf bzw NaN mit 0 
      
      if p_mw_bss_total > 0: # 0 muss auch noch abgefangen werden!!!
          print('p_mw_bss_total > 0')
          p_mw_bss = (p_mw_bss_total * distribution_factor_ch) #* np.ones(bss_num)
      
      elif p_mw_bss_total < 0:
          print('p_mw_bss_total < 0')
          p_mw_bss = (p_mw_bss_total * distribution_factor_dch) #* np.ones(bss_num)
      
      # needed capacity:
      needed_capacity = p_mw_bss * self.intervall / 3600 #
      
      #DIRECT CHARGING:
      
      # Temporal parameters:    
      sunrise, sunset, timedelta_day_s, timedelta_night_s, timedelta_sunrise_sunset_s = grid.get_timedelta(t) 
             
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
      p_mw_lin_dch = -(get_e_mwh * 3600)/ timedelta_night_s
      case_lin_ch = (p_mw_lin_ch < p_mw_bss)
      #case_lin_dch = (p_mw_lin_dch > p_mw_bss) #nochmal testen

      # Adjustment of power to linear charging:
      p_mw_bss[case_lin_ch] = p_mw_lin_ch[case_lin_ch]

     # Adjustment of power to linear discharging:
      time = t.tz_localize(None)
      if time <= sunrise or time >= sunset:
          print('Nacht')
          if timedelta_sunrise_sunset_s < (12*3600):
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
  
      BSS_control.pcontrol(self, grid, t)
      #BSS_P_control.pcontrol(self)
      bss = grid.net.storage

      p_mw_bss = bss.p_mw
      p_mw_bss_copy = np.copy(p_mw_bss)
      #print('type_p_start: '+ str(type(p_mw_bss)))
      #print('type_p_start_copy: '+ str(type(p_mw_bss_copy)))
      #print('start: '+ str(p_mw_bss))
     
      print('Current parameters of BSS')
      # Current parameters of BSS:
      get_soc = self.state_of_charge(grid)
      get_e_mwh = self.e_mwh_start 
      free_capacity = grid.net.storage.max_e_mwh - get_e_mwh 
      #print('free_capacity: '+ str(free_capacity))

      #FEED-IN DAMPING:
               
      #-----------------ev
      s_res, p_res = grid.get_residualload_s_sum() #residual_load_trafo_s_mva
      p_res = -p_res # warum? weil eingespeichert werden muss? jepp

      #free_capacity = grid.net.storage.max_e_mwh - get_e_mwh #
    
      if grid.s_trafo_power < -s_res: # Fall Trafoüberlastung bei Solarüberschuss, oder? -s_res
          print('trafo ueberlastet')
          q_res_to_the_power_of_2 = s_res**2 - p_res**2
          if q_res_to_the_power_of_2 < grid.s_trafo_power**2: 
              p_trafo_max = (grid.s_trafo_power**2 - q_res_to_the_power_of_2)**(.5)
          else:
              p_trafo_max = 0
          print('p_trafo_max: ' + str(p_trafo_max))   
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
          
      elif grid.s_trafo_power < s_res: # Fall Trafoüberlastung bei Solarüberschuss, oder? -s_res
          print('trafo ueberlastet Netzbezug')
          q_res_to_the_power_of_2 = s_res**2 + p_res**2
          if q_res_to_the_power_of_2 < grid.s_trafo_power**2: 
              p_trafo_max = (q_res_to_the_power_of_2 - grid.s_trafo_power**2)**(.5)
          else:
              p_trafo_max = 0
          print('p_trafo_max: ' + str(p_trafo_max))   
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

      else: 
          p_mw_damped = np.zeros(len(grid.net.storage))
          #print('p_mw_damped: ' + str(p_mw_damped))
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
      p_mw_bss_before_limitation = np.copy(p_mw_bss)
      
      # Limitation by maximum power:     
      p_mw_bss[bss.max_p_mw < p_mw_bss] = bss.max_p_mw[bss.max_p_mw < p_mw_bss]
      p_mw_bss[-bss.max_p_mw > p_mw_bss] = - bss.max_p_mw[-bss.max_p_mw > p_mw_bss]
      bss.p_mw = p_mw_bss
      
      grid.net.storage = bss    
  
      # calculate new energy content:
      p_mw_stored = p_mw_bss - p_mw_bss_copy#bss.p_mw
      #p_mw_stored = pd.Series.to_numpy(p_mw_stored)
      get_e_mwh = self.stored_energy(grid, p_mw_stored) # funktioniert für netz 9 nur mit p_damped, aber falsch
      #print('type_p_mw_stored: '+ str(type(p_mw_stored)))
      #print('type_p_mw_damped: '+ str(type(p_mw_damped)))
      #print('free_capacity: '+ str(free_capacity))
      #print('get_e_mwh: '+ str(get_e_mwh))
      #get_e_mwh = self.stored_energy(grid, p_mw_damped)
      #----------------------------------------------------
      
      
      #bss.p_mw = p_mw_bss # darf hier erst nach get_e_mwh stehen!
      return grid.net.storage
      #return p_mw_bss#d.values

'''
class BSS_P_control_grid_fid_original(BSS_control):

  def __init__(self, grid):
      #TODO
      print('Warning: EV grid-oriented_feed-in_damping control is not implemented.')
      super().__init__(grid)
  
  def pcontrol(self, grid, d):
      BSS_P_control.pcontrol(self)
      
      return d.values
'''  
