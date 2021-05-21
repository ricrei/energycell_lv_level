import numpy as np
import pandas as pd

class Curtailcontroller:

  def __init__(self, grid, set_curtailment):
    self.set_curtail = set_curtailment

    if self.set_curtail == True:
      self.curtailment = Curtailment(grid)
    elif self.set_curtail == False:
      self.curtailment = NO_Curtailment()
    else:
      raise ValueError('Curtailment must be 1 or 0. Defined in scenario[1].')

  def curtail(self, grid):
    self.curtailment.residual_load_s = self.curtailment.get_residualload_s(grid)
    grid = self.curtailment.curtail_pv(grid)
    grid = self.curtailment.curtail_load(grid)
    print(self.curtailment.get_residualload_s(grid))
    #print(((grid.net.res_trafo.p_hv_mw**2 + grid.net.res_trafo.q_hv_mvar**2)**(1./2.))[0])
    return grid


class Curtailment:

  def __init__(self, grid):
    self.trafo_power = grid.net.trafo.sn_mva.sum()
    self.sf = .99 # safty factor

  def get_residualload_s(self, grid):
    line_losses_p = grid.net.res_line.pl_mw
    line_losses_q = grid.net.res_line.ql_mvar
    trafo_losses_p = grid.net.res_trafo.pl_mw
    trafo_losses_q = grid.net.res_trafo.ql_mvar
    total_load_p = grid.net.load.p_mw.sum() + line_losses_p.sum() + trafo_losses_p.sum()
    total_load_q = grid.net.load.q_mvar.sum() + line_losses_q.sum() + trafo_losses_q.sum()

    p_res = total_load_p - grid.net.sgen.p_mw.sum()
    q_res = total_load_q - grid.net.sgen.q_mvar.sum()
    s_res = (p_res**2 + q_res**2)**(.5)
    if p_res < 0:
      s_res = -s_res
    
    return s_res

  def curtail_pv(self,grid):
    if (-self.residual_load_s > self.trafo_power*self.sf):
      #print('PV:')
      total_pv_power = (grid.net.sgen.p_mw.sum()**2 + grid.net.sgen.q_mvar.sum()**2)**.5
      curtail_power = -self.residual_load_s - self.trafo_power*self.sf

      grid.net.sgen.p_mw = grid.net.sgen.p_mw * (1 - curtail_power/total_pv_power)
      grid.net.sgen.q_mvar = grid.net.sgen.q_mvar * (1 - curtail_power/total_pv_power)

      grid.curtailed_pv_power = total_pv_power - grid.net.sgen.p_mw.sum()
    else:
      grid.curtailed_pv_power = 0

    return grid

  def curtail_load(self, grid):
    if (self.residual_load_s > self.trafo_power*self.sf):
      #print('Load:')
      total_load_power = (grid.net.load.p_mw.sum()**2 + grid.net.load.q_mvar.sum()**2)**.5
      curtail_power = self.residual_load_s - self.trafo_power*self.sf

      grid.net.load.p_mw = grid.net.load.p_mw * (1 - curtail_power/total_load_power)
      grid.net.load.q_mvar = grid.net.load.q_mvar * (1 - curtail_power/total_load_power)

      grid.curtailed_load_power = total_load_power - grid.net.load.p_mw.sum()
    else:
      grid.curtailed_load_power = 0

    return grid

class NO_Curtailment:
  def __init__(self):
    pass
  def get_residualload_s(self, grid):
    return None
  def curtail_pv(self,grid):
    return grid
  def curtail_load(self,grid):
    return grid
