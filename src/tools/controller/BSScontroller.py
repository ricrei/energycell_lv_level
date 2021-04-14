import numpy as np
import pandas as pd

from tools.powerflow.PowerFlow import PowerFlow #neu

class BSScontroller:

  def __init__(self, grid, time_scope, control='simple'): #neu Tabea (time_scope)
      self.set_bss = (grid.scenario in [6])
      self.soc_start = grid.net.storage.soc_percent #neu Tabea
      self.e_mwh_start = self.soc_start * grid.net.storage.max_e_mwh #neu Tabea
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
          self.P_controller = BSS_control_simple(grid)
        elif self.control == ' ':
          raise ValueError('BSS control is not implemented.')
        elif self.control == ' ':
          raise ValueError('BSS control is not implemented.')
      else:
        self.P_controller = BSS_control_no_bss(grid)

  def get_active_power(self, grid):
      return self.P_controller.pcontrol(grid)
  
  def state_of_charge(self, grid): #neu Tabea
      soc_test = (self.e_mwh_start / grid.net.storage.max_e_mwh) * 100
      return soc_test
  
  def stored_energy(self, grid):#neu Tabea
      e_mwh=self.e_mwh_start
      self.e_mwh_start = e_mwh + self.P_controller.pcontrol(grid)*self.intervall_in_seconds
      return e_mwh

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
  def __init__(self, grid):
      pass

  def pcontrol(self):
      pass


class BSS_control_no_bss(BSS_control):
  def __init__(self, grid):
      super().__init__(grid)

  def pcontrol(self, grid):
      BSS_control.pcontrol(self)
      return 0

class BSS_control_simple(BSS_control):

  def __init__(self, grid):
      super().__init__(grid)

  def pcontrol(self, grid):
      BSS_control.pcontrol(self)
      residual_load_per_bus = grid.net.load.loc[grid.load_index, 'p_mw'].values + \
                              grid.net.load.loc[grid.hp_index, 'p_mw'].values + \
                              grid.net.load.loc[grid.ev_index, 'p_mw'].values - \
                              grid.net.sgen['p_mw'].values
      #print(grid.net.storage['p_mw'].values)
      return -residual_load_per_bus


