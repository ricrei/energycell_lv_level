#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Jul 15 10:51:49 2020

@author: ricardo
"""

import time
import pandas as pd
import tools.tools as tt


from tools.creator.HHLcreator import HHLcreator
from tools.creator.PVcreator import PVcreator
from tools.creator.HPcreator import HPcreator
from tools.creator.EVcreator import EVcreator
from tools.creator.BSScreator import BSScreator

from tools.controller.PVcontroller import PVcontroller
from tools.controller.HPcontroller import HPcontroller
from tools.controller.EVcontroller import EVcontroller
from tools.controller.BSScontroller import BSScontroller

from tools.network.Grid import Grid

from tools.powerflow.PowerFlow import PowerFlow

from tools.datahandler.OutputDataHandler import OutputDataHandler
from tools.datahandler.InputDataHandler import InputDataHandler

from tools.evaluation.EvaluationSingleCase import EvaluationSingleCase

class EnergyCell():

    def __init__(self, net_name, scenario, time_scope):
        self.run_time('start')

        self.net_name = net_name
        if scenario in [1, 2, 3, 4, 6]:
          self.scenario = scenario
        else:
          raise ValueError('The entered ´scenario´ is not a valid option. \
                           ´Scenario´ should be between 1 and 4.')

        if ('start_time' in time_scope) and ('end_time' in time_scope) and ('t_freq' in time_scope):
          self.time_scope = time_scope
        else:
          raise ValueError('time_scope is not properly defined. \
                            start_time, end_time and t_freq is needed.')

        self.grid = Grid(net_name, self.scenario)

        self.hhl_creator = HHLcreator()
        self.pv_creator = PVcreator()
        self.hp_creator = HPcreator()
        self.ev_creator = EVcreator()
        self.bss_creator = BSScreator()

        self.grid = self.hhl_creator.create_hh_load_at_each_bus(self.grid)
        self.grid = self.pv_creator.create_pv_sgen_at_each_bus(self.grid)
        self.grid = self.hp_creator.create_hp_load_at_each_bus(self.grid)
        self.grid = self.ev_creator.create_ev_load_at_each_bus(self.grid)
        self.grid = self.bss_creator.create_bss_at_each_bus(self.grid)

        self.grid.get_component_index()
        self.grid.get_label_of_each_component()

        self.set_pvcontroller(control='qu', cos_phi=.9)
        self.set_hpcontroller(control='greedy')
        self.set_evcontroller(control='greedy')

        self.input_data_handler = InputDataHandler()
        self.input_data_handler.adjust_input_dataset(time_scope)

        self.output_data_handler = OutputDataHandler()
        self.output_dir = self.output_data_handler.create_output_dir(net_name, scenario, time_scope)
        self.output_data_handler.create_output_dataframes(self.grid)

        self.pf = PowerFlow(self.output_dir)

        self.print_object_parameter()

    def __repr__(self):
      return f'EnergyCell(net_name={self.net_name}, scenario={self.scenario}, time_scope={self.time_scope}'

    #########################################
    ### load timeseries and run powerflow ###
    #########################################
    def run_pf_timeseries(self):
        self.load_profiles()
        self.run_pf()
        self.run_time('end')
            
    ##########################################
    ### load genearation and load profiles ###
    ##########################################
    def load_profiles(self):

        # create df
        self.df = self.input_data_handler.create_empty_df(self.time_scope)

        # load all profiles and store them into df
        self.df = self.hhl_creator.load_hhl_profiles(self.df)
        self.df = self.pv_creator.load_pv_profiles(self.df, self.grid.category)
        self.df = self.hp_creator.load_hp_profiles(self.df)
        self.df = self.ev_creator.load_ev_profiles(self.df)

        self.input_dict = self.create_input_df(self.df, self.grid)


    ###################################
    ### run df for whole timeseries ###
    ###################################
    def run_pf(self):

      if not hasattr(self, 'pv_controller'):
        self.set_pvcontroller(control='qu', cos_phi=.9)

      if not hasattr(self, 'ev_controller'):
        self.set_evcontroller(control='greedy')

      if not hasattr(self, 'hp_controller'):
        self.set_hpcontroller(control='greedy')

      if not hasattr(self, 'bss_controller'):
        self.set_bsscontroller()

      self.pf.run_power_flow_through_timeseries(df=self.df,
                                                grid=self.grid,
                                                pv_controller=self.pv_controller,
                                                hp_controller=self.hp_controller,
                                                ev_controller=self.ev_controller,
                                                bss_controller=self.bss_controller,
                                                output_data_handler=self.output_data_handler)



    ############################
    ### calculate time delta ###
    ############################
    def create_input_df(self, df, grid):
        input_dict = {}
        input_dict['load_p'] = df[grid.label_load_p]
        input_dict['load_q'] = df[grid.label_load_q]
        input_dict['pv'] = df[grid.label_pv_p]
        input_dict['hp'] = df[grid.label_hp_p]
        input_dict['ev'] = df[grid.label_ev]

    ############################
    ### calculate time delta ###
    ############################
    def run_time(self, button):
        if button == 'start':
          self.start = time.time()
        elif button == 'end':
          self.end = time.time()
          print(tt.text1('Processing time : ') + '%s seconds' % (str(round(self.end - self.start, 1))))
        else:
          print('Error: no start or end time defined. run_time()')

    ##############################################
    ### print object parameter in command line ###
    ##############################################
    def print_object_parameter(self):
        print(tt.text1('Grid: ') + str(self.grid.net_name) + ', ' + str(self.grid.category) + tt.text1('   Scenario: ') + str(self.scenario))
        print(tt.text1('Daterange: ') + str(self.input_data_handler.dates))

    #############################
    ### initialize controller ###
    #############################
    def set_pvcontroller(self, control='qu', cos_phi=.9):
        self.pv_controller = PVcontroller(grid=self.grid, control=control, cos_phi=cos_phi)

    def set_evcontroller(self, control='greedy'):
        self.ev_controller = EVcontroller(grid=self.grid, control=control)

    def set_hpcontroller(self, control='greedy'):
        self.hp_controller = HPcontroller(grid=self.grid, control=control)

    def set_bsscontroller(self, control='simple'):
        self.bss_controller = BSScontroller(grid=self.grid, control=control)

    ####################################################
    ### initiate evaluation object for a single case ###
    ####################################################
    def initiate_evaluation(self):
        self.eva = EvaluationSingleCase(self.output_dir, self.net_name, self.scenario, self.time_scope)

