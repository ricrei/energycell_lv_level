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

    def __init__(self):
        #print("Init HP-Storage")
        self.hp_storages = pd.DataFrame({
            'name': [],
            'bus': 0,
            'capacity': 0.0,
            'level': 0,
            'comfort_level': 0.0,
            'max_flow': 0.0
            })

        self.hp_stor_para = {'hp_max_capacity_mwh': 0.045,
                             'hp_start_soc': 0.5,
                             'hp_self_dis_per_day': 0.1,
                             'hp_max_p_kw': 0.01,
                             'hp_cop': 4}



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
        grid.net.load.loc[grid.hp_index, 'hp_self_dis_per_day'] = \
            self.hp_stor_para['hp_self_dis_per_day']
        grid.net.load.loc[grid.hp_index, 'hp_max_p_kw'] = \
            self.hp_stor_para['hp_max_p_kw']
        grid.net.load.loc[grid.hp_index, 'hp_cop'] = \
            self.hp_stor_para['hp_cop']

        #print(grid.net.load.loc[grid.hp_index])

        return 0

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
    