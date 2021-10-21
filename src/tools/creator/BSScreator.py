import numpy as np
import pandapower as pp

import tools.tools as tt
from tools.controller.BSScontroller import BSScontroller

class BSScreator:

  def __init__(self, net_name, grid): #net_name
        self.bss_para = {}
        self.net_name = net_name
        self.efficiency_AC2Bat = 0.952 # für jetzt
        self.efficiency_Bat2AC = 0.949 # für jetzt
        self.efficiency_storage = 0.915
        self.soc_max_brutto = 80
        self.soc_min_brutto = 20
        self.soc_percent = 0
        self.sizing_factor = 0.6
        self.i_max_a = 270 # wahl i_max entsprechend des gewählten netzes implementieren. Auch für Kerber?
        self.p_max_feeder_mw = self.i_max_a * grid.net.trafo.vn_lv_kv.loc[0] * 1.1 * 10**(-3) 

  ###########################################
  ### Create Loads at each bus for all HP ### # anpassen
  ###########################################
  def create_bss_at_each_bus(self, grid): 
      # create bss at each bus 

      for index in grid.component_buses.index:
          pp.create_storage(grid.net, grid.net.load.loc[index, "bus"], \
                            p_mw = 0, \
                            max_e_mwh = grid.net.sgen.installed_power.loc[index] * 10**(-3), \
                            soc_percent = self.soc_percent , \
                            name = 'bss_'+str(grid.net.load.loc[index, "bus"]), \
                            type = 'bss', \
                            max_p_mw = grid.net.sgen.installed_power.loc[index] * self.sizing_factor * 10**(-3))
      
      grid.net.storage['efficiency_AC2Bat'] = self.efficiency_AC2Bat # für jetzt  
      grid.net.storage['efficiency_Bat2AC'] = self.efficiency_Bat2AC
      grid.net.storage['efficiency_storage'] = self.efficiency_storage
      #grid.net.storage['efficiency_inverter'] = 0.96
      #grid.net.storage['efficiency_mppt'] = 0.98
      grid.net.storage['e_mwh'] =  0 ###
      grid.net.storage['max_e_mwh_brutto'] = grid.net.storage.max_e_mwh / ((self.soc_max_brutto - self.soc_min_brutto)/100)

      return grid
      

  def create_bss_at_lvbb(self, grid): 
      # create  community bss at low voltage busbar
      
      max_e_mwh = grid.net.sgen.installed_power.sum() * 10**(-3) # [MWh]
      max_p_mw = grid.net.sgen.installed_power.sum() * self.sizing_factor * 10**(-3) # [MW] # später anpassen
      #max_p_mw = min(max_p_mw, self.p_max_feeder_mw * grid.feeder['n_feeder'])
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
      
      grid.net.storage['efficiency_AC2Bat'] = self.efficiency_AC2Bat # für jetzt  
      grid.net.storage['efficiency_Bat2AC'] = self.efficiency_Bat2AC
      grid.net.storage['efficiency_storage'] = self.efficiency_storage
      #grid.net.storage['efficiency_storage'] = 0.9
      #grid.net.storage['efficiency_inverter'] = 0.96
      #grid.net.storage['efficiency_mppt'] = 0.98
      grid.net.storage['e_mwh'] =  0 ###
      grid.net.storage['max_e_mwh_brutto'] = max_e_mwh / ((self.soc_max_brutto - self.soc_min_brutto)/100) # anpassen
      return grid

  def create_bss_at_selected_buses(self, grid): 
      # create community bss at one or more buses  

      if self.net_name == "simbench_rural_1":
          selected_buses = [int(grid.net.trafo.lv_bus.sum())]
          hh_per_line = [0] # per feeder?
          print('No scenario for CBSS in power line implemented')# wird nicht ausgegeben
          #raise ValueError('No scenario for CBSS in power line implemented' )
      elif self.net_name == "simbench_rural_2":
          selected_buses = [9,19,46,75]#[9,19,46,42]#[9,19,46,75] 75!!! 75 austauschen --> 42 (verworfen)
          hh_per_line = [48,45,141,63] 
      elif self.net_name == "simbench_rural_3":
          selected_buses = [74,93,95,108,111]#[75,93,95,108,111]#[74,93,95,108,111] #74 austauschen --> 75(verworfen)
          hh_per_line = [66,30,63,84,72]
      elif self.net_name == "simbench_suburb_4":
          selected_buses = [2]
          hh_per_line = [81]
      elif self.net_name == "simbench_suburb_5":
          selected_buses = [2,10]#[79,56] # beide austauschen [2,10] --> [79,56] (verworfen)
          hh_per_line = [102,111]
      
      i = 0
      for x in selected_buses:
          max_e_mwh = grid.net.sgen.installed_power.sum() * 10**(-3) * hh_per_line[i]/sum(hh_per_line) # später noch
          max_e_mwh = np.nan_to_num(max_e_mwh)
          max_p_mw = grid.net.sgen.installed_power.sum() * self.sizing_factor * 10**(-3) * hh_per_line[i]/sum(hh_per_line) # [MW] # später anpassen
          max_p_mw = np.nan_to_num(max_p_mw)
          #max_p_mw = min(max_p_mw, self.p_max_feeder_mw * 2)
          pp.create_storage(grid.net, x, \
                            p_mw = 0,\
                            max_e_mwh = max_e_mwh, \
                            soc_percent = self.soc_percent ,\
                            name='bss_'+str(x), \
                            type='bss', \
                            max_p_mw = max_p_mw)
          i = i+1
            
      grid.net.storage['efficiency_AC2Bat'] = self.efficiency_AC2Bat # für jetzt  
      grid.net.storage['efficiency_Bat2AC'] = self.efficiency_Bat2AC
      grid.net.storage['efficiency_storage'] = self.efficiency_storage
      #grid.net.storage['efficiency_storage'] = 0.9
      #grid.net.storage['efficiency_inverter'] = 0.96
      #grid.net.storage['efficiency_mppt'] = 0.98
      grid.net.storage['e_mwh'] =  0 ###
      grid.net.storage['max_e_mwh_brutto'] = max_e_mwh / ((self.soc_max_brutto - self.soc_min_brutto)/100) # anpassen
      return grid

