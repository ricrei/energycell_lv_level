#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Jul 15 10:51:49 2020

@author: ricardo
"""

import os
import csv
import time
import numpy as np
import pandas as pd
import pandapower as pp
import pandapower.networks as pn
#import pandapower.plotting.plotly as ppply
import simbench as sb
import tools.progress as prog

import bz2
#import pickle
import _pickle as cPickle

class EnergyCell():
    
    def __init__(self, net_name, set_hp, set_ev, set_pv, start_time, end_time, t_freq):
        self.run_time('start')
        self.net_name = net_name
        self.set_hp = set_hp
        self.set_ev = set_ev
        self.set_pv = set_pv
        self.output_dir = os.path.join("./", "output-files/"+str(net_name)+"/"+start_time[0:10]+"_"+end_time[0:10]+"_"+t_freq+"/")

        # installed PV-power per roof-top side in kW, rural:18kW, village:16.7kW, suburban:11.6kW
        # rate: frequency of occurrence of pv-orientation
        self.pv_para = {'orientation' : [90, 100, 110, 120, 130, 140, 150, 160, 170, 180, 190, 200, 210, 220, 230, 240, 250, 260],
                        'rate' : pd.DataFrame([10.8, 4.8, 4.4, 4, 4, 4.4, 5.2, 6.3, 6.3, 10.8, 4.9, 4.7, 4.3, 4, 4.3, 5, 5.9, 5.9]),
                        'installed_power_scaling' : [2, 2, 2, 2, 2, 1, 1, 1, 1, 1, 1, 1, 1, 1, 2, 2, 2, 2],
                        'power_rural' : 18, 'power_village' : 16.7, 'power_suburban' : 11.6, 'power_urban': 10,
                        'cos_phi' : .95}
        #todo: power urban has to be verified

        self.hp_para = {'building_type' : ['DE_HEF33', 'DE_HEF34', 'DE_HMF33', 'DE_HMF34'],
                        'heatpump_type' : ['Air', 'Ground'],
                        'hp_types' : [],
                        'cos_phi' : .95}
        self.hp_para['sin_phi'] = np.sin(np.arccos(self.hp_para['cos_phi']))

        self.ev_para = {'ev_types' : []}

        self.create_net()
        self.adjust_input_dataset(start_time, end_time, t_freq)
        self.create_output_dir()
    
    ######################
    ### create network ###
    ######################
    def create_net(self):
        print('Create grid ...')
        # create net: only load without pv
        if self.net_name == "kerber_rural_1":
            self.net = pn.create_kerber_landnetz_freileitung_1()
            self.category = 'rural'
        elif self.net_name == "kerber_rural_2":
            self.net = pn.create_kerber_landnetz_freileitung_2()
            self.category = 'rural'
        elif self.net_name == "kerber_rural_3":
            self.net = pn.create_kerber_landnetz_kabel_1()
            self.category = 'rural'
        elif self.net_name == "kerber_rural_4":
            self.net = pn.create_kerber_landnetz_kabel_2()
            self.category = 'rural'
        elif self.net_name == "kerber_village":
            self.net = pn.create_kerber_dorfnetz()
            self.category = 'village'
        elif self.net_name == "kerber_suburb_1":
            self.net = pn.create_kerber_vorstadtnetz_kabel_1()
            self.category = 'suburban'
        elif self.net_name == "kerber_suburb_2":
            self.net = pn.create_kerber_vorstadtnetz_kabel_2()
            self.category = 'suburban'
        elif self.net_name == "simbench_rural_1":
            self.net = sb.get_simbench_net('1-LV-rural1--0-sw')
            self.category = 'rural'
        elif self.net_name == "simbench_rural_2":
            self.net = sb.get_simbench_net('1-LV-rural2--0-sw')
            self.category = 'rural'
        elif self.net_name == "simbench_rural_3":
            self.net = sb.get_simbench_net('1-LV-rural3--0-sw')
            self.category = 'rural'
        elif self.net_name == "simbench_suburb_4":
            self.net = sb.get_simbench_net('1-LV-semiurb4--0-sw')
            self.category = 'suburban'
        elif self.net_name == "simbench_suburb_5":
            self.net = sb.get_simbench_net('1-LV-semiurb5--0-sw')
            self.category = 'suburban'
        elif self.net_name == "simbench_urban_6":
            self.net = sb.get_simbench_net('1-LV-urban6--0-sw')
            self.category = 'urban'
        else:
            print('Hint: No Network found. Please check net_name')
        print('Grid: ' + str(self.net_name) + ', Category: ' + str(self.category))

        # Set vm_pu of external grid
        #print(self.net.ext_grid.vm_pu)
        self.net.ext_grid.vm_pu = 1.025

        # if there are any sgen's within the original network -> remove them first
        for index in self.net.sgen.index:
          self.net.sgen.drop(index=index, inplace=True)

        # calculate distribution of pv systems with different orientation
        n_pv_systems = self.net.load.index.max() + 1
        pv_orientation_proberbility = self.pv_para['rate']/100
        n_pv_systems_orientation = pd.DataFrame(columns=['orientation','amount', 'decimal_amount', 'final_amount'])
        n_pv_systems_orientation['orientation'] = self.pv_para['orientation']      
        n_pv_systems_orientation['amount'] = n_pv_systems * pv_orientation_proberbility
        n_pv_systems_orientation['final_amount'] = n_pv_systems_orientation['amount'].apply(np.floor)
        n_pv_systems_orientation['decimal_amount'] = n_pv_systems_orientation['amount'] - n_pv_systems_orientation['final_amount']
        n_pv_systems_left = n_pv_systems - n_pv_systems_orientation['final_amount'].sum()
      
        n_pv_systems_orientation = n_pv_systems_orientation.sort_values(by=['decimal_amount'], ascending=False).reset_index(drop=True)

        i = 0
        while n_pv_systems_left > 0:
          n_pv_systems_orientation['final_amount'].loc[i] += 1
          n_pv_systems_left -= 1
          i += 1
        n_pv_systems_orientation = n_pv_systems_orientation.sort_values(by=['orientation'], ascending=True).reset_index(drop=True)
        n_pv_systems_to_distribute = n_pv_systems_orientation[['orientation', 'final_amount']]

        # create sgen per load and set all values to zero
        # asign pv-orientaiton to every sgen
        if self.set_pv == True:
            j = 0
            for index in self.net.load.index:
                # create PV sgen at every load
                pp.create_sgen(self.net, self.net.load.loc[index, "bus"], 0.0)
                self.net.load.loc[index, "p_mw"] = 0.0
                # asign pv-orientation to every PV sgen
                if n_pv_systems_to_distribute.final_amount.sum() > 0:
                  if index%10 == 0 and n_pv_systems_to_distribute['final_amount'].loc[9] > 0:
                    self.net.sgen.type.loc[index] = 'pv_180'
                    n_pv_systems_to_distribute['final_amount'].loc[9] -= 1
                  elif (index+5)%10 == 0 and n_pv_systems_to_distribute['final_amount'].loc[0] > 0:
                    self.net.sgen.type.loc[index] = 'pv_90'
                    n_pv_systems_to_distribute['final_amount'].loc[0] -= 1
                  else:
                    for k in range(0,18):
                      i = (k + j)%18
                      if i != 0 and i !=9:
                        if n_pv_systems_to_distribute['final_amount'].loc[i] > 0:
                          self.net.sgen.type.loc[index] = 'pv_' + str(n_pv_systems_to_distribute['orientation'][i])
                          n_pv_systems_to_distribute['final_amount'].loc[i] -= 1
                          j = i + 1
                          break
                        elif k == 17:
                          for l in [0, 9]:
                            if n_pv_systems_to_distribute['final_amount'].loc[l] > 0:
                              self.net.sgen.type.loc[index] = 'pv_' + str(n_pv_systems_to_distribute['orientation'][l])
                              n_pv_systems_to_distribute['final_amount'].loc[l] -= 1
                              break
                else:
                  print('Error: No pv-system orientation to distrubute. Number of pv-systems by orientation does not match with number of sgen in the grid')
            if n_pv_systems_to_distribute['final_amount'].sum() != 0 or n_pv_systems_to_distribute['final_amount'].max() != 0:
              print('Assignment of PV-systems (orientation) to sgen failed.')

        # hp: create series with all building and heatpump types
        for hp_type in self.hp_para['heatpump_type']:        
          if self.category == 'rural' or self.category == 'village' or self.category == 'suburban':
            for b_type in self.hp_para['building_type'][0:2]:
              self.hp_para['hp_types'] += [b_type + '_' + hp_type]
          elif self.category == 'urban':
            for b_type in self.hp_para['building_type'][2:4]:
              self.hp_para['hp_types'] += [b_type + '_' + hp_type]

        # create hp-loads und ev-loads at each bus 
        for index in self.net.load.index:
          self.net.load.name.loc[index] = 'load_'+str(self.net.load.loc[index, "bus"])
          self.net.load.type.loc[index] = 'load'
          if self.set_hp == True:
            # calculate distribution of heatpump types and building types within the grid
            pp.create_load(self.net, self.net.load.loc[index, "bus"], 0.0, name='hp_'+str(self.net.load.loc[index, "bus"]), type='hp_'+self.hp_para['hp_types'][index%4])

          if self.set_ev == True:
            pp.create_load(self.net, self.net.load.loc[index, "bus"], 0.0, name='ev_'+str(self.net.load.loc[index, "bus"]), type='ev')

        # Run diagnostic if there are problems regarding powerflow
        #pp.diagnostic(self.net, report_style='detailed', warnings_only=False)

    #########################################
    ### load timeseries and run powerflow ###
    #########################################
    def run_pf_timeseries(self):
        print('Load profiles ...')
        self.load_profiles()
        print('Run powerflow ...')
        self.run_pf()
        self.run_time('end')
            
    ##########################################
    ### load genearation and load profiles ###
    ##########################################
    def load_profiles(self):
        load_p_data_file = 'input-files/11_p0_test.pbz2'
        load_q_data_file = 'input-files/11_q0_test.pbz2'
        pv_data_file = 'input-files/12_pv_test.pbz2'
        hp_data_file = 'input-files/13_hp_test.pbz2'
        ev_data_file = 'input-files/14_ev_test.pbz2'

        ### load pv profiles ###
        pv = self.decompress_pickle(pv_data_file)
        # Define timeseries
        time = pv.index
        # define dataframe for all data
        self.df = pd.DataFrame(range(0,len(time)), index=time)
        # Check if pv-orientation is south or east-west
        if self.set_pv == True:
          # Define maximum installed pv-power per roof-top side (in kW)
          pv_power_installed = self.pv_para['power_'+str(self.category)]
          cos_phi = self.pv_para['cos_phi']
          for i in range(0,len(self.pv_para['orientation'])):
              # calculate installed power per household and normalize timeseries to MW
              pv_dc_power = pv[str(self.pv_para['orientation'][i])]*pv_power_installed*self.pv_para['installed_power_scaling'][i]/1000
              # calculate active and reactive power of pv-system
              self.df['pv_'+str(self.pv_para['orientation'][i])+'_p'] = pv_dc_power*cos_phi
              self.df['pv_'+str(self.pv_para['orientation'][i])+'_q'] = -(pv_dc_power**2 - (pv_dc_power*cos_phi)**2)**(1/2)

        ### load heatpump profile ###
        if self.set_hp == True:
          hp = self.decompress_pickle(hp_data_file)
          for hp_type in self.hp_para['hp_types']:
            self.df['hp_'+hp_type+'_p'] = hp['Demand_el_'+hp_type]/1000 # normalized to MW
            self.df['hp_'+hp_type+'_q'] = hp['Demand_el_'+hp_type]*self.hp_para['sin_phi']/1000 # normalized to MW
        else:
          self.df['hp'] = 0

        ### load load profiles ###
        p0 = self.decompress_pickle(load_p_data_file)
        q0 = self.decompress_pickle(load_q_data_file)
        for i in range(0,74):
            self.df['load_p_'+str(i)] = p0["p"+str(i)]/1000	# normalized to MW
            self.df['load_q_'+str(i)] = q0["q"+str(i)]/1000	# normalized to MW

        ### load ev profile ###
        if self.set_ev == True:
            ev = self.decompress_pickle(ev_data_file)
            for i in ev.columns:
              self.df[i] = ev[i]/1000 # normalized to MW
              self.ev_para['ev_types'] += [i]
        else:
            self.df['ev'] = 0
        ev_len = len(self.ev_para['ev_types'])
        for i in self.net.load.index[self.net.load.type == 'ev']:
            self.net.load.type[i] = self.ev_para['ev_types'][i%ev_len]

        self.df['timestamp'] = time


    ###################################
    ### run df for whole timeseries ###
    ###################################
    def run_pf(self):
      time_series = self.df['timestamp']
      timesteps = len(time_series)                
      rest_time = ''
      vm_pu = pd.DataFrame(columns=self.net.bus.index, index=time_series)
      li_lo = pd.DataFrame(columns=self.net.line.index, index=time_series)
      tr_lo = pd.DataFrame(columns=self.net.trafo.index, index=time_series)
      power = pd.DataFrame(columns=['load', 'pv', 'hp', 'ev'], index=time_series)
      
      pv_index = self.net.sgen.index
      index_helper_pv = self.net.sgen.type.loc[pv_index]
      index_helper_pv_p = index_helper_pv + '_p'
      index_helper_pv_q = index_helper_pv + '_q'

      load_index = self.net.load.index[self.net.load.type == 'load']
      index_helper_load_p = ['load_p_'+str(i) for i in load_index%74]
      index_helper_load_q = ['load_q_'+str(i) for i in load_index%74]

      hp_index = self.net.load.index[self.net.load.type.str.contains('hp')]
      index_helper_hp_p = [self.net.load.type[i] + '_p' for i in hp_index]
      index_helper_hp_q = [self.net.load.type[i] + '_q' for i in hp_index]

      ev_index = self.net.load.index[self.net.load.type.str.contains('ev')]
      index_helper_ev = [self.net.load.type[i] for i in ev_index]

      for i in range(0,timesteps):
        start = time.time()
        # show bar of process in terminal
        prog.progress(i, timesteps, status=' %s s ' % rest_time)
        t = time_series[i]
        d = self.df.loc[t]

        self.net.sgen.loc[pv_index, 'p_mw'] = d[index_helper_pv_p].values
        self.net.sgen.loc[pv_index, 'q_mvar'] = d[index_helper_pv_q].values

        self.net.load.loc[load_index, 'p_mw'] = d[index_helper_load_p].values
        self.net.load.loc[load_index, 'q_mvar'] = d[index_helper_load_q].values

        self.net.load.loc[hp_index, 'p_mw'] = d[index_helper_hp_p].values
        self.net.load.loc[hp_index, 'q_mvar'] = d[index_helper_hp_q].values

        self.net.load.loc[ev_index, 'p_mw'] = d[index_helper_ev].values
        #self.net.load.loc[ev_index, 'q_mvar'] = 0
        '''
        pp.runpp(self.net, algorithm='nr', init='results', max_iteration=10)

        # write result into DataFrame
        vm_pu.loc[time_series[i]] = self.net.res_bus.vm_pu
        li_lo.loc[time_series[i]] = self.net.res_line.loading_percent
        tr_lo.loc[time_series[i]] = self.net.res_trafo.loading_percent
        '''
        power.pv.loc[t] = self.net.sgen.p_mw.sum()
        power.load.loc[t] = self.net.load.p_mw[load_index].sum()
        power.hp.loc[t] = self.net.load.p_mw[hp_index].sum()
        power.ev.loc[t] = self.net.load.p_mw[ev_index].sum()

        end = time.time()
        rest_time = round((end - start)*(timesteps - i), 0)
      prog.progress(1, 1, status=' Done')
      print('')

      vm_pu.to_csv(self.output_dir + 'res_bus_vm_pu.csv',mode='w', header=True, index = True)
      li_lo.to_csv(self.output_dir + 'res_line_load_percent.csv',mode='w', header=True, index = True)
      tr_lo.to_csv(self.output_dir + 'res_trafo_load_percent.csv',mode='w', header=True, index = True)
      power.to_csv(self.output_dir + 'power_total_MW.csv',mode='w', header=True, index = True)

    ##############################
    ### Adjustment of Datasets ###
    ##############################
    def adjust_input_dataset(self, start_time, end_time, t_freq):
      
      # Read csv / DEPRICATED
      def read_data(file):
        data = pd.read_csv(file, low_memory=False)
        data['timestamp'] = pd.to_datetime(data['timestamp'], utc=True)
        data = data.set_index('timestamp')
        data.index = data.index.tz_convert('Europe/Berlin')

        return data

      def shorted_data(data, start_time, end_time, t_freq):
        data_shorted = data.loc[start_time:end_time]
        data_shorted = data_shorted.resample(t_freq).mean()
        data_shorted = data_shorted.round(4)

        return data_shorted

      dates = start_time + ' ' + end_time + ' ' + t_freq

      with open('input-files/daterange.csv') as daterange:
         csv_daterange = csv.reader(daterange)
         #print(csv_daterange)
         for row in csv_daterange:
            dates_old = str(row[0])

      dates_old = dates_old.strip('[')
      dates_old = dates_old.strip(']')
      dates_old = dates_old.strip('\'')

      print('Daterange: %s' % dates)

      if dates != dates_old:
        
        print('Adjust input datasets ...')

        start_time = pd.to_datetime(start_time, format='%Y-%m-%d %H:%M:%S')
        end_time = pd.to_datetime(end_time, format='%Y-%m-%d %H:%M:%S')

        p0 = self.decompress_pickle('input-files/01_p0_load.pbz2')
        q0 = self.decompress_pickle('input-files/01_q0_load.pbz2')
        pv = self.decompress_pickle('input-files/02_pv_gen.pbz2')
        hp = self.decompress_pickle('input-files/03_hp_load.pbz2')
        ev = self.decompress_pickle('input-files/04_ev_load.pbz2')

        p0_shorted = shorted_data(p0, start_time, end_time, t_freq)
        q0_shorted = shorted_data(q0, start_time, end_time, t_freq)
        pv_shorted = shorted_data(pv, start_time, end_time, t_freq)
        hp_shorted = shorted_data(hp, start_time, end_time, t_freq)
        ev_shorted = shorted_data(ev, start_time, end_time, t_freq)

        self.compress_pickle('input-files/11_p0_test.pbz2', p0_shorted)
        self.compress_pickle('input-files/11_q0_test.pbz2', q0_shorted)
        self.compress_pickle('input-files/12_pv_test.pbz2', pv_shorted)
        self.compress_pickle('input-files/13_hp_test.pbz2', hp_shorted)
        self.compress_pickle('input-files/14_ev_test.pbz2', ev_shorted)

        f = open('input-files/daterange.csv','w')
        f.write(dates)
        f.close()

    #########################
    ### create output_dir ###
    #########################
    def create_output_dir(self):
        # Create output directory
        if os.path.isdir(self.output_dir):
          print("Output directory: " + str(self.output_dir))
        else:
          try:
            os.makedirs(self.output_dir)
          except OSError:
            print("Error: Creation of output directory %s failed" % self.output_dir)
          else:
            print ("Create outout directory %s" % self.output_dir)

    #####################################################################
    ### Pickle a file and then compress it into a file with extension ###
    #####################################################################
    def compress_pickle(self, title, data):
     with bz2.BZ2File(title, 'w') as f: 
      cPickle.dump(data, f)
     f.close()

    #######################################
    ### Load any compressed pickle file ###
    #######################################
    def decompress_pickle(self, file):
     f = bz2.BZ2File(file, 'rb')
     data = cPickle.load(f)
     f.close()
     return data

    def run_time(self, buttom):
     if buttom == 'start':
      self.start = time.time()
     elif buttom == 'end':
      self.end = time.time()
      print("Elapsed (after compilation) = %s seconds" % (str(round(self.end - self.start, 2))))
     else:
      print('Error: no start or end time defined. run_time()')













