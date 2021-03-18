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

    def controll_hps_df(self, res_bus_load, load, sgen, tstamp, hp_stor_obj):
        """Zweiter Entwurf der Kontroll-Funktion für HPs.
        Monitor residual load above -1,5kW add 1,5kW HP in Buffer
        heat demand is set by demand curve
        Except to iteration try usage of DataFrame-functions"""
        # "bus_id-wise" feed in to

        # search for feeder in res_bus
        feeder = res_bus_load.loc[res_bus_load['p_mw'] < 0]
        # print(feeder.to_markdown())

        if( feeder.empty is False ):

            print('>>> Timestamp:', tstamp)
            # sorted storages by bus and group storage to set index to bus for add
            new_sorted = hp_stor_obj.hp_storages.sort_values(by='bus')
            hps_level = new_sorted.groupby(['bus']).sum().level

            hps_res = (hps_level - feeder.p_mw).dropna()
            print(hps_res.to_markdown())


    def controll_hps(self, res_bus_load, tstamp, sgen, load, pv_index,
                     load_index, hp_index, ev_index, hp_stor_obj):
        """Erster Entwurf der Kontroll-Funktion für HPs.
           Monitor residual load above -1,5kW add 1,5kW HP in Buffer
           heat demand is set by demand curve"""
        # "bus_id-wise" feed in to
        print('>>> Timestamp:', tstamp)
        
        
        for bus_id in range(0, len(res_bus_load.p_mw)-2):
        #for bus_id in range(hp_index.astype('int64')):
            f_feed_in = False
            f_feed_out = False
            
            # Get values from net.load values in [MW]
            resi_load = res_bus_load.p_mw[bus_id]
            static_hp_load = load.p_mw[hp_index[bus_id]]
            new_hp_load = load.p_mw[hp_index[bus_id]]

            # Get values from hp_storage values in [kWh]
            stor_level = hp_stor_obj.get_level(bus_id).values
            max_level = hp_stor_obj.get_capacity(bus_id).values

            print('Bus_Id:', bus_id)
            print('Residual_Load[MW]:', resi_load)
            print('stor_level[kWh]: ', stor_level, ' max_level[kWh]:', max_level)


            # if Residual_load negative (feed in to grid) feed_in to storage
            if((resi_load < 0) & (max_level > stor_level)): f_feed_in = True
            else: f_feed_in = False

            # if Residual_load positiv (feed from grid) feed_out from storage
            if((resi_load > 0) & (stor_level > 0)): f_feed_out = True
            else: f_feed_out = False

            if(f_feed_in):
                print('Feed in to storage -> HP_load_start:', new_hp_load)             
                #print(hp_storages.get_level(bus_id))

                # Set Max_Flow
                if(resi_load >= -0.0015):
                    # Calculate new HP-Load
                    new_hp_load = static_hp_load - resi_load

                    # Calculate feed_in per Timestep in kW
                    amount_feed_in = (-resi_load * 1000)/12

                else:
                    # Set static max Feed_In_Value
                    new_hp_load = static_hp_load + 0.0015
                    
                    # Calculate feed_in per Timestep in kW
                    amount_feed_in = (0.0015 * 1000)/12

                print('new_hp_load [MW]:', new_hp_load, ' amount_feed_in[kW]:', amount_feed_in)
                print('Stor_Level_old[kWh]: ', hp_stor_obj.get_level(bus_id).values)
                # Feed into storage
                hp_stor_obj.feed_in(bus_id = bus_id, energy = amount_feed_in)
                print('Stor_Level_new[kWh]:', hp_stor_obj.get_level(bus_id).values)

            if(f_feed_out):
                print('Feed out from storage -> HP_load_start:', new_hp_load)

                # Calculate feed_out_in per Timestep in kW
                amount_feed_out = (static_hp_load * 1000)/12
                new_hp_load = static_hp_load - (amount_feed_out/1000)*12        

                print('new_hp_load [MW]:', new_hp_load, ' amount_feed_out[kW]:', amount_feed_out)
                print('Stor_Level_old[kWh]: ', hp_stor_obj.get_level(bus_id).values)
                
                # Feed out from storage
                hp_stor_obj.feed_out(bus_id = bus_id, energy = amount_feed_out)
                print('Stor_Level_new[kWh]:', hp_stor_obj.get_level(bus_id).values)

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