import numpy as np
import pandas as pd
import pandapower as pp

import tools.tools as tt
from tools.controller.BSScontroller import BSScontroller

class BSScreator:

  def __init__(self, grid, control_parameter, grid_analysis):
        self.bss_para = {}
        if grid_analysis == True:
            self.net_name = grid.net_name
        self.efficiency_AC2Bat = control_parameter['BSS_efficiency_AC2Bat']#0.953
        self.efficiency_Bat2AC = control_parameter['BSS_efficiency_Bat2AC']#0.955
        self.efficiency_storage = control_parameter['BSS_efficiency_storage']#0.959
        self.soc_max_brutto = 80
        self.soc_min_brutto = 20
        self.soc_percent =  control_parameter['BSS_start_soc_percent']#50
        self.soc_percent_winter =  control_parameter['BSS_start_soc_percent_winter']#25
        self.soc_percent_summer =  control_parameter['BSS_start_soc_percent_summer']#75
        self.sizing_factor = control_parameter['BSS_sizing_factor_power_to_capacity']#.75    # kW_WR,BSS / kWh_BSS
        self.sizing_factor_bss_to_pv = control_parameter['BSS_sizing_factor_bss_to_pv']#.75  # kWh_BSS   / kW_PV

        if 'name' in grid.time_scope.keys():
          if grid.time_scope['name'] == 'winter':
            self.soc_percent = self.soc_percent_winter         # in %
          if grid.time_scope['name'] == 'summer':
            self.soc_percent = self.soc_percent_summer         # in %

        # safe storage place in stored csv
        if grid.scenario[0] in [1 ,2, 3, 4, 5, 7]:
          self.soc_percent = np.nan
        if (grid_analysis == False) and (grid.scenario[2] == 5):
            raise ValueError('Hint: Selected scenario not valid. BSSs cannot be connected to a '
                             'feeder if simulations are conducted without power flow calculations '
                             'and no power grid is available')

  #########################################
  ### Mastermethod: choose bss position ###
  #########################################
  def create_bss(self, grid, bss_control):
        if bss_control in [None, 'direct', 'household-oriented_feed-in_damping', 'grid-oriented_feed-in_damping_HH']:
          grid = self.create_bss_at_each_bus(grid)
        elif bss_control == 'grid-oriented_feed-in_damping_LVbus':
          grid = self.create_bss_at_lvbb(grid)
        elif bss_control == 'grid-oriented_feed-in_damping_feeder':
          grid = self.create_bss_at_selected_buses(grid)

        return grid

  ###########################################
  ### Create Loads at each bus for all HP ### # anpassen
  ###########################################
  def create_bss_at_each_bus(self, grid): 
      # load bss sizes
      if grid.scenario[0] == 9:
        df = pd.read_csv('input-files/'+'20_bss_sizes.csv', delimiter = ',', low_memory=False).drop('Unnamed: 0', axis=1)

        dict_grid = {
          "simbench_rural_1" : 7,
          "simbench_rural_2" : 8,
          "simbench_rural_3" : 9,
          "simbench_suburb_4" : 10,
          "simbench_suburb_5" : 11,
        }

        num = dict_grid[grid.net_name]
      
        bss_size = df[df.grid == num]['max_bss_capa'].reset_index().drop('index', axis=1)

        # create bss at each bus
        for index in grid.component_buses.index:
          #print(str(index) + ' : ' + str(bss_size.loc[index].values[0]))
          pp.create_storage(grid.net, grid.net.load.loc[index, "bus"], \
                            p_mw = 0, \
                            max_e_mwh = bss_size.loc[index].values[0] * 10**(-3), \
                            soc_percent = self.soc_percent , \
                            name = 'bss_'+str(grid.net.load.loc[index, "bus"]), \
                            type = 'bss', \
                            max_p_mw = bss_size.loc[index].values[0] * self.sizing_factor * 10**(-3))

      else:
        # create bss at each bus
        for index in grid.component_buses.index:
          pp.create_storage(grid.net, grid.net.load.loc[index, "bus"], \
                            p_mw = 0, \
                            max_e_mwh = grid.net.sgen.installed_power.loc[index] * 10**(-3) * self.sizing_factor_bss_to_pv, \
                            soc_percent = self.soc_percent , \
                            name = 'bss_'+str(grid.net.load.loc[index, "bus"]), \
                            type = 'bss', \
                            max_p_mw = grid.net.sgen.installed_power.loc[index] * self.sizing_factor * 10**(-3) * self.sizing_factor_bss_to_pv)
      
      grid.net.storage['efficiency_AC2Bat'] = self.efficiency_AC2Bat # für jetzt  
      grid.net.storage['efficiency_Bat2AC'] = self.efficiency_Bat2AC
      grid.net.storage['efficiency_storage'] = self.efficiency_storage
      self.e_mwh_start = self.soc_percent/100 * grid.net.storage.max_e_mwh 
      grid.net.storage['e_mwh'] =  self.e_mwh_start
      grid.net.storage['max_e_mwh_brutto'] = grid.net.storage.max_e_mwh / ((self.soc_max_brutto - self.soc_min_brutto)/100)
      grid.net.storage['p_mw_flex'] =  0

      return grid
      

  def create_bss_at_lvbb(self, grid): 
      # create  community bss at low voltage busbar
      max_e_mwh = grid.net.sgen.installed_power.sum() * 10**(-3) * self.sizing_factor_bss_to_pv# [MWh] 
      max_p_mw = grid.net.sgen.installed_power.sum() * self.sizing_factor * 10**(-3) * self.sizing_factor_bss_to_pv# [MW]

      pp.create_storage(grid.net, grid.net.trafo.lv_bus[0], \
                        p_mw = 0, \
                        max_e_mwh = max_e_mwh, \
                        soc_percent = self.soc_percent , \
                        name = 'bss_'+str(grid.net.trafo.lv_bus.sum()), \
                        type = 'bss', \
                        max_p_mw = max_p_mw)
      
      grid.net.storage['efficiency_AC2Bat'] = self.efficiency_AC2Bat # für jetzt  
      grid.net.storage['efficiency_Bat2AC'] = self.efficiency_Bat2AC
      grid.net.storage['efficiency_storage'] = self.efficiency_storage
      self.e_mwh_start = self.soc_percent/100 * grid.net.storage.max_e_mwh 
      grid.net.storage['e_mwh'] =  self.e_mwh_start ###
      grid.net.storage['max_e_mwh_brutto'] = max_e_mwh / ((self.soc_max_brutto - self.soc_min_brutto)/100) # anpassen
      grid.net.storage['p_mw_flex'] =  0

      return grid

  def create_bss_at_selected_buses(self, grid): 
      # create community bss at one or more buses        
      if self.net_name == "simbench_rural_1":
          selected_buses = [4]#[int(grid.net.trafo.lv_bus.sum())] # The end of the longest feeder
          hh_per_line = [5]
          #print('No scenario for CBSS in power line implemented')# wird nicht ausgegeben
          #raise ValueError('No scenario for CBSS in power line implemented' )
      elif self.net_name == "simbench_rural_2":
          selected_buses = [9,19,46,75]
          #hh_per_line = [48,45,141,63] Falsche Zuordnung
          hh_per_line = [63,48,45,141]
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
          max_e_mwh = grid.net.sgen.installed_power.sum() * 10**(-3) * hh_per_line[i]/sum(hh_per_line) * self.sizing_factor_bss_to_pv# später noch
          max_e_mwh = np.nan_to_num(max_e_mwh)
          max_p_mw = grid.net.sgen.installed_power.sum() * self.sizing_factor * 10**(-3) * hh_per_line[i]/sum(hh_per_line) * self.sizing_factor_bss_to_pv# [MW] # später anpassen
          max_p_mw = np.nan_to_num(max_p_mw)
          pp.create_storage(grid.net, x, \
                            p_mw = 0,\
                            max_e_mwh = max_e_mwh, \
                            soc_percent = self.soc_percent ,\
                            name='bss_'+str(x), \
                            type='bss', \
                            max_p_mw = max_p_mw)
          i = i+1
            
      grid.net.storage['efficiency_AC2Bat'] = self.efficiency_AC2Bat 
      grid.net.storage['efficiency_Bat2AC'] = self.efficiency_Bat2AC
      grid.net.storage['efficiency_storage'] = self.efficiency_storage
      self.e_mwh_start = self.soc_percent/100 * grid.net.storage.max_e_mwh 
      grid.net.storage['e_mwh'] =  self.e_mwh_start
      grid.net.storage['max_e_mwh_brutto'] = max_e_mwh / ((self.soc_max_brutto - self.soc_min_brutto)/100)
      grid.net.storage['p_mw_flex'] =  0

      return grid

