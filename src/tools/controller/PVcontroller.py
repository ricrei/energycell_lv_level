import numpy as np
import pandas as pd

class PVcontroller:

  def __init__(self, grid, control='qu', cos_phi=.9):
      self.set_pv = (grid.scenario in [3, 4, 6])

      if (control=='qu' or control=='cos_phi'):
        self.control = control
        self.pv_para = {'cos_phi' : cos_phi,
                        'U1' : .93, 'U2' : .97, 'U3' : 1.03, 'U4' : 1.07}
      else:
        raise ValueError('The entered pv control is not a valid option.')
      self.pv_para['tan_phi'] = np.tan(np.arccos(self.pv_para['cos_phi']))

      if self.set_pv == True:
        self.P_controller = PV_P_controlFEEDINALL(self.pv_para)
      else:
        self.P_controller = PV_P_control_no_pv(self.pv_para)

      if self.control == 'qu':
        self.Q_controller = PV_Q_controlQU(grid, self.pv_para)
      elif self.control == 'cos_phi':
        self.Q_controller = PV_Q_controlCOSPHI(self.pv_para)


  def get_reactive_power(self, grid):
      return self.Q_controller.qcontrol(grid)

  def get_active_power(self, grid, d):
      return self.P_controller.pcontrol(grid, d)


class PV_P_control:
  def __init__(self, pv_para):
      self.pv_para = pv_para

  def pcontrol(self):
      pass

class PV_P_control_no_pv(PV_P_control):
  def __init__(self, pv_para):
      super().__init__(pv_para)

  def pcontrol(self, grid, d):
      return d[grid.label_pv_p].values*0


class PV_P_controlFEEDINALL(PV_P_control):
  def __init__(self, pv_para):
      super().__init__(pv_para)

  def pcontrol(self, grid, d):
      return d[grid.label_pv_p].values



class PV_Q_control:
  def __init__(self, pv_para):
      self.pv_para = pv_para

  def qcontrol(self):
      pass


class PV_Q_controlCOSPHI(PV_Q_control):

  def __init__(self, pv_para):
      super().__init__(pv_para)

  def qcontrol(self, grid):
      #PVQcontrol.qcontrol(self)
      grid = self.control_cos_phi(grid)
      return grid.net.sgen['q_mvar']

  def control_cos_phi(self, grid):
      grid.net.sgen["q_mvar"] = -1*grid.net.sgen["p_mw"]*self.pv_para['tan_phi']
      return grid


class PV_Q_controlQU(PV_Q_control):

  def __init__(self, grid, pv_para):
      super().__init__(pv_para)
      self.control_q_u_init(grid)

  def qcontrol(self, grid):
      #PVQcontrol.qcontrol(self)
      grid = self.control_q_u(grid)
      return grid.net.sgen['q_mvar']

  def control_q_u_init(self, grid):
      self.t_minus_x = pd.DataFrame()
      self.t_minus_x['v_t-1'] = grid.net.sgen['bus']*0 + 1.0
      self.calculate_past_time_steps(grid)

  def control_q_u(self, grid):
      a = .2
      q_sgen_t = (self.t_minus_x['q_t-1'])
      self.get_v_of_last_timestep(grid)
      v = (self.t_minus_x['v_t-1'])
      P = grid.net.sgen["p_mw"]
      Q = P * self.pv_para['tan_phi']
      m = Q/(self.pv_para['U2'] - self.pv_para['U1'])

      grid.net.sgen.loc[v <= self.pv_para['U1'], 'q_mvar'] = Q
      grid.net.sgen.loc[(v <= self.pv_para['U2']) & (v >= self.pv_para['U1']), 'q_mvar'] = -m*(v-self.pv_para['U2'])
      grid.net.sgen.loc[(v <= self.pv_para['U3']) & (v >= self.pv_para['U2']), 'q_mvar'] = 0
      grid.net.sgen.loc[(v <= self.pv_para['U4']) & (v >= self.pv_para['U3']), 'q_mvar'] = -m*(v-self.pv_para['U3'])
      grid.net.sgen.loc[v >= self.pv_para['U4'], 'q_mvar'] = -Q

      grid.net.sgen['q_mvar'] = a*grid.net.sgen['q_mvar'] + (1-a)*q_sgen_t
      grid.net.sgen.loc[grid.net.sgen['q_mvar'] < -Q, 'q_mvar'] = -Q
      grid.net.sgen.loc[grid.net.sgen['q_mvar'] >  Q, 'q_mvar'] = Q

      self.calculate_past_time_steps(grid)

      return grid

  def calculate_past_time_steps(self, grid):
      self.t_minus_x['q_t-1'] = grid.net.sgen['q_mvar']
      self.t_minus_x['p_t-1'] = grid.net.sgen['p_mw']

  def get_v_of_last_timestep(self, grid):
      v_buses = grid.net.res_bus.vm_pu[grid.net.sgen['bus']]
      self.t_minus_x['v_t-1'] = v_buses.values
