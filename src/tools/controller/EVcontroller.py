import numpy as np
import pandas as pd

class EVcontroller:

  def __init__(self, grid, control='greedy'):
      self.set_ev = (grid.scenario[0] in [2, 4, 5, 6, 7, 8])
      if (control=='greedy' or control=='household-oriented_feed-in_damping' or control=='grid-oriented_feed-in_damping'):
        self.control = control
      else:
        raise ValueError('The entered EV control is not a valid option.')

      if self.set_ev == True:
        if self.control == 'greedy':
          self.P_controller = EV_P_control_greedy(grid)
        elif self.control == 'household-oriented_feed-in_damping':
          self.P_controller = EV_P_control_hh_fid(grid)
        elif self.control == 'grid-oriented_feed-in_damping':
          self.P_controller = EV_P_control_grid_fid(grid)
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

### greedy ###
class EV_P_control_greedy(EV_P_control):

  def __init__(self, grid):
      super().__init__(grid)

  def pcontrol(self, grid, d):
      EV_P_control.pcontrol(self)
      return d.values

### household-oriented_feed-in_damping ###
class EV_P_control_hh_fid(EV_P_control):

  def __init__(self, grid):
      #TODO
      print('Warning: EV household-oriented_feed-in_damping control is not implemented')
      super().__init__(grid)

  def pcontrol(self, grid, d):
      EV_P_control.pcontrol(self)
      return d.values

### grid-oriented_feed-in_damping ###
class EV_P_control_grid_fid(EV_P_control):

  def __init__(self, grid):
      #TODO
      print('Warning: EV grid-oriented_feed-in_damping control is not implemented')
      super().__init__(grid)

  def pcontrol(self, grid, d):
      EV_P_control.pcontrol(self)
      return d.values
