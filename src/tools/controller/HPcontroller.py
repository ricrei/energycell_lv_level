import numpy as np
import pandas as pd

class HPcontroller:

  def __init__(self, grid, control='greedy'):
      self.set_hp = (grid.scenario in [2, 4, 5, 51, 52, 6])
      if (control=='greedy' or control=='preventive' or control=='curative'):
        self.control = control
        self.cos_phi = .95
        self.tan_phi = np.tan(np.arccos(self.cos_phi))
      else:
        raise ValueError('The entered HP control is not a valid option.')

      if self.set_hp == True:
        if self.control == 'greedy':
          self.P_controller = HP_P_control_greedy(grid)
        elif self.control == 'preventive':
          raise ValueError('HP preventive control is not implemented.')
        elif self.control == 'curative':
          raise ValueError('HP curative control is not implemented.')
      else:
        self.P_controller =  HP_P_control_no_hp(grid)

  def get_active_power(self, grid, d):
      return self.P_controller.pcontrol(grid, d)

  def get_reactive_power(self, grid, d):
      return self.P_controller.get_q(grid, d, self.tan_phi)


class HP_P_control:
  def __init__(self, grid):
      pass

  def pcontrol(self):
      pass

  def get_q(self, grid, d, tan_phi):
      return self.pcontrol(grid, d)*tan_phi 

class HP_P_control_no_hp(HP_P_control):

  def __init__(self, grid):
      super().__init__(grid)

  def pcontrol(self, grid, d):
      HP_P_control.pcontrol(self)
      return d.values*0

class HP_P_control_greedy(HP_P_control):

  def __init__(self, grid):
      super().__init__(grid)

  def pcontrol(self, grid, d):
      HP_P_control.pcontrol(self)
      return d.values


