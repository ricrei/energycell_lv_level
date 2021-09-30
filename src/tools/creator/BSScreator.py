import numpy as np
import pandapower as pp

import tools.tools as tt
from tools.controller.BSScontroller import BSScontroller #neu

class BSScreator:

  def __init__(self, net_name): #net_name
        self.bss_para = {}
        self.net_name = net_name
        self.soc_max_brutto = 70
        self.soc_min_brutto = 30
        self.soc_percent = 0
        #self.sizing_factor = 0.6
        self.c_rate = 0.6

  ###########################################
  ### Create Loads at each bus for all HP ###
  ###########################################
  def create_bss_at_each_bus(self, grid): 
      # create bss at each bus 
      #max_e_mwh = grid.net.sgen.installed_power * self.sizing_factor # [MWh]
      #max_e_mwh = 0.02 #später raus
     # max_p_mw = 0.02 #max_e_mwh # [MW]
      #max_e_mwh = grid.net.sgen.installed_power * 10**(-3) * self.sizing_factor # [MWh]
      #max_p_mw = grid.net.sgen.installed_power * 10**(-3) # [MW] # später anpassen
      '''
      for index in grid.component_buses.index:
          pp.create_storage(grid.net, grid.net.load.loc[index, "bus"], \
                            p_mw = 0, \
                            max_e_mwh = max_e_mwh, \
                            soc_percent = self.soc_percent , \
                            name = 'bss_'+str(grid.net.load.loc[index, "bus"]), \
                            type = 'bss', \
                            max_p_mw = max_p_mw[])
      
      grid.net.storage['efficiency_storage'] = 0.9
      grid.net.storage['efficiency_inverter'] = 0.96
      grid.net.storage['efficiency_mppt'] = 0.98
      grid.net.storage['e_mwh'] =  0 ###
      grid.net.storage['max_e_mwh_brutto'] = max_e_mwh / ((self.soc_max_brutto - self.soc_min_brutto)/100)
      '''
      for index in grid.component_buses.index:
          pp.create_storage(grid.net, grid.net.load.loc[index, "bus"], \
                            p_mw = 0, \
                            max_e_mwh = grid.net.sgen.installed_power.loc[index] * 10**(-3) * self.c_rate, \
                            soc_percent = self.soc_percent , \
                            name = 'bss_'+str(grid.net.load.loc[index, "bus"]), \
                            type = 'bss', \
                            max_p_mw = grid.net.sgen.installed_power.loc[index] * 10**(-3))
      
      grid.net.storage['efficiency_storage'] = 0.9
      grid.net.storage['efficiency_inverter'] = 0.96
      grid.net.storage['efficiency_mppt'] = 0.98
      grid.net.storage['e_mwh'] =  0 ###
      grid.net.storage['max_e_mwh_brutto'] = grid.net.storage.max_e_mwh / ((self.soc_max_brutto - self.soc_min_brutto)/100)
      
      return grid
      
  
    #ec.grid.bss_controller.state_of_charge(grid)

  def create_bss_at_lvbb(self, grid): 
      # create  community bss at low voltage busbar (bus 0)
      max_e_mwh = grid.net.sgen.installed_power.sum() * 10**(-3) * self.c_rate # [MWh]
      max_p_mw = grid.net.sgen.installed_power.sum() * 10**(-3) # [MW] # später anpassen
      '''
      pp.create_storage(grid.net, 4 , p_mw=0,\
                            max_e_mwh=max_e_mwh, soc_percent=0 ,name='bss_'+str(4), type='bss')
      '''
      pp.create_storage(grid.net, grid.net.trafo.lv_bus.sum(), \
                        p_mw = 0, \
                        max_e_mwh = max_e_mwh, \
                        soc_percent = self.soc_percent , \
                        name = 'bss_'+str(grid.net.trafo.lv_bus.sum()), \
                        type = 'bss', \
                        max_p_mw = max_p_mw)
      
      grid.net.storage['efficiency_storage'] = 0.9
      grid.net.storage['efficiency_inverter'] = 0.96
      grid.net.storage['efficiency_mppt'] = 0.98
      grid.net.storage['max_e_mwh_brutto'] = max_e_mwh / ((self.soc_max_brutto - self.soc_min_brutto)/100) # anpassen
      
      return grid

  def create_bss_at_selected_buses(self, grid): 
      # create community bss at one or more buses  
      
      #sizing_factor =
      if self.net_name == "simbench_rural_1":
          selected_buses = [int(grid.net.trafo.lv_bus.sum())]
          hh_per_line = [0]
          print('No scenario for CBSS in power line implemented')# wird nicht ausgegeben
          #raise ValueError('No scenario for CBSS in power line implemented' )
      elif self.net_name == "simbench_rural_2":
          selected_buses = [9,19,46,75]
          hh_per_line = [48,45,141,63] 
      elif self.net_name == "simbench_rural_3":
          selected_buses = [74,93,95,108,111]
          hh_per_line = [66,30,63,84,72]
      elif self.net_name == "simbench_suburb_4":
          selected_buses = [2]
          hh_per_line = [81]
      elif self.net_name == "simbench_suburb_5":
          selected_buses = [2,10]
          hh_per_line = [102,111]
      
      i = 0
      for x in selected_buses:
          max_e_mwh = grid.net.sgen.installed_power.sum() * 10**(-3) * self.c_rate * hh_per_line[i]/sum(hh_per_line) # später noch
          max_e_mwh = np.nan_to_num(max_e_mwh)
          max_p_mw = grid.net.sgen.installed_power.sum() * 10**(-3) * hh_per_line[i]/sum(hh_per_line) # [MW] # später anpassen
          max_p_mw = np.nan_to_num(max_p_mw)
          pp.create_storage(grid.net, x, \
                            p_mw = 0,\
                            max_e_mwh = max_e_mwh, \
                            soc_percent = self.soc_percent ,\
                            name='bss_'+str(x), \
                            type='bss', \
                            max_p_mw = max_p_mw)
          i = i+1
            
      
      grid.net.storage['efficiency_storage'] = 0.9
      grid.net.storage['efficiency_inverter'] = 0.96
      grid.net.storage['efficiency_mppt'] = 0.98
      grid.net.storage['max_e_mwh_brutto'] = max_e_mwh / ((self.soc_max_brutto - self.soc_min_brutto)/100) # anpassen
      
      #grid.net.storage['location'] = selected_buses
      return grid

