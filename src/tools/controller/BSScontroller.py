import numpy as np
import pandas as pd

class BSScontroller:

  def __init__(self, grid, control='simple'):
      self.set_bss = (grid.scenario in [6])

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
      return -residual_load_per_bus


