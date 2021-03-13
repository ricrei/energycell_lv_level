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
from tools.controller.PVQcontrolQU import PVQcontrolQU
from tools.controller.PVQcontrolCOSPHI import PVQcontrolCOSPHI

import bz2
import _pickle as cPickle

class PVcontroller:

  def __init__(self, grid, control='qu', cos_phi=.9):
      # 'control': 'qu', 'cos_phi'
      self.control = control
      self.pv_para = {'cos_phi' : cos_phi,
                      'U1' : .93, 'U2' : .97, 'U3' : 1.03, 'U4' : 1.07}
      self.pv_para['tan_phi'] = np.tan(np.arccos(self.pv_para['cos_phi']))

      if self.control == 'qu':
        self.Qcontroller = PVQcontrolQU(grid, self.pv_para)
      elif self.control == 'cos_phi':
        self.Qcontroller = PVQcontrolCOSPHI(self.pv_para)

  def get_reactive_power(self, grid):
    return self.Qcontroller.qcontrol(grid)
