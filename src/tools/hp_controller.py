#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Feb  3 12:58:22 2021

@author: Paul Oeser
"""

import datetime #Added by Paul


class HP_Controller():
    
    
    def __init__(self):
        print("init")
        self.lock1_start_time = datetime.datetime.strptime('2017-01-17 10-45-00-+0100','%Y-%m-%d %H-%M-%S-%z')
        self.lock1_stop_time = datetime.datetime.strptime('2017-01-17 12-15-00-+0100','%Y-%m-%d %H-%M-%S-%z')
        self.lock2_start_time = datetime.datetime.strptime('2017-01-17 17-15-00-+0100','%Y-%m-%d %H-%M-%S-%z')
        self.lock2_stop_time = datetime.datetime.strptime('2017-01-17 18-45-00-+0100','%Y-%m-%d %H-%M-%S-%z')


    def evu_sperre(self, load, t, hp_index):
        # EVU_Lock morning
        if (t >= self.lock1_start_time) & (t < self.lock1_stop_time) : 
            print("\n timestamp:"); print(t)
            #element-wise access to hp -> evu_lock
            for access_counter in hp_index:
                load.p_mw[access_counter] = 0
                print(access_counter)

        # EVU_Lock afternoon
        if (t >= self.lock2_start_time) & (t < self.lock2_stop_time):
            print("\n timestamp:")
            print(t)
            # element-wise access to hp -> evu_lock
            for access_counter in hp_index:
                load.p_mw[access_counter] = 0
                print(access_counter)
