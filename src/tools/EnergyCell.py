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
import tools.tools as tt
import logging

import bz2
import _pickle as cPickle

from tools.creator.HHLcreator import HHLcreator
from tools.creator.PVcreator import PVcreator
from tools.creator.HPcreator import HPcreator
from tools.creator.EVcreator import EVcreator

from tools.controller.PVcontroller import PVcontroller

from tools.network.Grid import Grid

from tools.powerflow.PowerFlow import PowerFlow

from tools.datahandler.OutputDataHandler import OutputDataHandler
from tools.datahandler.InputDataHandler import InputDataHandler

from tools.evaluation.EvaluationSingleCase import EvaluationSingleCase

class EnergyCell():
    
    def __init__(self, net_name, scenario, time_scope):
        self.run_time('start')

        self.net_name = net_name
        if scenario in [1, 2, 3, 4]:
          self.scenario = scenario
        else:
          raise ValueError('The entered ´scenario´ is not a valid option. '+
                           '´Scenario´ should be between 1 and 4.')

        if ('start_time' in time_scope) and ('end_time' in time_scope) and ('t_freq' in time_scope):
          self.time_scope = time_scope
        else:
          raise ValueError('time_scope is not properly defined. start_time, end_time and t_freq is needed.')

        self.grid = Grid(net_name)

        self.hhl_creator = HHLcreator()
        self.pv_creator = PVcreator(self.scenario)
        self.hp_creator = HPcreator(self.scenario)
        self.ev_creator = EVcreator(self.scenario)

        self.grid = self.hhl_creator.create_hh_load_at_each_bus(self.grid)
        self.grid = self.pv_creator.create_pv_sgen_at_each_bus(self.grid)
        self.grid = self.hp_creator.create_hp_load_at_each_bus(self.grid)
        self.grid = self.ev_creator.create_ev_load_at_each_bus(self.grid)

        self.grid.get_component_index()
        self.grid.get_label_of_each_component()

        self.input_data_handler = InputDataHandler()
        self.input_data_handler.adjust_input_dataset(time_scope)

        self.output_data_handler = OutputDataHandler()
        self.output_data_handler.create_output_dir(net_name, scenario, time_scope)
        self.output_dir = self.output_data_handler.output_dir
        self.output_data_handler.create_output_dataframes(self.grid)

        self.pf = PowerFlow(self.output_dir)

        self.print_object_parameter()
   

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
        # Define timeseries
        self.time_series = tt.decompress_pickle('input-files/10_time_short.pbz2')
        # define dataframe for all data
        self.df = pd.DataFrame(range(0,len(self.time_series)), index=self.time_series)
        self.df['timestamp'] = self.time_series

        # load all profiles and store them into df
        self.df = self.hhl_creator.load_hhl_profiles(self.df)
        self.df = self.pv_creator.load_pv_profiles(self.df, self.grid.category)
        self.df = self.hp_creator.load_hp_profiles(self.df)
        self.df = self.ev_creator.load_ev_profiles(self.df)


    ###################################
    ### run df for whole timeseries ###
    ###################################
    def run_pf(self):

      self.output_data_handler.write_dataframe_to_csv(mode='w', header=True, grid=self.grid)

      if not hasattr(self, 'pv_controller'):
        self.set_pvcontroller(control='qu', cos_phi=.9)

      self.pf.run_power_flow_through_timeseries(df=self.df,
                                                grid=self.grid,
                                                pv_controller=self.pv_controller,
                                                output_data_handler=self.output_data_handler)

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

    ################################
    ### initialize pv controller ###
    ################################
    def set_pvcontroller(self, control='qu', cos_phi=.9):
        self.pv_controller = PVcontroller(grid=self.grid, control=control, cos_phi=cos_phi)

    ####################################################
    ### initiate evaluation object for a single case ###
    ####################################################
    def initiate_evaluation(self):
        self.eva = EvaluationSingleCase(self.output_dir, self.net_name, self.scenario, self.time_scope)

