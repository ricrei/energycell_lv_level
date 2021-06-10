import numpy as np
import pandas as pd

class EVcontroller:

  def __init__(self, grid, control='greedy'):
      self.set_ev = (grid.scenario in [2, 4, 5, 51, 52, 6])
      if (control=='greedy' or control=='preventive' or control=='curative'):
        self.control = control
      else:
        raise ValueError('The entered EV control is not a valid option.')

      if self.set_ev == True:
        if self.control == 'greedy':
          self.P_controller = EV_P_control_greedy(grid)
        elif self.control == 'preventive':
          raise ValueError('EV preventive control is not implemented.')
        elif self.control == 'curative':
          raise ValueError('EV curative control is not implemented.')
      else:
        self.P_controller = EV_P_control_no_ev(grid)

  def get_active_power(self, grid, d):
      return self.P_controller.pcontrol(grid, d)


class EV_P_control:
  def __init__(self, grid):
      pass

  def pcontrol(self):
      pass


class EV_P_control_no_ev(EV_P_control):

  def __init__(self, grid):
      super().__init__(grid)

  def pcontrol(self, grid, d):
      EV_P_control.pcontrol(self)
      return d.values*0


class EV_P_control_greedy(EV_P_control):

  def __init__(self, grid):
      super().__init__(grid)

  def pcontrol(self, grid, d):
      EV_P_control.pcontrol(self)
      return d.values


