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
        print("Init HP-Storage")
        self.hp_storages = pd.DataFrame({
            'name': [],
            'bus': 0,
            'capacity': 0.0,
            'level': 0,
            'comfort_level': 0.0,
            'max_flow': 0.0
            })

        # Defines in kW
        self.hp_stor_para = {'el_capacity': [10.0, 5.0, 3.0],
                             'start_level': [5.0, 3.0, 1.0],
                             'max_flow': [2, 1, 0.5]}

    def create_hp_storages(self, grid):
        '''
        Returns 0
        -------
        Search for HPs in net.load and add HP-Storage
        '''
        print("Create HP-Storage")
        
        self.hp_storages['name'] = grid.net.load.loc[grid.hp_index, 'name']
        self.hp_storages['bus'] = grid.net.load.loc[grid.hp_index, 'bus']
        self.hp_storages['capacity'] = self.hp_stor_para.get('el_capacity')[0]
        self.hp_storages['level'] = self.hp_stor_para.get('start_level')[0]
        self.hp_storages['max_flow'] = self.hp_stor_para.get('max_flow')[0]

        self.hp_storages['comfort_level'] = self.hp_storages['capacity'] * 0.7
        
        print(self.hp_storages)
        
        return 0

    def get_level(self, grid, index):
        '''
        Returns level of storages by index
        -------
        Input grid
        index to identify storages
        '''
        
        return self.hp_storages.level[index]

    def get_capacity(self, grid, index):
        '''
        Returns capacity of storages by index
        -------
        Input grid
        index to identify storages
        '''
        return self.hp_storages.capacity[index]

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
        
        return 0

    def feed_out(self, grid, indexer, energy):
        '''
        Returns new_level as a result of feed_out
        -------
        input: bus_id to identify storage, amount of energy in kWh per timestep
        '''
        
        self.hp_storages.level[indexer] = self.hp_storages.level[indexer] - energy * 1000

        #self.hp_storages.level = self.hp_storages.level - energy * 1000

        return 0
    