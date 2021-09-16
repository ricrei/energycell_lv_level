import numpy as np
import pandas as pd
import tools.tools as tt

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

  def get_active_power(self, grid, t): #t
      return self.P_controller.pcontrol(grid, t) #t
  
  def get_active_power_direct_charge(self, grid):
      return self.P_controller.pcontrol_direct_charge(grid) 
  
  def get_active_power_linear_charge(self, grid, t):
      return self.P_controller.pcontrol_linear_charge(grid, t)
  '''
  def get_active_power_trafo_charge(self, grid, t):
      return self.P_controller.pcontrol(grid, t)
  '''
  def get_e_mwh(self, grid):
      return self.P_controller.e_mwh_start
  
  def get_soc(self, grid):
      return self.P_controller.soc_new
 
class BSS_control:
  def __init__(self, grid, intervall_in_seconds, bss_num): 
      self.intervall = intervall_in_seconds
      self.bss_num = len(grid.net.storage)# bss_num
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
  
  def residual_load_per_bus(self, grid):
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


class BSS_control_no_bss(BSS_control):
  def __init__(self, grid, intervall_in_seconds, busses_num):
      super().__init__(grid, intervall_in_seconds, busses_num)

  def pcontrol(self, grid, t):#t
      BSS_control.pcontrol(self)
      return 0

### SIMPLE ###
class BSS_control_simple(BSS_control): 
  def __init__(self, grid, intervall_in_seconds, bss_num): 
      super().__init__(grid, intervall_in_seconds, bss_num)
      
  def pcontrol_direct_charge(self, grid): #eigentlich brauche ich t nicht
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
      
      BSS_control.pcontrol(self)
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
      free_capacity = grid.net.storage.max_e_mwh - get_e_mwh #
      needed_capacity = p_mw_bss * self.intervall / 3600 #

      # Test cases for determination of charging/discharging power:
      solar_excess_1, solar_excess_2, load_excess_1, load_excess_2 = \
          self.get_solar_load_excess(grid) 
        
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
      
      # New energy content and SOC of BSS:
      get_e_mwh = self.stored_energy(grid, p_mw_bss)    
      ###grid.net.storage['soc_percent'] = bss_controller.get_soc(grid)
      bss.p_mw = p_mw_bss
      
      grid.net.storage = bss
      return grid.net.storage
      #return p_mw_bss


### FEED IN DAMPING ###
class BSS_P_control_grid_fid2(BSS_control):#BSS_control_feed_in_damping(BSS_control): 
  def __init__(self, grid, intervall_in_seconds, busses_num): 
      super().__init__(grid, intervall_in_seconds, busses_num)
      
      self.trafo_sn_mva = grid.net.trafo.sn_mva.sum() # .sum()?
      self.trafo_load_percent = grid.net.res_trafo.loading_percent
  

  def pcontrol(self, grid, t):
      
      
      #p_mw_bss = - self.residual_load_per_bus(grid)#np.zeros(self.busses_num)#
      #residual_load_trafo_p_mw = sum(p_mw_bss)
      #residual_load_trafo_q_mvar = grid.net.load.q_mvar.sum()
      #residual_load_trafo_s_mva = (residual_load_trafo_p_mw**2 + residual_load_trafo_q_mvar**2)**(.5)
      
      #ts=tt.get_time_sun()
      #print(ts)
      
      #------------------ersetzen------------------------------------------
      '''
      sunrise = grid.time_scope['time solar'].sunrise #wie aktualisieren über mehrere Tage?
      sunset = grid.time_scope['time solar'].sunset
      daylight = sunset - sunrise
      daylight_s = daylight[0].total_seconds()
      '''
      #--------------------------------------------------------------------
      
      p_mw_bss = - self.residual_load_per_bus(grid) 
     # print(p_mw_bss)
      '''
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
      
      
      
      p_mw_bss = - self.residual_load_per_bus(grid) 
     # print(p_mw_bss)
      '''

      
      get_soc=self.state_of_charge(grid)
      #get_soc=get_soc.fillna(0) # befüllt alle inf, -inf bzw NaN mit 0
      self.soc_new = get_soc
            
      get_e_mwh=self.e_mwh_start
      
      ###p_mw_bss = self.power_simple(grid, p_mw_bss, get_e_mwh, get_soc) ###  #ist das ein sicherer Weg?
      
      
      free_capacity = grid.net.storage.max_e_mwh - get_e_mwh
      '''
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
      '''
      #weitere Szenarien für Scheinleistung > Scheinleistung_nenn
      
      #feed-in damping:
      residual_load_trafo_s_mva = grid.get_residualload_s_sum() # warum bekomme ich hier array mit 2 einträgen? [s_res, p_res]
      print('trafo real:')
      print(residual_load_trafo_s_mva[0])
      print('trafo nenn:')
      print(self.trafo_sn_mva)
      
      diff_trafo = self.trafo_sn_mva - residual_load_trafo_s_mva[0]
      print('diff trafo:')
      print(diff_trafo)
      
      busses_num = len(grid.component_buses.index) # nur vorübergehend
      p_mw_damped = (diff_trafo * np.ones(busses_num))/200 # später anpassen
          
      
      
      
      #p_mw_bss = p_mw_lin
      #p_mw_bss[case_lin] = p_mw_lin[case_lin]
      
      
     #feed-in-damping:
         

      
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
          #print(p_mw_lin)
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

          
      
     # p_mw_bss[self.solar_excess_1]=3
      #case_linear =
      #case_damping =
      
      #print(residual_load_trafo)
      #print(self.trafo_mw_rat)
      #print(self.trafo_load_percent)
      
      get_e_mwh = - self.stored_energy(grid, p_mw_bss)
      
      return p_mw_bss

### household-oriented_feed-in_damping ###
class BSS_P_control_hh_fid(BSS_control):

  def __init__(self, grid, intervall_in_seconds, bss_num):
      #TODO
      print('Warning: BSS household-oriented_feed-in_damping control is not implemented.')
      super().__init__(grid, intervall_in_seconds, bss_num)
      
      self.trafo_sn_mva = grid.net.trafo.sn_mva.sum()
      self.df_solar = tt.get_time_sun()
      #Methode lineares Laden

  #def pcontrol(self, grid, t): #d?
  def pcontrol_linear_charge(self, grid, t):
      BSS_control.pcontrol(self)
      #BSS_P_control.pcontrol(self)
      bss = grid.net.storage
      
      p_mw_bss = - self.residual_load_per_bus(grid) 
      
      # Current parameters of BSS:
      get_soc=self.state_of_charge(grid)
      self.soc_new = get_soc
      get_e_mwh = self.e_mwh_start          
      free_capacity = grid.net.storage.max_e_mwh - get_e_mwh
      
      #LINEAR CHARGING:
      
      # Temporal parameters:    
      sunrise = self.df_solar.loc[str(t.date())].sunrise
      sunset = self.df_solar.loc[str(t.date())].sunset
      timedelta_sunrise_sunset_s = (sunset - sunrise).total_seconds()
      timedelta_day_s = abs((sunset - t).total_seconds())
      timedelta_night_s = abs((sunrise - t).total_seconds())

      # power and test cases for linear charging and discharging: 
      p_mw_lin_ch = (free_capacity * 3600)/ timedelta_day_s # hier läuft was verkehrt!!!
      p_mw_lin_dch = -(get_e_mwh * 3600)/ timedelta_night_s
      case_lin_ch = np.less(p_mw_lin_ch, p_mw_bss) # & Scheinliestung kleiner Scheinleistung_nenn
      case_lin_dch = np.greater(p_mw_lin_dch, p_mw_bss) 
             
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
      if timedelta_sunrise_sunset_s < (12*3600):
          p_mw_bss[case_lin_dch] = p_mw_lin_dch[case_lin_dch]
            
      bss.p_mw = p_mw_bss
      grid.net.storage = bss
      
      # calculate new energy content:
      get_e_mwh = - self.stored_energy(grid, p_mw_bss)
      
      return grid.net.storage
      #return p_mw_bss #d.values
  

### grid-oriented_feed-in_damping ###
class BSS_P_control_grid_fid(BSS_control):
  def __init__(self, grid, intervall_in_seconds, busses_num): 
      super().__init__(grid, intervall_in_seconds, busses_num)
      #Methode lineares Laden
      #Methode feed-in damping
      
      self.trafo_sn_mva = grid.net.trafo.sn_mva.sum()
      self.df_solar = tt.get_time_sun()

  '''  
  def __init__(self, grid):
      #TODO
      print('Warning: EV grid-oriented_feed-in_damping control is not implemented.')
      super().__init__(grid)
  '''
  def pcontrol_linear_charge(self, grid, t): #pcontrol(self, grid, t): #t
      BSS_control.pcontrol(self)
      #BSS_P_control.pcontrol(self)
      bss = grid.net.storage
      
      p_mw_bss = - self.residual_load_per_bus(grid) 
      
      # Current parameters of BSS:
      get_soc=self.state_of_charge(grid)
      self.soc_new = get_soc
      get_e_mwh = self.e_mwh_start          
      free_capacity = grid.net.storage.max_e_mwh - get_e_mwh
      
      #LINEAR CHARGING:
      
      # Temporal parameters:    
      sunrise = self.df_solar.loc[str(t.date())].sunrise
      sunset = self.df_solar.loc[str(t.date())].sunset
      timedelta_sunrise_sunset_s = (sunset - sunrise).total_seconds()
      timedelta_day_s = abs((sunset - t).total_seconds())
      timedelta_night_s = abs((sunrise - t).total_seconds())

      # power and test cases for linear charging and discharging: 
      p_mw_lin_ch = (free_capacity * 3600)/ timedelta_day_s # hier läuft was verkehrt!!!
      p_mw_lin_dch = -(get_e_mwh * 3600)/ timedelta_night_s
      case_lin_ch = np.less(p_mw_lin_ch, p_mw_bss) # & Scheinliestung kleiner Scheinleistung_nenn
      case_lin_dch = np.greater(p_mw_lin_dch, p_mw_bss) 
             
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
      if timedelta_sunrise_sunset_s < (12*3600):
          p_mw_bss[case_lin_dch] = p_mw_lin_dch[case_lin_dch]
      
      bss.p_mw = p_mw_bss
      grid.net.storage = bss    
      
      # calculate new energy content:
      get_e_mwh = - self.stored_energy(grid, p_mw_bss)
      
      #return p_mw_bss
      return grid.net.storage
  
   
  def pcontrol_xxx_charge(self, grid, t): #pcontrol(self, grid, t): #t
      BSS_control.pcontrol(self)
      #BSS_P_control.pcontrol(self)
      bss = grid.net.storage
      
      p_mw_bss = - self.residual_load_per_bus(grid) 
      
      # Current parameters of BSS:
      get_soc=self.state_of_charge(grid)
      self.soc_new = get_soc
      get_e_mwh = self.e_mwh_start          
      free_capacity = grid.net.storage.max_e_mwh - get_e_mwh    
  #-----------
      #FEED-IN DAMPING:
               
      #-----------------ev
      s_res, p_res = grid.get_residualload_s_sum() #residual_load_trafo_s_mva
      p_res = -p_res

      if grid.s_trafo_power < -s_res:
         q_res_to_the_power_of_2 = s_res**2 - p_res**2
         if q_res_to_the_power_of_2 < grid.s_trafo_power**2:
            p_trafo_max = (grid.s_trafo_power**2 - q_res_to_the_power_of_2)**(.5)
         else:
            p_trafo_max = 0
      else:
         p_trafo_max = p_res

      p_total_bss = p_res - p_trafo_max
      print('p total:')
      print(p_total_bss)
      
      #---------------------ev
          
      #residual_load_trafo_s_mva = grid.get_residualload_s_sum() # warum bekomme ich hier array mit 2 einträgen? [s_res, p_res]
      #print('trafo real:')
      #print(residual_load_trafo_s_mva[0])
      #print('trafo nenn:')
      #print(self.trafo_sn_mva)
      
      ##diff_s_trafo = self.trafo_sn_mva - s_res #residual_load_trafo_s_mva[0]
      #print('diff trafo:')
      #print(diff_trafo)
      
      busses_num = len(grid.component_buses.index) # nur vorübergehend
      p_mw_damped =(p_total_bss * np.ones(self.busses_num))/200 # später anpassen !!! hier weiter!
      
      #if (-residual_load_trafo_s_mva[0] > self.trafo_sn_mva) :
      if (-s_res > self.trafo_sn_mva): 
          
          needed_capacity = p_mw_bss * self.intervall / 3600
      
      # test cases
      solar_excess_1, solar_excess_2, load_excess_1, load_excess_2 = \
          self.get_solar_load_excess(grid)

         # p_mw_bss = (diff_trafo * np.ones(self.busses_num))/200
      #if (res_s > self.trafo_power*self.sf_load): dieser Fall muss noch beprochen werden
      

      return p_mw_bss#d.values

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
    
class BSS_control_feed_in_damping2(BSS_control): #kann dann raus
  def __init__(self, grid, intervall_in_seconds, busses_num): 
      super().__init__(grid, intervall_in_seconds, busses_num)
      
      #self.trafo_mw_rat = 0.16
      self.trafo_sn_mva = grid.net.trafo.sn_mva.sum() # .sum()?
      self.trafo_load_percent = grid.net.res_trafo.loading_percent
      
      #ts=tt.get_time_sun()
      #print(ts)
  

  def pcontrol(self, grid):
      
      print(grid.net.storage)
      
      p_mw_res = - self.residual_load_per_bus(grid) 
      p_mw_bss = p_mw_res.sum()
      
      print(p_mw_bss)
      print(p_mw_bss.sum())
      
     # test2 = np.equal(e.grid.net.storage.bus)
      
      return p_mw_bss
