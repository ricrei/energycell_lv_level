import numpy as np
import pandas as pd

class BSScontroller:

  def __init__(self, grid, control='simple'):
      self.set_bss = (grid.scenario in [6])
      #self.intervall=pd.to_timedelta(time_scope['t_freq']) # converts offset alias to time_delta object
      #self.intervall_in_seconds = self.intervall.total_seconds() # converts time_delta object to time in seconds
      self.intervall_in_seconds = grid.time_scope['intervall_in_seconds']
      #self.sunrise = grid.time_scope['time solar'].sunrise
      self.busses_num = len(grid.component_buses.index)

      if (control=='simple'):
        self.control = control
      elif (control=='feed_in_damping'):
        self.control = control
      else:
        raise ValueError('The entered BSS control is not a valid option.')

      if self.set_bss == True:
        if self.control == 'simple':
          self.P_controller = BSS_control_simple(grid, \
                                                 self.intervall_in_seconds, \
                                                 self.busses_num)
        elif self.control == 'feed_in_damping':
          self.P_controller = BSS_control_feed_in_damping(grid, \
                                                 self.intervall_in_seconds, \
                                                 self.busses_num)
        elif self.control == ' ':
          raise ValueError('BSS control is not implemented.')
        elif self.control == ' ':
          raise ValueError('BSS control is not implemented.')
      else:
        self.P_controller = BSS_control_no_bss(grid, self.intervall_in_seconds, self.busses_num)

  def get_active_power(self, grid):
      return self.P_controller.pcontrol(grid)
  
  def get_e_mwh(self, grid):
      return self.P_controller.e_mwh_start
  
  def get_soc(self, grid):
      return self.P_controller.soc_new
 
class BSS_control:
  def __init__(self, grid, intervall_in_seconds, busses_num): 
      self.intervall = intervall_in_seconds
      self.busses_num = busses_num
      self.soc_start = grid.net.storage.soc_percent 
      self.e_mwh_start = self.soc_start/100 * grid.net.storage.max_e_mwh 
      self.soc_new = self.soc_start
      
      
      
      pass

  def pcontrol(self):
      pass
  
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
      p_neg = np.less(p_mw_dch,np.zeros(self.busses_num))
      p_mw_dch[p_neg] = p_mw_dch[p_neg] \
                          / (grid.net.storage.efficiency_storage[p_neg] \
                             * grid.net.storage.efficiency_inverter[p_neg])
      
      self.e_mwh_start = e_mwh + (p_mw_dch * self.intervall / 3600) # [MWh]
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
  
  def residual_load_per_bus(self, grid):
      residual_load_per_bus = grid.net.load.loc[grid.load_index, 'p_mw'].values + \
                              grid.net.load.loc[grid.hp_index, 'p_mw'].values + \
                              grid.net.load.loc[grid.ev_index, 'p_mw'].values - \
                              grid.net.sgen['p_mw'].values
      return residual_load_per_bus


class BSS_control_no_bss(BSS_control):
  def __init__(self, grid, intervall_in_seconds, busses_num):
      super().__init__(grid, intervall_in_seconds, busses_num)

  def pcontrol(self, grid):
      BSS_control.pcontrol(self)
      return 0

### SIMPLE ###
class BSS_control_simple(BSS_control): 
  def __init__(self, grid, intervall_in_seconds, busses_num): 
      super().__init__(grid, intervall_in_seconds, busses_num)

  def pcontrol(self, grid):
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
      BSS_control.pcontrol(self)
      
      residual_load_per_bus = grid.net.load.loc[grid.load_index, 'p_mw'].values + \
                              grid.net.load.loc[grid.hp_index, 'p_mw'].values + \
                              grid.net.load.loc[grid.ev_index, 'p_mw'].values - \
                              grid.net.sgen['p_mw'].values
                           
      p_mw_bss = -residual_load_per_bus      
      
      get_soc=self.state_of_charge(grid)
      #get_soc=get_soc.fillna(0) # befüllt alle inf, -inf bzw NaN mit 0
      self.soc_new = get_soc
            
      get_e_mwh=self.e_mwh_start
    
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

      get_e_mwh = self.stored_energy(grid, p_mw_bss)

      return p_mw_bss


### FEED IN DAMPING ###
class BSS_control_feed_in_damping(BSS_control): 
  def __init__(self, grid, intervall_in_seconds, busses_num): 
      super().__init__(grid, intervall_in_seconds, busses_num)
      
      #self.trafo_mw_rat = 0.16
      self.trafo_sn_mva = grid.net.trafo.sn_mva.sum() # .sum()?
      self.trafo_load_percent = grid.net.res_trafo.loading_percent
  

  def pcontrol(self, grid):
      
      p_mw_bss = - self.residual_load_per_bus(grid)#np.zeros(self.busses_num)#
      residual_load_trafo_p_mw = sum(p_mw_bss)
      residual_load_trafo_q_mvar = grid.net.load.q_mvar.sum()
      residual_load_trafo_s_mva = (residual_load_trafo_p_mw**2 + residual_load_trafo_q_mvar**2)**(.5)
      
      
      sunrise = grid.time_scope['time solar'].sunrise #wie aktualisieren über mehrere Tage?
      sunset = grid.time_scope['time solar'].sunset
      daylight = sunset - sunrise
      daylight_s = daylight[0].total_seconds()
      #print(daylight)
      
     # p_mw_bss = - self.residual_load_per_bus(grid) 
     # print(p_mw_bss)
      

      
      get_soc=self.state_of_charge(grid)
      #get_soc=get_soc.fillna(0) # befüllt alle inf, -inf bzw NaN mit 0
      self.soc_new = get_soc
            
      get_e_mwh=self.e_mwh_start
      
      ###p_mw_bss = self.power_simple(grid, p_mw_bss, get_e_mwh, get_soc) ###  #ist das ein sicherer Weg?
      
      
      ###-------------
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
      ###----------
      
      #linear charging:
      
      p_mw_lin = (grid.net.storage.max_e_mwh * 3600)/ daylight_s #Cannot divide float64 data by TimedeltaArray
      #print(p_mw_lin)
      
      case_lin = np.less(p_mw_lin, p_mw_bss) # & Scheinliestung kleiner Scheinleistung_nenn
      #weitere Szenarien für Scheinleistung > Scheinleistung_nenn
      
      #p_mw_bss = p_mw_lin
      p_mw_bss[case_lin] = p_mw_lin[case_lin]
      
      
     #feed-in-damping:
         
      residual_load_trafo_s_mva = grid.get_residualload_s_sum()
      print('trafo real:')
      print(residual_load_trafo_s_mva)
      print('trafo nenn:')
      print(self.trafo_sn_mva)
      
      diff_trafo = self.trafo_sn_mva - residual_load_trafo_s_mva
      print('diff trafo:')
      print(diff_trafo)
      
        #case trafo overload grid supply (richtig rum?)
      c_trafo_ol_gs = np.greater(-residual_load_trafo_s_mva, self.trafo_sn_mva) #case: trafo overload grid supply
      c_trafo_ol_fi = np.greater(residual_load_trafo_s_mva, self.trafo_sn_mva)#case: trafo overload feed-in
      
     ### p_mw_bss[c_trafo_ol_fi] = (diff_trafo * np.ones(self.busses_num))[c_trafo_ol_fi]
     ### p_mw_bss[c_trafo_ol_fi] = (diff_trafo * np.ones(self.busses_num))[c_trafo_ol_fi] p_mw_bss[c_trafo_ol_gs] = (diff_trafo * np.ones(self.busses_num))[c_trafo_ol_gs]
      
      if (-residual_load_trafo_s_mva > self.trafo_sn_mva) :
          
          p_mw_bss[solar_excess_1] = free_capacity[solar_excess_1] * 3600 \
                                  / self.intervall
          p_mw_bss[solar_excess_2] = 0 
         # p_mw_bss = (diff_trafo * np.ones(self.busses_num))/200
      #if (res_s > self.trafo_power*self.sf_load):
      
      #self.define_scenarios(grid, p_mw_bss) #?

     # print(type(residual_load_trafo_s_mva))
     # print(type(self.trafo_sn_mva))
      #print((residual_load_trafo_s_mva > self.trafo_sn_mva).item())
      
      #if residual_load_trafo_s_mva > self.trafo_sn_mva:
         # print('Überlastung')
      

      
     # p_mw_bss[self.solar_excess_1]=3
      #case_linear =
      #case_damping =
      
      #print(residual_load_trafo)
      #print(self.trafo_mw_rat)
      #print(self.trafo_load_percent)
      
      get_e_mwh = - self.stored_energy(grid, p_mw_bss)
      
      return p_mw_bss