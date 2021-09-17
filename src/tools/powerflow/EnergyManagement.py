import time
import numpy as np
import pandas as pd
import logging
import tools.tools as tt

class EnergyManagement:
  '''
  Manageing the sequence the components(HP, EV, BSS) are charging/discharging.
  Creating an object 'energy_manager', which contains the method control_components. These method manage the order of component utilization. 
  '''

  def __init__(self, scenario):
    self.scenario = scenario
    if (self.scenario[0] in [1, 2, 3, 4, 5, 6]) & (self.scenario[1] in [0]):
      self.energy_manager = EnergyManagementTest()
    elif (self.scenario[0] in [6, 7, 8]) & (self.scenario[1] in [1, 2]):
      self.energy_manager = EnergyManagementTest()

  def control_components(self,
                         input_dict,
                         grid,
                         pv_controller,
                         hp_controller,
                         ev_controller,
                         bss_controller,
                         curtail_controller,
                         t):
    ''' Call from energy_manager control_components. Retrun grid.net : TYPE pandapower network. '''
    grid.net = self.energy_manager.control_components(
                         input_dict,
                         grid,
                         pv_controller,
                         hp_controller,
                         ev_controller,
                         bss_controller,
                         curtail_controller,
                         t)
    return grid.net


### Parent class EnergyManagement ###
class EnergyManagementParent:
  def __init__(self):
    pass

  def control_components(self,
                         input_dict,
                         grid,
                         pv_controller,
                         hp_controller,
                         ev_controller,
                         bss_controller,
                         curtail_controller,
                         t):

    return grid.net

### EnergeManagementBasic 1-6 ###
class EnergyManagementBasic(EnergyManagementParent):
  def __init__(self):
    super().__init__()

  def control_components(self,
                         input_dict,
                         grid,
                         pv_controller,
                         hp_controller,
                         ev_controller,
                         bss_controller,
                         curtail_controller,
                         t):
    '''
    Set the sequence in which the components are loaded. This is done in a basic manner. PV, HP and EV are driven in a simple way. The BSS act like its specified mode in bss_controller.
    Only used in scenario 1 to 6.

    Parameters
    ----------
    input_dict: TYPE dict
    grid : TYPE network
    pv_controller : TYPE pv_controller
    hp_controller : TYPE hp_controller
    ev_controller : TYPE ev_controller
    bss_controller : TYPE bss_controller
    curtail_controller : TYPE curtail_controller

    Returns
    -------
    grid.net : pandapower network
    '''

    grid.net.sgen['p_mw'] = pv_controller.get_active_power(grid, input_dict['pv'].loc[t])
    grid.net.sgen['q_mvar'] = pv_controller.get_reactive_power(grid)

    grid.net.load.loc[grid.load_index, 'p_mw'] = input_dict['load_p'].loc[t].values
    grid.net.load.loc[grid.load_index, 'q_mvar'] = input_dict['load_q'].loc[t].values

    grid.net.load.loc[grid.hp_index, 'p_mw'] = hp_controller.get_active_power(grid, input_dict['hp'].loc[t])
    grid.net.load.loc[grid.hp_index, 'q_mvar'] = hp_controller.get_reactive_power(grid, input_dict['hp'].loc[t])

    grid.net.load.loc[grid.ev_index] = ev_controller.get_active_power_direct_charge(grid, t)

    grid.net.storage['p_mw'] = bss_controller.get_active_power(grid)
    grid.net.storage['soc_percent'] = bss_controller.get_soc(grid)

    grid.net.ext_grid.vm_pu = grid.get_vm_pu_ext_grid(grid)

    grid = curtail_controller.curtail(grid)

    return grid.net

### EnergeManagement 8 ###
class EnergyManagement8(EnergyManagementParent):
  def __init__(self):
    super().__init__()

  def control_components(self,
                         input_dict,
                         grid,
                         pv_controller,
                         hp_controller,
                         ev_controller,
                         bss_controller,
                         curtail_controller,
                         t):
    '''
    Set the sequence in which the components are loaded. This is done in a basic manner. PV, HP and EV are driven in a simple way. The BSS act like its specified mode in bss_controller.
    Only used in scenario 1 to 6.

    Parameters
    ----------
    input_dict: TYPE dict
    grid : TYPE network
    pv_controller : TYPE pv_controller
    hp_controller : TYPE hp_controller
    ev_controller : TYPE ev_controller
    bss_controller : TYPE bss_controller
    curtail_controller : TYPE curtail_controller

    Returns
    -------
    grid.net : pandapower network
    '''

    grid.net.sgen['p_mw'] = pv_controller.get_active_power(grid, input_dict['pv'].loc[t])
    grid.net.sgen['q_mvar'] = pv_controller.get_reactive_power(grid)

    grid.net.load.loc[grid.load_index, 'p_mw'] = input_dict['load_p'].loc[t].values
    grid.net.load.loc[grid.load_index, 'q_mvar'] = input_dict['load_q'].loc[t].values

    grid.net.load.loc[grid.hp_index] = hp_controller.get_active_power_direct_charge(grid, t)
    grid.net.load.loc[grid.hp_index] = hp_controller.get_active_power_p_res_charge(grid, t)
    grid.net.load.loc[grid.hp_index] = hp_controller.get_active_power_trafo_charge(grid, t)

    grid.net.load.loc[grid.hp_index] = hp_controller.get_reactive_power(grid, input_dict['hp'].loc[t])

    grid.net.load.loc[grid.ev_index] = ev_controller.get_active_power_direct_charge(grid, t)
    grid.net.load.loc[grid.ev_index] = ev_controller.get_active_power_p_res_charge(grid, t)
    grid.net.load.loc[grid.ev_index] = ev_controller.get_active_power_trafo_charge(grid, t)

    grid.net.storage = bss_controller.get_active_power_linear_charge(grid)
    grid.net.storage = bss_controller.get_active_power_trafo_charge(grid)
    #grid.net.storage['soc_percent'] = bss_controller.get_soc(grid) #

    grid.net.ext_grid.vm_pu = grid.get_vm_pu_ext_grid(grid)

    grid = curtail_controller.curtail(grid)

    return grid.net


class EnergyManagementTest(EnergyManagementParent):
  def __init__(self):
    pass

  def control_components(self,
                         input_dict,
                         grid,
                         pv_controller,
                         hp_controller,
                         ev_controller,
                         bss_controller,
                         curtail_controller,
                         t):
    '''
    Set the sequence in which the components are loaded. This is done in a complex manner. PV, HP, EV and BSS act like its specified mode defined in their respective controller.
    Only used in scenario 7 and 8.

    Parameters
    ----------
    input_dict: TYPE dict
    grid : TYPE network
    pv_controller : TYPE pv_controller
    hp_controller : TYPE hp_controller
    ev_controller : TYPE ev_controller
    bss_controller : TYPE bss_controller
    curtail_controller : TYPE curtail_controller

    Returns
    -------
    grid.net : pandapower network
    '''

    grid = grid.reset_all_power_values()

    grid.net.sgen['p_mw'] = pv_controller.get_active_power(grid, input_dict['pv'].loc[t])
    grid.net.sgen['q_mvar'] = pv_controller.get_reactive_power(grid)

    grid.net.load.loc[grid.load_index, 'p_mw'] = input_dict['load_p'].loc[t].values
    grid.net.load.loc[grid.load_index, 'q_mvar'] = input_dict['load_q'].loc[t].values

    grid.net.load.loc[grid.hp_index, 'p_mw'] = hp_controller.get_active_power(grid, input_dict['hp'].loc[t], t)
    grid.net.load.loc[grid.hp_index, 'q_mvar'] = hp_controller.get_reactive_power(grid, input_dict['hp'].loc[t], t)

    grid.net.load.loc[grid.ev_index] = ev_controller.get_active_power_direct_charge(grid, t)
    grid.net.load.loc[grid.ev_index] = ev_controller.get_active_power_p_res_charge(grid, t)
    grid.net.load.loc[grid.ev_index] = ev_controller.get_active_power_trafo_charge(grid, t)

    grid.net.storage = bss_controller.get_active_power_direct_charge(grid, t)##
    ###grid.net.storage['p_mw'] = bss_controller.get_active_power_direct_charge(grid)
    grid.net.storage = bss_controller.get_active_power_linear_charge(grid, t)
    #grid.net.storage = bss_controller.get_active_power(grid, t)
    ##grid.net.storage['p_mw'] = bss_controller.get_active_power(grid,t) #t
    grid.net.storage['soc_percent'] = bss_controller.get_soc(grid)

    grid.net.ext_grid.vm_pu = grid.get_vm_pu_ext_grid(grid)

    grid = curtail_controller.curtail(grid)

    return grid.net
