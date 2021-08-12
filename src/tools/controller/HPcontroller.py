import numpy as np
import pandas as pd

class HPcontroller:

  def __init__(self, grid, control='direct'):
      self.set_hp = (grid.scenario[0] in [2, 4, 5, 6, 7, 8])
      if (control=='direct' or control=='household-oriented_feed-in_damping' or control=='grid-oriented_feed-in_damping'):
        self.control = control
        self.cos_phi = .95
        self.tan_phi = np.tan(np.arccos(self.cos_phi))
      else:
        raise ValueError('The entered HP control is not a valid option.')

      if self.set_hp == True:
        if self.control == 'direct':
          self.P_controller = HP_P_control_direct(grid)
        elif self.control == 'household-oriented_feed-in_damping':
          self.P_controller = HP_P_control_hh_fid(grid)
        elif self.control == 'grid-oriented_feed-in_damping':
          self.P_controller = HP_P_control_grid_fid(grid)
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

### no HP ###
class HP_P_control_no_hp(HP_P_control):

  def __init__(self, grid):
      super().__init__(grid)

  def pcontrol(self, grid, d):
      HP_P_control.pcontrol(self)
      return d.values*0

### direct ###
class HP_P_control_direct(HP_P_control):

  def __init__(self, grid):
      super().__init__(grid)

  def pcontrol(self, grid, d):
      HP_P_control.pcontrol(self)
      return d.values

### household-oriented_feed-in_damping ###
class HP_P_control_hh_fid(HP_P_control):

  def __init__(self, grid):
      #TODO
      print('Warning: HP household-oriented_feed-in_damping control is not implemented')
      super().__init__(grid)

  def pcontrol(self, grid, d):
      HP_P_control.pcontrol(self)
      return d.values

### grid-oriented_feed-in_damping ###
class HP_P_control_grid_fid(HP_P_control):

  def __init__(self, grid):
      #TODO
      print('Warning: HP grid-oriented_feed-in_damping control is not implemented')
      super().__init__(grid)

  def pcontrol(self, grid, d):
      HP_P_control.pcontrol(self)
      return d.values
