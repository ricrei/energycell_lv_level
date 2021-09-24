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
                            max_e_mwh=0.02, soc_percent=0 ,name='bss_'+str(grid.net.load.loc[index, "bus"]), type='bss')
      
      grid.net.storage['efficiency_storage'] = 0.9
      grid.net.storage['efficiency_inverter'] = 0.96
      grid.net.storage['efficiency_mppt'] = 0.98
      grid.net.storage['e_mwh'] =  0 ###
      
      return grid
      
  
    #ec.grid.bss_controller.state_of_charge(grid)

  def create_bss_at_lvbb(self, grid): 
      # create  community bss at low voltage busbar (bus 0)
      max_e_mwh = 0.01
      '''
      pp.create_storage(grid.net, 4 , p_mw=0,\
                            max_e_mwh=max_e_mwh, soc_percent=0 ,name='bss_'+str(4), type='bss')
      '''
      pp.create_storage(grid.net, grid.net.trafo.lv_bus.sum(), p_mw=0,\
                            max_e_mwh=max_e_mwh, soc_percent=0 ,name='bss_'+str(grid.net.trafo.lv_bus.sum()), type='bss')
      
      grid.net.storage['efficiency_storage'] = 0.9
      grid.net.storage['efficiency_inverter'] = 0.96
      grid.net.storage['efficiency_mppt'] = 0.98
      
      return grid

  def create_bss_at_selected_buses(self, grid):
      # create community bss at one or more buses
      storage_num = 2
      selected_buses = [2,5]# seperate several buses by ',' (f.i. [3,8])
      max_e_mwh = 0.01
      
      for x in selected_buses:
          pp.create_storage(grid.net, x, p_mw=0,\
                            max_e_mwh=0.01*x, soc_percent=0 ,name='bss_'+str(x), type='bss')
            
      
      grid.net.storage['efficiency_storage'] = 0.9
      grid.net.storage['efficiency_inverter'] = 0.96
      grid.net.storage['efficiency_mppt'] = 0.98
      
      #grid.net.storage['location'] = selected_buses
      return grid

