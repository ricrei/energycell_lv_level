import os
import csv
import time
import numpy as np
import pandas as pd
import pandapower as pp
import pandapower.networks as pn
import pandapower.toolbox as tb
import simbench as sb
import tools.tools as tt

import bz2
import _pickle as cPickle

class PVQcontrolCOSPHI:

  def __init__(self, pv_para):
      self.pv_para = pv_para

  def qcontrol(self, grid):
      grid = self.control_cos_phi(grid)
      return grid.net.sgen['q_mvar']

  def control_cos_phi(self, grid):
      grid.net.sgen["q_mvar"] = -1*grid.net.sgen["p_mw"]*self.pv_para['tan_phi']
      return grid

  def get_v_of_last_timestep(self, grid):
      pass
