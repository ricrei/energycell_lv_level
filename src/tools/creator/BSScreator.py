import numpy as np
import pandapower as pp

import tools.tools as tt

class BSScreator:

  def __init__(self):
        self.bss_para = {}

  ###########################################
  ### Create Loads at each bus for all HP ###
  ###########################################
  def create_bss_at_each_bus(self, grid):
      # create bss at each bus 
      for index in grid.component_buses.index:
          pp.create_storage(grid.net, grid.net.load.loc[index, "bus"], p_mw=0, max_e_mwh=0, name='bss_'+str(grid.net.load.loc[index, "bus"]), type='bss')

      return grid
