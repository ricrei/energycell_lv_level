#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Feb  3 12:58:22 2021

@author: Paul Oeser
"""

import datetime

class HP_Controller():
    """Der HP_Controller steuert die Leistung der HPs."""

    def __init__(self):
        print("Init HP-Controller")

    def controll_hps(self, res_bus_load, tstamp, sgen, load, pv_index,
                     load_index, hp_index, ev_index, hp_storages):
        """Erster Entwurf der Kontroll-Funktion für HPs.
           Monitor residual load -> add 1kW HP in case of feed in"""
        # "bus_id-wise" feed in to
        print('>>> Timestamp:', tstamp)
        
        for bus_id in range(0, len(res_bus_load.p_mw)-2):
            f_feed_in = False
            f_feed_out = False

            resi_load = res_bus_load.p_mw[bus_id]
            static_hp_load = load.p_mw[hp_index[bus_id]]
            new_hp_load = load.p_mw[hp_index[bus_id]]

            print('Bus_Id:', bus_id)
            print(resi_load)



            # if Residual_load negative (feed in to grid) fill into storage
            if(resi_load < 0): f_feed_in = True
            else: f_feed_in = False

            if(f_feed_in):
                print('Feed in storage -> HP_load_start', new_hp_load)             
                #print(hp_storages.get_level(bus_id))
                
                #Calculate new HP-Load
                new_hp_load = static_hp_load - resi_load
                
                # Calculate feed_in per Timestep in kW
                amount_feed_in = (-resi_load * 1000)/12
                level = hp_storages.get_level(bus_id).values
                print('Level_old:', level)
#                level = level+amount_feed_in
                print('Level_new:', level)                

                '''
                if(resi_load <= -0.001):
                    new_hp_load = static_hp_load - resi_load

                else:
                    new_hp_load = static_hp_load + 0.001
                '''

                print('End Feed in stor -> new_hp_load ', new_hp_load)

            load.p_mw[hp_index[bus_id]] = new_hp_load



'''
class Max_Load_Controller():

    def __init__(self, max_load):
        self.max_load = max_load

    def control_hps(self, load, t, hp_index):
        for access_counter in hp_index:
                if (load.p_mw[access_counter] > self.max_load):
                    load.p_mw[access_counter] = self.max_load
                    
    def get_resi_load(self, sgen, load, pv_index,
                 load_index, hp_index, ev_index):
    """ Calculate residual_load per timestep. """
    resi_load = []

    for access_counter in range(13):
        resi_load.append([load.p_mw[load_index[access_counter]]
                     + load.p_mw[hp_index[access_counter]]
                     + load.p_mw[ev_index[access_counter]]
                     - sgen.p_mw[pv_index[access_counter]]])

    return resi_load
'''

#Intstanzierung mit Strategy pattern
#hp_controller = [
#        hp_cntr.HP_Controller(start, stop),
#        hp_cntr.Max_Load_Controller(max)
#    ]

#        for controller in hp_controller:
#            controller.control_hps(load, t, hp)

'''
class EVU_Controller():

    def __init__(self, start_time, stop_time):
        print("init")
        self.start_time = start_time
        self.stop_time = stop_time

    def control_hps(self, load, t, hp_index):
        # EVU_Lock morning
        if (t >= self.start_time) & (t < self.stop_time) : 
            print("\n timestamp:"); print(t)
            #element-wise access to hp -> evu_lock
            for access_counter in hp_index:
                load.p_mw[access_counter] = 0
                print(access_counter)
'''