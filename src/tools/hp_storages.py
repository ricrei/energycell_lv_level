#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Mar  4 13:38:06 2021

@author: sputn1k
"""

import pandas as pd

class HP_Storage():
    """ HP-Storage creates and controls HP-Storage. """

    def __init__(self):
        print("Init HP-Storage")
        self.hp_storages = pd.DataFrame({
            'name': [],
            'bus': 0,
            'capacity': 0.0,
            'level': 0,
            'max_flow': 0.0
            })

        # Defines in kW
        self.hp_stor_para = {'el_capacity': [10.0, 5.0, 3.0],
                             'start_level': [3.0, 2.0, 1.0],
                             'max_flow': [2, 1, 0.5]}

        # Access_list for hp_storages_indexed by bus_id
        self.hp_storage_index = self.get_hp_stor_index()

    def create_hp_storages(self, net):
        '''
        Returns 0
        -------
        Search for HPs in net.load and add HP-Storage
        '''

        for index in net.load.index:
            if str.startswith(net.load.loc[index].type, 'hp_'):
               new_storage = {'name': 'hp_st_'+str(net.load.loc[index].bus),
                              'bus': net.load.loc[index].bus,
                              'capacity': self.hp_stor_para.get('el_capacity')[0],
                              'level':    self.hp_stor_para.get('start_level')[0],
                              'max_flow': self.hp_stor_para.get('max_flow')[0],}

               self.hp_storages = self.hp_storages.append(new_storage, ignore_index=True)

        # Access_list for hp_storages_indexed by bus_id
        self.hp_storage_index = self.get_hp_stor_index()

        print("Create HP-Storage")
        # print(self.hp_storage_index_index)

        return self.hp_storage_index

    def get_level(self, bus_id):
        '''
        Returns level of specific storage
        -------
        Input bus_id to identify storage
        '''
        return self.hp_storages.level[self.hp_storage_index[bus_id]]

    def get_capacity(self, bus_id):
        '''
        Returns capacity of specific storage
        -------
        Input bus_id
        '''
        return self.hp_storages.capacity[self.hp_storage_index[bus_id]]

    def feed_in(self, bus_id, energy):
        '''
        Returns new_level as a result of feed_in
        -------
        input: bus_id to identify storage, amount of energy in kWh per timestep
        '''
        new_level = self.hp_storages.loc[self.hp_storage_index
                                                  [bus_id]].level + energy
        self.hp_storages.loc[self.hp_storage_index
                                        [bus_id], 'level'] = new_level
        return new_level

    def feed_out(self, bus_id, energy):
        '''
        Returns new_level as a result of feed_out
        -------
        input: bus_id to identify storage, amount of energy in kWh per timestep
        '''
        new_level = self.hp_storages.loc[self.hp_storage_index
                                                  [bus_id]].level - energy
        self.hp_storages.loc[self.hp_storage_index
                                        [bus_id], 'level'] = new_level    
        return new_level
    
    def get_hp_stor_index(self):
        
        '''
        Returns List indexed by bus_id for hp-storages
        to access storages by given bus_id
        -------
        input hp_storage

        '''
        hp_stor_index = []
        
        # Watch in hp_storages for inverted bus_id with isin()
        # Result is a list with the matched row shown true
        # Finally is list with all bus_id willbe created
        for i in range(len(self.hp_storages)):
            temp_list = self.hp_storages.bus.isin([i])
            #print(temp_list)
            hp_stor_index.append(list(temp_list[temp_list == True].index))
            #print(hp_stor_index)

        return hp_stor_index
