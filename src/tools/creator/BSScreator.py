import numpy as np
import pandapower as pp

import tools.tools as tt
from tools.controller.BSScontroller import BSScontroller #neu

class BSScreator:

  def __init__(self):
        self.bss_para = {}

  ###########################################
  ### Create Loads at each bus for all HP ###
  ###########################################
  def create_bss_at_each_bus(self, grid):
      # create bss at each bus 
      for index in grid.component_buses.index:
          pp.create_storage(grid.net, grid.net.load.loc[index, "bus"], p_mw=0,\
                            max_e_mwh=0.01, soc_percent=0 ,name='bss_'+str(grid.net.load.loc[index, "bus"]), type='bss')
      
      grid.net.storage['efficiency_storage'] = 1#0.9
      grid.net.storage['efficiency_inverter'] = 1#0.96
      grid.net.storage['efficiency_mppt'] = 1#0.98
      
      return grid
      
  
    #ec.grid.bss_controller.state_of_charge(grid)

  def create_bss_at_one_bus(self, grid):
      # create bss at bus 0
      pp.create_storage(grid.net, grid.net.load.loc[0, "bus"], p_mw=0,\
                            max_e_mwh=0.13, soc_percent=0 ,name='bss_'+str(grid.net.load.loc[0, "bus"]), type='bss')

      return grid
