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
import tools.tools as tt

import bz2
import _pickle as cPickle

from tools.creator.HHLcreator import HHLcreator
from tools.creator.PVcreator import PVcreator
from tools.creator.HPcreator import HPcreator
from tools.creator.EVcreator import EVcreator

from tools.controller.PVcontroller import PVcontroller

from tools.network.Grid import Grid

from tools.data.OutputDataHandler import OutputDataHandler
from tools.data.InputDataHandler import InputDataHandler

class EnergyCell():
    
    def __init__(self, net_name, scenario, time_scope):
        self.run_time('start')
        self.scenario = scenario
        [self.set_hp, self.set_ev, self.set_pv] = self.get_scenario_parameter(scenario=self.scenario)

        self.grid = Grid(net_name)

        self.hhl_creator = HHLcreator()
        self.pv_creator = PVcreator(self.set_pv)
        self.hp_creator = HPcreator(self.set_hp)
        self.ev_creator = EVcreator(self.set_ev)

        self.grid = self.hhl_creator.create_hh_load_at_each_bus(self.grid)
        self.grid = self.pv_creator.create_pv_sgen_at_each_bus(self.grid)
        self.grid = self.hp_creator.create_hp_load_at_each_bus(self.grid)
        self.grid = self.ev_creator.create_ev_load_at_each_bus(self.grid)

        self.input_data_handler = InputDataHandler()
        self.input_data_handler.adjust_input_dataset(time_scope)

        self.output_data_handler = OutputDataHandler()
        self.output_data_handler.create_output_dir(net_name, scenario, time_scope)
        self.output_dir = self.output_data_handler.output_dir
   

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
        # Define timeseries
        time = tt.decompress_pickle('input-files/10_time_short.pbz2')
        # define dataframe for all data
        self.df = pd.DataFrame(range(0,len(time)), index=time)
        self.df['timestamp'] = time

        # load all profiles and store them into df
        self.df = self.hhl_creator.load_hhl_profiles(self.df)
        self.df = self.pv_creator.load_pv_profiles(self.df, self.grid.category)
        self.df = self.hp_creator.load_hp_profiles(self.df)
        self.df = self.ev_creator.load_ev_profiles(self.df)


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

      self.pv_controller = PVcontroller(self.grid)

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

            self.grid.net.sgen['p_mw'] = d[index_helper_pv_p].values
            if self.pv_controller.pv_para['control'] == 'qu':
              self.grid = self.pv_controller.control_q_u(self.grid)
            elif self.pv_controller.pv_para['control'] == 'cos_phi':
              self.grid = self.pv_controller.control_cos_phi(self.grid)

            self.grid.net.load.loc[load_index, 'p_mw'] = d[index_helper_load_p].values
            self.grid.net.load.loc[load_index, 'q_mvar'] = d[index_helper_load_q].values

            self.grid.net.load.loc[hp_index, 'p_mw'] = d[index_helper_hp_p].values
            self.grid.net.load.loc[hp_index, 'q_mvar'] = d[index_helper_hp_q].values

            self.grid.net.load.loc[ev_index, 'p_mw'] = d[index_helper_ev].values
        
            # run pandapower power flow
            pp.runpp(self.grid.net, max_iteration=30, tolerance_mva=1e-6)

            self.pv_controller.get_v_of_last_timestep(self.grid.net.res_bus.vm_pu)

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













