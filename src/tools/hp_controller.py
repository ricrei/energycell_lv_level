#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Feb  3 12:58:22 2021

@author: Paul Oeser
"""

import datetime #Added by Paul


class HP_Controller():
    """Der HP_Controller steuert die Leistung der HPs."""

    def __init__(self):
        print("Init HP-Controller")

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

    def controll_hps(self, res_bus_load, tstamp, sgen, load, pv_index,
                     load_index, hp_index, ev_index):
        """Erster Entwurf der Kontroll-Funktion für HPs."""
        # Monitor residual load -> add 1kW HP in case of feed in
        for bus_id in range(0, len(res_bus_load.p_mw)-2):
            if(res_bus_load.p_mw[bus_id] <= 0):
                load.p_mw[hp_index[bus_id]] = load.p_mw[hp_index[bus_id]] + 0.001

class EVU_Controller():

    def __init__(self, start_time, stop_time):
        print("init")
        self.start_time = start_time
        self.stop_time = stop_time

    def control_hps(self, load, t, hp_index):
        # EVU_Lock morning
        if (t >= self.lock1_start_time) & (t < self.lock1_stop_time) : 
            print("\n timestamp:"); print(t)
            #element-wise access to hp -> evu_lock
            for access_counter in hp_index:
                load.p_mw[access_counter] = 0
                print(access_counter)


class Max_Load_Controller():

    def __init__(self, max_load):
        self.max_load = max_load

    def control_hps(self, load, t, hp_index):
        for access_counter in hp_index:
                if load.p_mw[access_counter] > self.max_load :
                    load.p_mw[access_counter] = self.max_load


#Intstanzierung mit Strategy pattern
#hp_controller = [
#        hp_cntr.HP_Controller(start, stop),
#        hp_cntr.Max_Load_Controller(max)
#    ]

#        for controller in hp_controller:
#            controller.control_hps(load, t, hp)
