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
import pandapower.toolbox as tb
import simbench as sb
import tools.progress as prog

import bz2
import _pickle as cPickle

from tools.creator.HHLcreator import HHLcreator
from tools.creator.PVcreator import PVcreator
from tools.creator.HPcreator import HPcreator
from tools.creator.EVcreator import EVcreator
from tools.network.Grid      import Grid

class EnergyCell():
    
    def __init__(self, net_name, scenario, time_scope):
        self.run_time('start')
        self.scenario = scenario
        [self.set_hp, self.set_ev, self.set_pv] = self.get_scenario_parameter(scenario=self.scenario)
        #print('Scenario: %s' % self.scenario)
        self.output_dir = os.path.join("./", "output-files/"+str(scenario)+"/"+str(net_name)+"/"+time_scope['start_time'][0:10]+"_"+time_scope['end_time'][0:10]+"_"+time_scope['t_freq']+"/")

        self.grid = Grid(net_name)

        self.hhl_creator = HHLcreator()
        self.grid = self.hhl_creator.create_hh_load_at_each_bus(self.grid)

        self.pv_creator = PVcreator(self.set_pv)
        self.grid = self.pv_creator.create_pv_sgen_at_each_bus(self.grid)

        self.hp_creator = HPcreator(self.set_hp)
        self.grid = self.hp_creator.create_hp_load_at_each_bus(self.grid)

        self.ev_creator = EVcreator(self.set_ev)
        self.grid = self.ev_creator.create_ev_load_at_each_bus(self.grid)

        self.adjust_input_dataset(time_scope)
        self.create_output_dir()
   

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

        # Define timeseries
        time = self.decompress_pickle(pv_data_file).index
        self.df['timestamp'] = time
        # define dataframe for all data
        self.df = pd.DataFrame(range(0,len(time)), index=time)

        # load all profiles and store them into df
        self.df = self.hhl_creator.load_hhl_profiles(self.df, load_p_data_file, load_q_data_file)
        self.df = self.pv_creator.load_pv_profiles(self.df, pv_data_file, self.grid.category)
        self.df = self.hp_creator.load_hp_profiles(self.df, hp_data_file)
        self.df = self.ev_creator.load_ev_profiles(self.df, ev_data_file)


    ###################################
    ### run df for whole timeseries ###
    ###################################
    def run_pf(self):

      def create_output_dataframes():
        vm_pu = pd.DataFrame(columns=self.grid.net.bus.index)
        li_lo = pd.DataFrame(columns=self.grid.net.line.index)
        tr_lo = pd.DataFrame(columns=self.grid.net.trafo.index)
        power = pd.DataFrame(columns=['load', 'pv', 'hp', 'ev'])
        reactive_power = pd.DataFrame(columns=self.grid.net.bus.index)
        active_power = pd.DataFrame(columns=self.grid.net.bus.index)
        vm_pu.index.name = 'timestamp'
        li_lo.index.name = 'timestamp'
        tr_lo.index.name = 'timestamp'
        power.index.name = 'timestamp'
        reactive_power.index.name  = 'timestamp'
        active_power.index.name = 'timestamp'

        return vm_pu, li_lo, tr_lo, power, reactive_power, active_power

      def write_df_to_csv(mode, header, vm_pu, li_lo, tr_lo, power, reactive_power, active_power):
        vm_pu.round(3).to_csv(self.output_dir + 'res_bus_vm_pu.csv',mode=mode, header=header, index = True)
        li_lo.round(1).to_csv(self.output_dir + 'res_line_load_percent.csv',mode=mode, header=header, index = True)
        tr_lo.round(1).to_csv(self.output_dir + 'res_trafo_load_percent.csv',mode=mode, header=header, index = True)
        power.round(6).to_csv(self.output_dir + 'power_total_MW.csv',mode=mode, header=header, index = True)
        reactive_power.round(6).to_csv(self.output_dir + 'reactive_power_MW.csv',mode=mode, header=header, index = True)
        active_power.round(6).to_csv(self.output_dir + 'active_power_MW.csv',mode=mode, header=header, index = True)

      def calculate_time_step_array(time_step_size):
        time_delta = int((timesteps - timesteps%time_step_size)/time_step_size)
        a = 0*np.arange(time_delta + 1) + 1
        a = int((timesteps - timesteps%time_delta)/time_delta)*a
        a[time_delta] = int(timesteps%time_delta)

        return a

      time_series = self.df['timestamp']
      timesteps = len(time_series)
      rest_time = ''
      time_step_size = 1

      vm_pu, li_lo, tr_lo, power, reactive_power, active_power = create_output_dataframes()

      pv_index = self.grid.net.sgen.index
      index_helper_pv = self.grid.net.sgen.type.loc[pv_index]
      index_helper_pv_p = index_helper_pv + '_p'
      index_helper_pv_q = index_helper_pv + '_q'

      load_index = self.grid.net.load.index[self.grid.net.load.type.str.contains('load')]
      index_helper_load_p = [self.grid.net.load.type[i] + '_p' for i in load_index]
      index_helper_load_q = [self.grid.net.load.type[i] + '_q' for i in load_index]


      hp_index = self.grid.net.load.index[self.grid.net.load.type.str.contains('hp')]
      index_helper_hp_p = [self.grid.net.load.type[i] + '_p' for i in hp_index]
      index_helper_hp_q = [self.grid.net.load.type[i] + '_q' for i in hp_index]

      ev_index = self.grid.net.load.index[self.grid.net.load.type.str.contains('ev')]
      index_helper_ev = [self.grid.net.load.type[i] for i in ev_index]

      a = calculate_time_step_array(time_step_size)
      l, k, j, i = 0, 0, 0, 0

      q_sgen_t_minus_1 = self.grid.net.sgen['q_mvar']
      q_sgen_t_minus_2 = self.grid.net.sgen['q_mvar']
      q_sgen_t_minus_3 = self.grid.net.sgen['q_mvar']
      q_sgen_t_minus_4 = self.grid.net.sgen['q_mvar']
      q_sgen_t_minus_5 = self.grid.net.sgen['q_mvar']
      p_sgen_t_minus_1 = self.grid.net.sgen['p_mw']
      v_t_minus_1 = self.grid.net.bus.index*0 + 1.0
      v_t_minus_2 = self.grid.net.bus.index*0 + 1.0
      v_t_minus_3 = self.grid.net.bus.index*0 + 1.0
      v_t_minus_4 = self.grid.net.bus.index*0 + 1.0
      v_t_minus_5 = self.grid.net.bus.index*0 + 1.0

      ### main loop: try to avoid 'if', 'for', ... statments ###
      ###           Processing time is valuable!             ###
      for k in a:
          for j in range(k):
            i = j + l
            start = time.time()
            # show bar of process in terminal
            prog.progress(i, timesteps, status=' %s s ' % rest_time)

            t = time_series[i]
            d = self.df.loc[t]

            self.grid.net.sgen.loc[pv_index, 'p_mw'] = d[index_helper_pv_p].values
            if self.pv_creator.pv_para['q_u_cont'] == True:
              v_t_minus_5 = v_t_minus_4
              v_t_minus_4 = v_t_minus_3
              v_t_minus_3 = v_t_minus_2
              v_t_minus_2 = v_t_minus_1
              self.q_u_control(v_t_minus_1, v_t_minus_2, v_t_minus_3, v_t_minus_4, v_t_minus_5, p_sgen_t_minus_1, q_sgen_t_minus_1, q_sgen_t_minus_2, q_sgen_t_minus_3, q_sgen_t_minus_4, q_sgen_t_minus_5)
              q_sgen_t_minus_5 = q_sgen_t_minus_4
              q_sgen_t_minus_4 = q_sgen_t_minus_3
              q_sgen_t_minus_3 = q_sgen_t_minus_2
              q_sgen_t_minus_2 = q_sgen_t_minus_1
              q_sgen_t_minus_1 = self.grid.net.sgen.loc[pv_index,'q_mvar']
              p_sgen_t_minus_1 = self.grid.net.sgen['p_mw']
            else:
              self.grid.net.sgen.loc[pv_index, 'q_mvar'] = d[index_helper_pv_q].values

            self.grid.net.load.loc[load_index, 'p_mw'] = d[index_helper_load_p].values
            self.grid.net.load.loc[load_index, 'q_mvar'] = d[index_helper_load_q].values

            self.grid.net.load.loc[hp_index, 'p_mw'] = d[index_helper_hp_p].values
            self.grid.net.load.loc[hp_index, 'q_mvar'] = d[index_helper_hp_q].values

            self.grid.net.load.loc[ev_index, 'p_mw'] = d[index_helper_ev].values
        
            # run pandapower power flow
            pp.runpp(self.grid.net, init='auto', init_vm_pu=v_t_minus_1, init_va_degree='results', max_iteration=30, tolerance_mva=1e-6)

            v_t_minus_1 = self.grid.net.res_bus.vm_pu

            # write result into DataFrame
            vm_pu.loc[t] = self.grid.net.res_bus.vm_pu
            li_lo.loc[t] = self.grid.net.res_line.loading_percent
            tr_lo.loc[t] = self.grid.net.res_trafo.loading_percent
            power.loc[t] = [self.grid.net.load.p_mw[load_index].sum(),
                            self.grid.net.sgen.p_mw.sum(),
                            self.grid.net.load.p_mw[hp_index].sum(),
                            self.grid.net.load.p_mw[ev_index].sum()]
            reactive_power.loc[t] = self.grid.net.sgen['q_mvar']
            active_power.loc[t] = self.grid.net.sgen['p_mw']

            end = time.time()
            rest_time = int(round((end - start)*(timesteps - i), 0))

          if l == 0:
            write_df_to_csv(mode='w', header=True, vm_pu=vm_pu, li_lo=li_lo, tr_lo=tr_lo, power=power, reactive_power=reactive_power, active_power=active_power)
            vm_pu, li_lo, tr_lo, power, reactive_power, active_power = create_output_dataframes()
          else:
            write_df_to_csv(mode='a', header=False, vm_pu=vm_pu, li_lo=li_lo, tr_lo=tr_lo, power=power, reactive_power=reactive_power, active_power=active_power)
            vm_pu, li_lo, tr_lo, power, reactive_power, active_power = create_output_dataframes()
          l += k

      prog.progress(1, 1, status=' Done ')
      print('')
      

    ####################
    ### Q(U) Control ###
    ####################
    def q_u_control(self, v_t_minus_1, v_t_minus_2, v_t_minus_3, v_t_minus_4, v_t_minus_5, p_sgen_t_minus_1, q_sgen_t_minus_1, q_sgen_t_minus_2, q_sgen_t_minus_3, q_sgen_t_minus_4, q_sgen_t_minus_5):
      a = .2
      q_sgen_t = (q_sgen_t_minus_1 + q_sgen_t_minus_2 + q_sgen_t_minus_3 + q_sgen_t_minus_4 + q_sgen_t_minus_5)/5
      v_t = (v_t_minus_1 + v_t_minus_2 + v_t_minus_3 + v_t_minus_4 + v_t_minus_5)/5
      v = v_t[self.grid.net.sgen['bus']].values
      P = self.grid.net.sgen["p_mw"]
      Q = P * self.pv_creator.pv_para['tan_phi']
      m = Q/(self.pv_creator.pv_para['U2'] - self.pv_creator.pv_para['U1'])

      self.grid.net.sgen.loc[v <= self.pv_creator.pv_para['U1'], 'q_mvar'] = Q
      self.grid.net.sgen.loc[(v <= self.pv_creator.pv_para['U2']) & (v >= self.pv_creator.pv_para['U1']), 'q_mvar'] = -m*(v-self.pv_creator.pv_para['U2'])
      self.grid.net.sgen.loc[(v <= self.pv_creator.pv_para['U3']) & (v >= self.pv_creator.pv_para['U2']), 'q_mvar'] = 0
      self.grid.net.sgen.loc[(v <= self.pv_creator.pv_para['U4']) & (v >= self.pv_creator.pv_para['U3']), 'q_mvar'] = -m*(v-self.pv_creator.pv_para['U3'])
      self.grid.net.sgen.loc[v >= self.pv_creator.pv_para['U4'], 'q_mvar'] = -Q

      self.grid.net.sgen['q_mvar'] = a*self.grid.net.sgen['q_mvar'] + q_sgen_t
      self.grid.net.sgen.loc[self.grid.net.sgen['q_mvar'] < -Q, 'q_mvar'] = -Q
      self.grid.net.sgen.loc[self.grid.net.sgen['q_mvar'] >  Q, 'q_mvar'] = Q

      #print(v_t[42])
      #print(q_sgen_t_minus_1[42])
      #print((self.grid.net.sgen['q_mvar'] - q_sgen_t_minus_1).sum())
      #print((self.grid.net.sgen['q_mvar'] - q_sgen_t_minus_1).max())
      #print(self.get_cos_phi(self.grid.net.sgen['p_mw'], self.grid.net.sgen['q_mvar']).min())

    #########################
    ### Calculate cos phi ###
    #########################      
    def get_cos_phi(self, P, Q):
       return P/(P**2 + Q**2)**(1/2)

    ##############################
    ### Adjustment of Datasets ###
    ##############################
    def adjust_input_dataset(self, time_scope):
      
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

      dates = time_scope['start_time'] + ' ' + time_scope['end_time'] + ' ' + time_scope['t_freq']

      with open('input-files/daterange.csv') as daterange:
         csv_daterange = csv.reader(daterange)
         for row in csv_daterange:
            dates_old = str(row[0])

      dates_old = dates_old.strip('[')
      dates_old = dates_old.strip(']')
      dates_old = dates_old.strip('\'')

      print('Daterange: %s' % dates)

      if dates != dates_old:
        
        print('Adjust input datasets ...')

        start_time = pd.to_datetime(time_scope['start_time'], format='%Y-%m-%d %H:%M:%S')
        end_time = pd.to_datetime(time_scope['end_time'], format='%Y-%m-%d %H:%M:%S')
        t_freq = time_scope['t_freq']

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

    ##############################
    ### get scenario parameter ###
    ##############################
    def get_scenario_parameter(self, scenario):
        print('Scenario: %s' % self.scenario)
        # hp, ev, pv
        scenario_dict = {
             1 : [0, 0, 0],
             2 : [1, 1, 0],
             3 : [0, 0, 1],
             4 : [1, 1, 1]
        }
        return scenario_dict[scenario][0], scenario_dict[scenario][1], scenario_dict[scenario][2]


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
            print("Create outout directory %s" % self.output_dir)

    #####################################################################
    ### Pickle a file and then compress it into a file with extension ###
    #####################################################################
    def compress_pickle(self, title, data):
     '''
     Method to pickle a file and then compress it into a file with extension.

     :param title: string
     :param data:  DataFrame
     '''
     with bz2.BZ2File(title, 'w') as f: 
      cPickle.dump(data, f)
     f.close()

    #######################################
    ### Load any compressed pickle file ###
    #######################################
    def decompress_pickle(self, file):
     '''
     Method to load a compressed pickle file.

     :param file: string
     :return: DataFrame
     '''
     f = bz2.BZ2File(file, 'rb')
     data = cPickle.load(f)
     f.close()
     return data

    ############################
    ### calculate time delta ###
    ############################
    def run_time(self, button):
     if button == 'start':
      self.start = time.time()
     elif button == 'end':
      self.end = time.time()
      print("Elapsed (after compilation) = %s seconds" % (str(round(self.end - self.start, 2))))
     else:
      print('Error: no start or end time defined. run_time()')













