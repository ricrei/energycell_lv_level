#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Mar  4 13:38:06 2021

@author: paul
"""

import pandas as pd
import numpy as np

class HPstorages():
    """ HP-Storage creates and controls HP-Storage. """

    def __init__(self, grid, control_parameter):
        #print("Init HP-Storage")
        self.hp_storages = pd.DataFrame({
            'name': [],
            'bus': 0,
            'capacity': 0.0,
            'level': 0,
            'comfort_level': 0.0,
            'max_flow': 0.0
            })

        ## default parameters
        self.hp_stor_para = {'hp_max_capacity_mwh': 0,
                             'hp_TES_max_capacity_mwh': control_parameter['HP_TES_max_capacity_def_mwh'],#.0325,
                             'hp_building_capacity_mwh': 0.,
                             'hp_start_soc': control_parameter['HP_TES_start_soc'], #0.5, # 0-1
                             'hp_loss_per_s': control_parameter['HP_TES_loss_per_s'], #0.04 / 86400,   #4% per day / 86400s
                             'hp_max_p_kw': control_parameter['HP_max_p_kw'], #0.012, # in MW
                             'hp_cop': np.nan,
                             'upper_tes_reserve': control_parameter['HP_upper_TES_reserve'], #1., # default = 1
                             'lower_tes_reserve': control_parameter['HP_lower_TES_reserve']  #0 # default = 0
                            }

        ## Select HP_max_p due to the design point
        ## Depending on building-type select HP_thermal_power * oversizing_factor
        # SFH15
        if (grid.scenario[0] == 'A') :
          self.hp_stor_para['HP_max_p_kw'] = control_parameter['HP_dp_SFH15_p_kw'] * control_parameter['HP_max_p_oversizing']
        # SFH45
        elif (grid.scenario[0] == 'B') :
          self.hp_stor_para['HP_max_p_kw'] = control_parameter['HP_dp_SFH45_p_kw'] * control_parameter['HP_max_p_oversizing']
        # SFH100
        elif (grid.scenario[0] == 'C') :
          self.hp_stor_para['HP_max_p_kw'] = control_parameter['HP_dp_SFH100_p_kw'] * control_parameter['HP_max_p_oversizing']
        # default
        else :
          self.hp_stor_para['HP_max_p_kw'] = control_parameter['HP_max_p_kw'], #0.012, # in MW
        
        ## choose size of tes due to hp scenario digit
        # tes_small
        if (grid.scenario[3] == 6) :
          ## Sizing VDI4645 minimum, no heating water storage, only potable water storage
          self.hp_stor_para['hp_TES_max_capacity_mwh'] = 0.005  
          print('scenario:')
          print(grid.scenario[0], grid.scenario[3])
          print(self.hp_stor_para['HP_max_p_kw'])
          print(self.hp_stor_para['hp_TES_max_capacity_mwh'])
        # tes_medium
        elif (grid.scenario[3] == 7) :
          ## Sizing VDI 4645: hp_dp_p_kw  * 20l/kW_th * 1.632Wh/(Kg*K) * 10K
          self.hp_stor_para['hp_TES_max_capacity_mwh'] = \
            self.hp_stor_para['HP_max_p_kw'] / control_parameter['HP_max_p_oversizing'] \
              / 1000 * 20 * 1.632 * 10 
          ## add potable water storage 5kWh
          self.hp_stor_para['hp_TES_max_capacity_mwh'] += 0.005
          print('scenario:')
          print(grid.scenario[0], grid.scenario[3])
          print(self.hp_stor_para['HP_max_p_kw'])
          print(self.hp_stor_para['hp_TES_max_capacity_mwh'])
        # tes_large
        elif (grid.scenario[3] == 8) : 
          ## Sizing VDI 4645: hp_max_p_kw * 40l/kW_th * 3h EVU_Lock * 1.632Wh/(Kg*K) * 10K
          self.hp_stor_para['hp_TES_max_capacity_mwh'] = \
            self.hp_stor_para['HP_max_p_kw'] / control_parameter['HP_max_p_oversizing'] \
              / 1000 * 40 * 3 * 1.632 * 10
          ## add potable water storage 5kWh
          self.hp_stor_para['hp_TES_max_capacity_mwh'] += 0.005
          print('scenario:')
          print(grid.scenario[0], grid.scenario[3])
          print(self.hp_stor_para['HP_max_p_kw'])
          print(self.hp_stor_para['hp_TES_max_capacity_mwh'])
          # tes_xlarge
        elif (grid.scenario[3] == 9) : 
          ## Sizing VDI 4645: hp_max_p_kw * 40l/kW_th * 3h EVU_Lock * 1.632Wh/(Kg*K) * 10K
          self.hp_stor_para['hp_TES_max_capacity_mwh'] = \
            self.hp_stor_para['HP_max_p_kw'] / control_parameter['HP_max_p_oversizing'] \
              / 1000 * 60 * 3 * 1.632 * 10
          ## add potable water storage 5kWh
          self.hp_stor_para['hp_TES_max_capacity_mwh'] += 0.005
          print('scenario:')
          print(grid.scenario[0], grid.scenario[3])
          print(self.hp_stor_para['HP_max_p_kw'])
          print(self.hp_stor_para['hp_TES_max_capacity_mwh'])
        else :
          self.hp_stor_para['hp_TES_max_capacity_mwh'] = control_parameter['HP_TES_max_capacity_def_mwh']

        ## varies upper_tes_reserve depending on seasons
        if 'name' in grid.time_scope.keys():
          if grid.time_scope['name'] in ['winter', 'spring', 'autumn']:
            self.hp_stor_para['hp_building_capacity_mwh'] = control_parameter['HP_building_capacity_mwh']#.014
            if grid.time_scope['name'] in ['winter']:
              self.hp_stor_para['lower_tes_reserve'] = control_parameter['HP_lower_TES_reserve_winter'] #.1 # in 0-1
              self.hp_stor_para['hp_start_soc'] = control_parameter['HP_TES_start_soc_winter']#.25
          elif grid.time_scope['name'] == 'summer':
            self.hp_stor_para['upper_tes_reserve'] = control_parameter['HP_upper_TES_reserve_summer'] #.5 # in 0-1
            self.hp_stor_para['hp_start_soc'] = control_parameter['HP_TES_start_soc_summer']#.75


        self.hp_stor_para['hp_max_capacity_mwh'] = \
            self.hp_stor_para['hp_building_capacity_mwh'] \
          + self.hp_stor_para['hp_TES_max_capacity_mwh']
        
        self.intervall_in_seconds = grid.time_scope['intervall_in_seconds']

    def create_hp_storages(self, grid):
        '''
        Returns 0
        -------
        Search for HPs in net.load and add HP-Storage
        '''
        #print("Create HP-Storage")

        grid.net.load.loc[grid.hp_index, 'hp_max_capacity_mwh'] = \
            self.hp_stor_para['hp_max_capacity_mwh']
        
        grid.net.load.loc[grid.hp_index, 'hp_soc_mwh'] = \
            grid.net.load.loc[grid.hp_index, 'hp_max_capacity_mwh'] \
                * self.hp_stor_para['hp_start_soc']
        
        grid.net.load.loc[grid.hp_index, 'hp_loss_per_s'] = \
            self.hp_stor_para['hp_loss_per_s']
        
        grid.net.load.loc[grid.hp_index, 'hp_max_p_kw'] = \
            self.hp_stor_para['hp_max_p_kw']
        
        grid.net.load.loc[grid.hp_index, 'hp_cop'] = \
            self.hp_stor_para['hp_cop']

        #print(grid.net.load.loc[grid.hp_index])

        return 0

    def set_hp_max_power(self, hps, hp_soc_change, hp_th_demand):
        '''
        sets maximum power of heat_pump
        leads maximum chargable amount of energy
        -------
        Input hps - dataframe
        '''
        hp_soc_change[hp_soc_change + hp_th_demand \
          > self.hp_stor_para['hp_max_p_kw'] * (self.intervall_in_seconds / 3600)] = \
          self.hp_stor_para['hp_max_p_kw'] * (self.intervall_in_seconds / 3600) - hp_th_demand
        
        return hp_soc_change
   
      

    def set_limits(self, hps, hp_soc_change):
        '''
        sets max and minimum level of storages
        -------
        Input hps - dataframe
        '''
        
        ### storage full
        #limit increase hp_soc untill [hp_soc + soc_change > hp_max_capacity]
        hp_soc_change[hps.hp_soc_mwh + hp_soc_change > hps.hp_max_capacity_mwh] = \
            hps.hp_max_capacity_mwh[hps.hp_soc_mwh + hp_soc_change > hps.hp_max_capacity_mwh] - \
              hps.hp_soc_mwh[hps.hp_soc_mwh + hp_soc_change > hps.hp_max_capacity_mwh]

        ### storage emtpy
        #decrease hp_soc untill [hp_soc + soc_change < 0]
        hp_soc_change[hps.hp_soc_mwh + hp_soc_change < 0] =\
            -hps.hp_soc_mwh[hps.hp_soc_mwh + hp_soc_change < 0]
        
        return hp_soc_change
        
    def set_loss(self, hps):
        '''
        sets max and minimum level of storages
        -------
        Input hps - dataframe
        '''

        #calc loss in per due intervall in sec and loss in percent per s
        loss_per_intervall_in_per = self.intervall_in_seconds * self.hp_stor_para['hp_loss_per_s']
        #calc loss in mwh due hp_soc
        loss_in_mwh = hps.hp_soc_mwh * loss_per_intervall_in_per
        #decrease level
        hps.hp_soc_mwh -= loss_in_mwh
        hps.hp_tes_losses_th = loss_in_mwh
        
        #print('inter_in_s   ', self.intervall_in_seconds)
        #print('hp_loss__s   ', self.hp_stor_para['hp_loss_per_s'])
        #print('inter_in_s   ', loss_per_intervall_in_per)
        #print('loss         ', loss_in_mwh)
        #print('hpsoc   ', hps.hp_soc_mwh)
        
        return hps

    def get_capacity(self, grid, index):
        '''
        Returns capacity of storages by index
        -------
        Input grid
        index to identify storages
        '''
        
        return grid.net.load.hp_el_capacity_kwh[index]
        #return self.hp_storages.capacity[index]
    
