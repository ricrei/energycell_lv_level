import time
import numpy as np
import pandas as pd
import logging
import tools.tools as tt

class EnergyManagement:
  '''
  Manage the sequence the components(HP, EV, BSS) are charging/discharging.
  Create an object 'energy_manager', which contains the method control_components. These method manage the order of component utilization. 
  '''

  def __init__(self, scenario):
    self.scenario = scenario
    if (self.scenario[0] in [1, 2, 3, 4, 5]):
      self.energy_manager = EnergyManagementBasic()
    elif(self.scenario[0] in [6]):
      self.energy_manager = EnergyManagementStorage()
    elif (self.scenario[0] in [7, 8, 9]):
      self.energy_manager = EnergyManagementAdvanced()
    else:
      raise ValueError('No appropriate scenario to choose EnergyManagement.')

  def control_components(self,
                         input_dict,
                         grid,
                         pv_controller,
                         hp_controller,
                         ev_controller,
                         bss_controller,
                         curtail_controller,
                         t,
                         grid_analysis):
    ''' Call from energy_manager control_components. Retrun grid.net : TYPE pandapower network. '''
    grid.net = self.energy_manager.control_components(
                         input_dict,
                         grid,
                         pv_controller,
                         hp_controller,
                         ev_controller,
                         bss_controller,
                         curtail_controller,
                         t,
                         grid_analysis)
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
                         t,
                         pf):

    return grid.net

### EnergeManagementBasic 1-5 ###
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
                         t,
                         pf):
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

    grid = grid.reset_all_power_values()

    # PV
    grid.net.sgen['p_mw'] = pv_controller.get_active_power(grid, input_dict['pv'].loc[t])
    if pf==True:
      grid.net.sgen['q_mvar'] = pv_controller.get_reactive_power(grid)

    # HH-Load
    grid.net.load.loc[grid.load_index, 'p_mw'] = input_dict['load_p'].loc[t].values
    if pf == True:
      grid.net.load.loc[grid.load_index, 'q_mvar'] = input_dict['load_q'].loc[t].values

    # direct
    grid.net.load.loc[grid.ev_index] = ev_controller.get_active_power_direct_charge(grid, t)
    grid.net.load.loc[grid.hp_index] = hp_controller.get_active_power_direct_charge(grid, input_dict['hp'].loc[t], t)

    #get final q_mvar of hp
    #grid.net.load.loc[grid.hp_index, 'q_mvar'] = hp_controller.get_reactive_power(grid, input_dict['hp'].loc[t], t)
    if pf == True:
      grid.net.ext_grid.vm_pu = grid.get_vm_pu_ext_grid(grid)

    grid = curtail_controller.curtail(grid, t)

    return grid.net


### EnergeManagement 6 ###
class EnergyManagementStorage(EnergyManagementParent):
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
    Only used in scenario 6 to 8.

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

    # PV
    grid.net.sgen['p_mw'] = pv_controller.get_active_power(grid, input_dict['pv'].loc[t])
    grid.net.sgen['q_mvar'] = pv_controller.get_reactive_power(grid)

    # HH-Load
    grid.net.load.loc[grid.load_index, 'p_mw'] = input_dict['load_p'].loc[t].values
    grid.net.load.loc[grid.load_index, 'q_mvar'] = input_dict['load_q'].loc[t].values

    # direct
    grid.net.load.loc[grid.ev_index] = ev_controller.get_active_power_direct_charge(grid, t)
    grid.net.load.loc[grid.hp_index] = hp_controller.get_active_power_direct_charge(grid, input_dict['hp'].loc[t], t)
    grid.net.storage                 = bss_controller.get_active_power_direct_charge(grid, t)
    # linear
    grid.net.storage                 = bss_controller.get_active_power_linear_charge(grid, t)
    # trafo overload
    grid.net.storage                 = bss_controller.get_active_power_trafo_charge(grid, t)

    #get final q_mvar of hp
    #grid.net.load.loc[grid.hp_index, 'q_mvar'] = hp_controller.get_reactive_power(grid, input_dict['hp'].loc[t], t)

    grid.net.ext_grid.vm_pu = grid.get_vm_pu_ext_grid(grid)

    grid = curtail_controller.curtail(grid, t)

    return grid.net

### EnergeManagement 7, 8 ###
class EnergyManagementAdvanced(EnergyManagementParent):
  def __init__(self):
    super().__init__()
    self.time = 0

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
    Only used in scenario 6 to 8.

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

    # PV
    grid.net.sgen['p_mw'] = pv_controller.get_active_power(grid, input_dict['pv'].loc[t])
    grid.net.sgen['q_mvar'] = pv_controller.get_reactive_power(grid)

    # HH-Load
    grid.net.load.loc[grid.load_index, 'p_mw'] = input_dict['load_p'].loc[t].values
    grid.net.load.loc[grid.load_index, 'q_mvar'] = input_dict['load_q'].loc[t].values

    # direct
    grid.net.load.loc[grid.ev_index] = ev_controller.get_active_power_direct_charge(grid, t)
    grid.net.load.loc[grid.hp_index] = hp_controller.get_active_power_direct_charge(grid, input_dict['hp'].loc[t], t)
    grid.net.storage                 = bss_controller.get_active_power_direct_charge(grid, t)

    # linear
    grid.net.load.loc[grid.hp_index] = hp_controller.get_active_power_linear_charge(grid, input_dict['hp'].loc[t], t)
    grid.net.storage                 = bss_controller.get_active_power_linear_charge(grid, t)

    # pv excess
    grid.net.load.loc[grid.ev_index] = ev_controller.get_active_power_p_res_charge(grid, t)

    # trafo overload
    grid.net.load.loc[grid.ev_index] = ev_controller.get_active_power_trafo_charge(grid, t)
    grid.net.load.loc[grid.hp_index] = hp_controller.get_active_power_trafo_charge(grid, input_dict['hp'].loc[t], t)
    grid.net.storage                 = bss_controller.get_active_power_trafo_charge(grid, t)

    #get final q_mvar of hp
    #grid.net.load.loc[grid.hp_index, 'q_mvar'] = hp_controller.get_reactive_power(grid, input_dict['hp'].loc[t], t)

    grid.net.ext_grid.vm_pu = grid.get_vm_pu_ext_grid(grid)

    grid = curtail_controller.curtail(grid, t)

    return grid.net
