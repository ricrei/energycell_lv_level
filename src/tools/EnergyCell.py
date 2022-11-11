#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mo March 07 11:08:14 2022

@author: ricardo
"""

import time
import sys
import pandas as pd
import tools.tools as tt
import pvlib
import datetime
import numpy as np

import pandapower as pp

from tools.creator.HHLcreator import HHLcreator
from tools.creator.PVcreator import PVcreator
from tools.creator.HPcreator import HPcreator
from tools.creator.EVcreator import EVcreator
from tools.creator.BSScreator import BSScreator

from tools.controller.PVcontroller import PVcontroller
from tools.controller.HPcontroller import HPcontroller
from tools.controller.EVcontroller import EVcontroller
from tools.controller.BSScontroller import BSScontroller
from tools.controller.Curtailcontroller import Curtailcontroller

from tools.network.Grid import Grid
from tools.network.GridReinforce import GridReinforce

from tools.powerflow.PowerFlow import PowerFlow
from tools.powerflow.EnergyManagement import EnergyManagement

from tools.datahandler.OutputDataHandler import OutputDataHandler
from tools.datahandler.InputDataHandler import InputDataHandler

from tools.evaluation.EvaluationSingleCase import EvaluationSingleCase
from tools.evaluation.EvaBSSsizing import EvaBSSsizing

class EnergyCell():

    def __init__(self, net_name, scenario, control_parameter, time_scope, save_full_data = False, verbose = False, grid_reinforce_dev_mode = False):
        self.run_time('start')

        self.save_full_data = save_full_data

        self.controls = self.scenario_interpreter(scenario)
        self.net_name = net_name
        self.control_parameter = control_parameter

        self.time_scope = time_scope
        self.intervall_in_seconds = pd.to_timedelta(time_scope['t_freq']).total_seconds()
        self.time_scope['intervall_in_seconds'] = self.intervall_in_seconds

        self.input_data_handler = InputDataHandler(self.time_scope, self.scenario)
        self.input_data_handler.adjust_input_dataset(self.time_scope)

        self.grid = Grid(self.net_name, self.scenario, self.time_scope)

        self.hhl_creator = HHLcreator(self.input_data_handler.inputfolder)
        self.pv_creator = PVcreator(self.input_data_handler.inputfolder)
        self.hp_creator = HPcreator(self.input_data_handler.inputfolder, self.control_parameter)
        self.ev_creator = EVcreator(self.input_data_handler.inputfolder, self.control_parameter)
        self.bss_creator = BSScreator(self.grid, self.control_parameter)

        self.grid = self.hhl_creator.create_hh_load_at_each_bus(self.grid)
        self.grid = self.pv_creator.create_pv_sgen_at_each_bus(self.grid)
        self.grid = self.hp_creator.create_hp_load_at_each_bus(self.grid)
        self.grid = self.ev_creator.create_ev_load_at_each_bus(self.grid)
        self.grid = self.bss_creator.create_bss(self.grid, self.controls['bss'])

        self.grid.get_component_index()
        self.grid.get_label_of_each_component()
        self.grid.get_load_sgen_index_per_feeder()

        self.pv_controller = PVcontroller(grid=self.grid, control=self.controls['pv'], cos_phi=self.control_parameter['PV_cos_phi'])
        self.ev_controller = EVcontroller(grid=self.grid, control=self.controls['ev'], inputfolder=self.input_data_handler.inputfolder, control_parameter=self.control_parameter)
        self.hp_controller = HPcontroller(grid=self.grid, control=self.controls['hp'], control_parameter=self.control_parameter)
        self.bss_controller = BSScontroller(grid=self.grid, control=self.controls['bss'], control_parameter=self.control_parameter)

        self.curtail_controller = Curtailcontroller(grid = self.grid, set_curtailment = self.controls['curtailment'])

        self.output_data_handler = OutputDataHandler(save_full_data, self.control_parameter, self.grid)
        self.output_dir = self.output_data_handler.create_output_dir(
                                         self.net_name,
                                         self.scenario,
                                         self.time_scope)

        self.pf = PowerFlow(self.output_dir)
        self.energy_manager = EnergyManagement(self.scenario)

        self.grid_reinforce_dev_mode = grid_reinforce_dev_mode
        self.grid_reinforcement(exit=False)

        self.output_data_handler.create_output_dataframes(self.grid)

        # Save net to pickle
        #pp.to_pickle(self.grid.net, 'networks/'+self.net_name+'.p')

        self.display = tt.Progress(verbose)
        self.print_object_parameter('Start: ')

        self.run_time('end', 'init ec')

    def __repr__(self):
      return f'EnergyCell(net_name={self.net_name}, scenario={self.scenario}, time_scope={self.time_scope}'

    #######################
    ### load timeseries ###
    #######################
    def load_timeseries(self):
        # create df
        self.df = self.input_data_handler.create_empty_df(self.time_scope)

        # load all profiles and store them into df
        self.df = self.hhl_creator.load_hhl_profiles(self.df)
        self.df = self.pv_creator.load_pv_profiles(self.df, self.grid.category)
        self.df = self.hp_creator.load_hp_profiles(self.df)
        self.df = self.ev_creator.load_ev_profiles(self.df)

    #########################################
    ### load timeseries and run powerflow ###
    #########################################
    def run_pf_timeseries(self):

        self.run_time('start')
        
        self.load_timeseries()

        # run powerflow
        self.pf.run_power_flow_through_timeseries(df=self.df,
                                                  grid=self.grid,
                                                  pv_controller=self.pv_controller,
                                                  hp_controller=self.hp_controller,
                                                  ev_controller=self.ev_controller,
                                                  bss_controller=self.bss_controller,
                                                  curtail_controller=self.curtail_controller,
                                                  energy_manager=self.energy_manager,
                                                  output_data_handler=self.output_data_handler,
                                                  display=self.display)
        
        self.print_object_parameter('End  : ')
        self.run_time('end', 'run pf')

    ##################################
    ### conduct grid reinforcement ###
    ##################################
    def grid_reinforcement(self, exit=True):
        if self.scenario[6] == 1:
          use_data_of_scenario = np.copy(np.array(self.scenario))
          use_data_of_scenario[6] = 0
          if use_data_of_scenario[0] != 4: use_data_of_scenario = [4,1,0,1,1,0,0]
          self.output_data_handler_worst_case = OutputDataHandler(save_full_data = False)
          self.output_dir_worst_case = self.output_data_handler_worst_case.create_output_dir(
                                       self.net_name,
                                       use_data_of_scenario,
                                       self.time_scope)
          self.grid_reinforce = GridReinforce(
                                       self.grid,
                                       self.output_dir_worst_case,
                                       self.output_dir,
                                       use_data_of_scenario,
                                       self.control_parameter,
                                       self.grid_reinforce_dev_mode)
          self.grid = self.grid_reinforce.reinforce_transformer(self.grid)
          self.grid = self.grid_reinforce.reinforce_lines(self.grid)
          if self.grid_reinforce_dev_mode == True:
            self.grid_reinforce.final_grid_check()
            sys.exit(0)
          if exit == True: sys.exit(0)

    ####################################################
    ### initiate evaluation object for a single case ###
    ####################################################
    def initiate_evaluation(self):
        self.eva = EvaluationSingleCase(self.grid, self.output_dir, self.net_name, self.scenario[0], self.time_scope, self.save_full_data)

    ####################################################
    ### initiate evaluation object for a single case ###
    ####################################################
    def initiate_BSS_sizing(self):
        self.bss_sizing = EvaBSSsizing(self.grid, self.output_dir, self.net_name, self.scenario[0], self.time_scope)

    #####################################################
    ### check scenario and convert into control_names ###
    #####################################################
    def scenario_interpreter(self, scenario):
      self.scenario = scenario
      pv = [None, 'qu', 'cos_phi']
      bss = [None, 'direct', 'household-oriented_feed-in_damping', 'grid-oriented_feed-in_damping_HH', 'grid-oriented_feed-in_damping_LVbus', 'grid-oriented_feed-in_damping_feeder']
      hp = [None, 'direct', 'household-oriented_feed-in_damping', 'grid-oriented_feed-in_damping', 'evu_lock', 'residual_load_driven']
      ev = [None, 'direct', 'household-oriented_feed-in_damping', 'grid-oriented_feed-in_damping']
      curtailment = [False, True]
      grid_reinforce = [False, True]
      try:
        controls = {'scenario' : scenario[0],
                    'pv' :    pv[scenario[1]],
                    'bss' :  bss[scenario[2]],
                    'hp' :    hp[scenario[3]],
                    'ev' :    ev[scenario[4]],
                    'curtailment' :       curtailment[scenario[5]],
                    'grid_reinforce' : grid_reinforce[scenario[6]]
                   }
      except:
        raise ValueError('Scenario number not defined: ' + str(scenario))

      # PhD-scenarios
      phd_scenarios = [
        [1,0,0,0,0,0,0],
        [2,0,0,1,1,0,0], [2,0,0,1,1,1,0],
        [3,1,0,0,0,0,0], [3,1,0,0,0,1,0],
        [4,1,0,1,1,0,0], [4,1,0,1,1,1,0], [4,1,0,1,1,0,1],
        [6,1,1,1,1,0,0], [6,1,1,1,1,1,0], [6,1,1,1,1,0,1],
        [6,1,2,1,1,0,0], [6,1,2,1,1,1,0], [6,1,2,1,1,0,1],
        [6,1,3,1,1,0,0], [6,1,3,1,1,1,0], [6,1,3,1,1,0,1],
        [6,1,4,1,1,0,0], [6,1,4,1,1,1,0], [6,1,4,1,1,0,1],
        [6,1,5,1,1,0,0], [6,1,5,1,1,1,0], [6,1,5,1,1,0,1],
        [7,1,0,2,2,0,0], [7,1,0,2,2,1,0], [7,1,0,2,2,0,1],
        [7,1,0,3,3,0,0], [7,1,0,3,3,1,0], [7,1,0,3,3,0,1],
        [8,1,3,3,3,0,0], [8,1,3,3,3,1,0], [8,1,3,3,3,0,1], [8,1,3,3,3,1,1], [8,1,5,3,3,1,0],
                      ]

      if self.scenario not in phd_scenarios:
        print('WARNING: Scenario '+str(self.scenario)+' is not part of phd_scenarios')

      return controls

    ############################
    ### calculate time delta ###
    ############################
    def run_time(self, button, string=''):
        if button == 'start':
          self.start = time.time()
        elif button == 'end':
          self.end = time.time()
          self.display.display_time_info(self.end, self.start, string)
        else:
          print('Error: no start or end time defined. run_time()')

    ##############################################
    ### print object parameter in command line ###
    ##############################################
    def print_object_parameter(self, string):
        self.display.display_info(self.grid.net_name, self.grid.category, self.scenario, self.input_data_handler.dates, string)


