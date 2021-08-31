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
    grid = self.curtailment.curtail(grid)

    return grid


class Curtailment:

  def __init__(self, grid):
    self.trafo_power = grid.net.trafo.sn_mva.sum()
    self.sf_pv =  .95 # safty factor
    self.sf_load =  .95 # safty factor

    #print(grid.net.bus.feeder)
    #print(grid.monitored_lines)

  def curtail(self,grid):

    res_s, res_p = grid.get_residualload_s_sum()

    if (-res_s > self.trafo_power*self.sf_pv):
      #print('PV:')
      total_pv_power = (grid.net.sgen.p_mw.sum()**2 + grid.net.sgen.q_mvar.sum()**2)**.5
      total_pv_power_mw = grid.net.sgen.p_mw.sum()
      curtail_power = -res_s - self.trafo_power*self.sf_pv

      grid.net.sgen.p_mw = grid.net.sgen.p_mw * (1 - curtail_power/total_pv_power)
      grid.net.sgen.q_mvar = grid.net.sgen.q_mvar * (1 - curtail_power/total_pv_power)

      grid.curtailed_pv_power = total_pv_power_mw - grid.net.sgen.p_mw.sum()
    else:
      grid.curtailed_pv_power = 0

    if (res_s > self.trafo_power*self.sf_load):
      #print('Load:')
      total_load_power = (grid.net.load.p_mw.sum()**2 + grid.net.load.q_mvar.sum()**2)**.5
      total_load_power_mw = grid.net.load.p_mw.sum()
      curtail_power = res_s - self.trafo_power*self.sf_load

      grid.net.load.p_mw = grid.net.load.p_mw * (1 - curtail_power/total_load_power)
      grid.net.load.q_mvar = grid.net.load.q_mvar * (1 - curtail_power/total_load_power)

      grid.curtailed_load_power = total_load_power_mw - grid.net.load.p_mw.sum()
    else:
      grid.curtailed_load_power = 0

    return grid

class NO_Curtailment:
  def __init__(self):
    pass
  def curtail(self,grid):
    return grid
