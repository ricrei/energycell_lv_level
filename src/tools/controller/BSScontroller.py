import numpy as np
import pandas as pd

from tools.powerflow.PowerFlow import PowerFlow #neu

class BSScontroller:

  def __init__(self, grid, time_scope, control='simple'): #neu Tabea (time_scope)
      self.set_bss = (grid.scenario in [6])
      #self.soc_start = grid.net.storage.soc_percent #neu Tabea
      #self.e_mwh_start = self.soc_start * grid.net.storage.max_e_mwh #neu Tabea
      self.intervall=pd.to_timedelta(time_scope['t_freq']) # converts offset alias to time_delta object; neu Tabea
      self.intervall_in_seconds = self.intervall.total_seconds() # converts time_delta object to time in seconds; neu Tabea: 
      #print('Intervall in seconds:') #kann später raus
      #print(self.intervall_in_seconds) #kann später raus

      if (control=='simple'):
        self.control = control
      else:
        raise ValueError('The entered BSS control is not a valid option.')

      if self.set_bss == True:
        if self.control == 'simple':
          self.P_controller = BSS_control_simple(grid, self.intervall_in_seconds)#self.e_mwh_start
        elif self.control == ' ':
          raise ValueError('BSS control is not implemented.')
        elif self.control == ' ':
          raise ValueError('BSS control is not implemented.')
      else:
        self.P_controller = BSS_control_no_bss(grid)

  def get_active_power(self, grid):
      return self.P_controller.pcontrol(grid)
'''
  def state_of_charge(self, grid): #neu Tabea
      soc_test = (self.e_mwh_start / grid.net.storage.max_e_mwh) * 100
      return soc_test
      soc_test = (self.e_mwh_start / grid.net.storage.max_e_mwh) * 100
      return soc_test
  
  def stored_energy(self, grid):#neu Tabea
      e_mwh=self.e_mwh_start
      self.e_mwh_start = e_mwh + self.P_controller.pcontrol(grid)*self.intervall_in_seconds
      return e_mwh
'''
'''
  def test(self, grid, output_data_handler, time_series): # neu Tabea
      test=output_data_handler.storage_state_of_charge.loc[time_series[0]]
      print('test:'+str(test))
      #print(soc_list)
      return test
'''  

''' 
  def get_e_mwh (self, grid.net.storage.min_e_mwh, **kwargs):
      e_mwh = grid.net.storage.min_e_mwh
      return e_mwh
'''

class BSS_control:
  def __init__(self, grid, intervall_in_seconds): #,e_mwh_start
      self.intervall=intervall_in_seconds
      self.soc_start = grid.net.storage.soc_percent #neu Tabea
      self.e_mwh_start = self.soc_start/100 * grid.net.storage.max_e_mwh #neu Tabea
      #self.e_mwh_storage = e_mwh_start
      pass

  def pcontrol(self):
      pass
  
  def state_of_charge(self, grid): #neu Tabea
      soc_test = (self.e_mwh_start / grid.net.storage.max_e_mwh) * 100
      return soc_test
  '''
  def stored_energy(self, grid, residual_load_per_bus):#neu Tabea
      e_mwh=self.e_mwh_start
      #self.e_mwh_start = e_mwh + self.P_controller.pcontrol(grid)*self.intervall_in_seconds
      self.e_mwh_start = e_mwh + residual_load_per_bus*self.intervall#_in_seconds
      return e_mwh
  '''
  def stored_energy(self, grid, p_mw_bss):#neu Tabea
      e_mwh = self.e_mwh_start # [MWh]
     # e_mj = e_mwh * 3600 # [MJ]
      self.e_mwh_start = e_mwh + (p_mw_bss * self.intervall / 3600) #_in_seconds
      #self.e_mj_start = e_mj + p_mw_bss * self.intervall#_in_seconds
      return e_mwh


class BSS_control_no_bss(BSS_control):
  def __init__(self, grid):
      super().__init__(grid)

  def pcontrol(self, grid):
      BSS_control.pcontrol(self)
      return 0

class BSS_control_simple(BSS_control): #intervall_in_seconds
  '''
  def __init__(self, grid, intervall_in_seconds): #BSScontroller
      super().__init__(grid)
      self.intervall=intervall_in_seconds
  '''
  def __init__(self, grid, intervall_in_seconds): #int in s #e_mwh_start
      super().__init__(grid, intervall_in_seconds) #e_mwh_start)

  def pcontrol(self, grid):
      BSS_control.pcontrol(self)
      
      residual_load_per_bus = grid.net.load.loc[grid.load_index, 'p_mw'].values + \
                              grid.net.load.loc[grid.hp_index, 'p_mw'].values + \
                              grid.net.load.loc[grid.ev_index, 'p_mw'].values - \
                              grid.net.sgen['p_mw'].values
                           
      p_mw_bss = -residual_load_per_bus      
      
      get_soc=self.state_of_charge(grid)
      #get_e_mwh=self.stored_energy(grid, residual_load_per_bus)
      get_e_mwh=self.e_mwh_start
      #print('emwh_start_1:')
      #print(get_e_mwh)
      
      #max_e_mj = grid.net.storage.max_e_mwh*3600
      free_capacity = grid.net.storage.max_e_mwh - get_e_mwh
      needed_capacity = p_mw_bss*self.intervall / 3600
      
      busses_num = len(grid.component_buses.index)
      
      #test cases
      solar_excess_1 = np.greater(p_mw_bss,np.zeros(busses_num)) & \
                       np.less(get_soc,np.ones(busses_num)*100) & \
                       np.less(free_capacity, needed_capacity)
      solar_excess_2 = np.greater(p_mw_bss,np.zeros(busses_num)) & \
                       np.equal(get_soc,np.ones(busses_num)*100)
      load_excess_1 = np.less(p_mw_bss,np.zeros(busses_num)) & \
                      np.greater(get_soc,np.zeros(busses_num)) & \
                      np.less(get_e_mwh,-needed_capacity)
      load_excess_2 = np.less(p_mw_bss,np.zeros(busses_num)) & \
                      np.equal(get_soc,np.zeros(busses_num))
      
      # Excess in solar power:
      p_mw_bss[solar_excess_1] = free_capacity[solar_excess_1] * 3600/self.intervall
      p_mw_bss[solar_excess_2] = 0
      
      # Excess in load: # später soc_min integrieren statt zeros
      p_mw_bss[load_excess_1] = - get_e_mwh[load_excess_1] * 3600/self.intervall
      p_mw_bss[load_excess_2] = 0
      
     # print('res_load:')
      #print(residual_load_per_bus)
      #print('e_mwh:')
     # print(get_e_mwh)
      #print('emwh_start:')
      #print(e_mwh)
      print('soc:')
      print(get_soc)
      #print('pmw neu:')
      #print(p_mw_bss)
      
      get_e_mwh=self.stored_energy(grid, p_mw_bss)
      #print('e_mwh2:')
      #print(get_e_mwh)
      #print((residual_load_per_bus < 0).any())
      #z = np.greater(get_e_mwh, grid.net.storage.max_e_mwh)
      #for x in z == False:
         # print('falsch')
  
      
      #print(grid.net.storage['p_mw'].values)
      #return -residual_load_per_bus
      return p_mw_bss


