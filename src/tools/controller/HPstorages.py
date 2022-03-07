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

        self.hp_stor_para = {'hp_el_capacity_mwh': 0.015,
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

        grid.net.load.loc[grid.hp_index, 'hp_el_capacity_mwh'] = \
            self.hp_stor_para['hp_el_capacity_mwh']
        grid.net.load.loc[grid.hp_index, 'hp_soc_mwh'] = \
            grid.net.load.loc[grid.hp_index, 'hp_el_capacity_mwh'] \
                * self.hp_stor_para['hp_start_soc']
        grid.net.load.loc[grid.hp_index, 'hp_self_dis_per_day'] = \
            self.hp_stor_para['hp_self_dis_per_day']
        grid.net.load.loc[grid.hp_index, 'hp_max_p_kw'] = \
            self.hp_stor_para['hp_max_p_kw']
        grid.net.load.loc[grid.hp_index, 'hp_cop'] = \
            self.hp_stor_para['hp_cop']

        #print(grid.net.load.loc[grid.hp_index])

        return 0

    def get_level(self, grid, index):
        '''hp_start_soc
        Returns level of storages by index
        -------
        Input grid
        index to identify storages
        '''
        
        return grid.net.load.hp_soc_kwh[index]
        #return self.hp_storages.level[index]
        

    def get_capacity(self, grid, index):
        '''
        Returns capacity of storages by index
        -------
        Input grid
        index to identify storages
        '''
        
        return grid.net.load.hp_el_capacity_kwh[index]
        #return self.hp_storages.capacity[index]

    def greater(self, para1, para2):
        '''
        Returns series of compared entries
        -------
        Input para1
        Input para2
        '''
        greater = np.less(self.hp_storages.get(para1), 
                          self.hp_storages.get(para2))
        return greater        


    def feed_in(self, grid, indexer, energy):
        '''
        Returns new_level as a result of feed_in
        -------
        input: bus_id to identify storage, amount of energy in kWh per timestep
        '''
        
        self.hp_storages.level[indexer] = self.hp_storages.level[indexer] + energy * 1000
        
        grid.net.load.loc[grid.hp_index].hp_soc_kwh[indexer] = \
            grid.net.load.loc[grid.hp_index].hp_soc_kwh[indexer] + energy * 1000
        
        return 0

    def feed_out(self, grid, indexer, energy):
        '''
        Returns new_level as a result of feed_out
        -------
        input: bus_id to identify storage, amount of energy in kWh per timestep
        '''
        
        self.hp_storages.level[indexer] = self.hp_storages.level[indexer] - energy * 1000
        grid.net.load.loc[grid.hp_index].hp_soc_kwh[indexer] = \
            grid.net.load.loc[grid.hp_index].hp_soc_kwh[indexer] + energy * 1000

        return 0
    