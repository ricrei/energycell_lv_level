#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Jul 15 10:51:49 2020

@author: ricardo
"""

import time
import sys
import pandas as pd
import tools.tools as tt
import pvlib ###
import datetime ###

#temp
import pandapower as pp
#temp

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

    def __init__(self, net_name, scenario, control_parameter, time_scope):
        self.run_time('start')

        self.net_name = net_name

        if ((scenario[0] in [6, 7, 8]) and (scenario[1] in [1, 2, 3, 4])) or \
          ((scenario[0] in [1, 2, 3, 4, 5, 6]) and (scenario[1] in [0, 5, 6])): ###Paul
          self.scenario = scenario
        else:
          raise ValueError('Scenario number and controll mode do not match: ' + str(scenario))
        
        if ('start_time' in time_scope) and ('end_time' in time_scope) and ('t_freq' in time_scope):
          self.time_scope = time_scope
          self.intervall_in_seconds = pd.to_timedelta(time_scope['t_freq']).total_seconds()
          self.time_scope['intervall_in_seconds'] = self.intervall_in_seconds
        else:
          raise ValueError('time_scope is not properly defined. \
                            start_time, end_time and t_freq is needed.')

        self.input_data_handler = InputDataHandler()
        self.input_data_handler.adjust_input_dataset(self.time_scope)

        self.grid = Grid(self.net_name, self.scenario, self.time_scope)

        self.hhl_creator = HHLcreator()
        self.pv_creator = PVcreator()
        self.hp_creator = HPcreator()
        self.ev_creator = EVcreator()
        self.bss_creator = BSScreator(self.net_name, self.grid)#net_name

        self.grid = self.hhl_creator.create_hh_load_at_each_bus(self.grid)
        self.grid = self.pv_creator.create_pv_sgen_at_each_bus(self.grid)
        self.grid = self.hp_creator.create_hp_load_at_each_bus(self.grid)
        self.grid = self.ev_creator.create_ev_load_at_each_bus(self.grid)
        if (self.scenario[1] in [0, 1, 2, 5, 6]): ###Paul
          self.grid = self.bss_creator.create_bss_at_each_bus(self.grid)
        elif (self.scenario[0] in [6, 8]) and (self.scenario[1] in [3]):
          self.grid = self.bss_creator.create_bss_at_lvbb(self.grid)
        elif (self.scenario[0] in [6, 8]) and (self.scenario[1] in [4]):
          self.grid = self.bss_creator.create_bss_at_selected_buses(self.grid) #####PRÜFEN!!!
        else:
          raise ValueError('Scenario number and controll mode do not match: ' + str(scenario))

        self.grid.get_component_index()
        self.grid.get_label_of_each_component()
        self.grid.get_load_sgen_index_per_feeder()

        self.pv_controller = PVcontroller(grid=self.grid, control=control_parameter['PV_mod'], cos_phi=control_parameter['PV_cos_phi'])
        if (self.scenario[0] in [1, 2, 3, 4, 5, 6]) and (self.scenario[1] in [0]):
          self.ev_controller = EVcontroller(grid=self.grid, control='direct')
          self.hp_controller = HPcontroller(grid=self.grid, control='direct')
          self.bss_controller = BSScontroller(grid=self.grid, control='direct')
        elif (self.scenario[0] in [1, 2, 3, 4, 5, 6]) and (self.scenario[1] in [5]): ###Paul
          self.ev_controller = EVcontroller(grid=self.grid, control='direct')
          self.hp_controller = HPcontroller(grid=self.grid, control='evu_lock')
          self.bss_controller = BSScontroller(grid=self.grid, control='direct')
        elif (self.scenario[0] in [1, 2, 3, 4, 5, 6]) and (self.scenario[1] in [6]): ###Paul
          self.ev_controller = EVcontroller(grid=self.grid, control='direct')
          self.hp_controller = HPcontroller(grid=self.grid, control='residual_load_driven')
          self.bss_controller = BSScontroller(grid=self.grid, control='direct') 
        elif (self.scenario[0] in [6, 7, 8]) and (self.scenario[1] in [1, 2, 3, 4]): ###Paul
          mode = [0, 'household-oriented_feed-in_damping', 'grid-oriented_feed-in_damping',\
                  'grid-oriented_feed-in_damping', 'grid-oriented_feed-in_damping', 'evu_lock', 'residual_load_driven']
          self.ev_controller = EVcontroller(grid=self.grid, control=mode[scenario[1]])
          self.hp_controller = HPcontroller(grid=self.grid, control=mode[scenario[1]])
          self.bss_controller = BSScontroller(grid=self.grid, control=mode[scenario[1]])
        else:
          raise ValueError('Scenario number and controll mode do not match: ' + str(scenario))

        self.curtail_controller = Curtailcontroller(grid = self.grid, set_curtailment = int(scenario[2]))

        self.output_data_handler = OutputDataHandler()
        self.output_dir = self.output_data_handler.create_output_dir(
                                         self.net_name,
                                         self.scenario,
                                         self.time_scope)

        self.pf = PowerFlow(self.output_dir)
        self.energy_manager = EnergyManagement(self.scenario)

        self.print_object_parameter()

        self.run_time('end', 'init ec')

        if self.scenario[0] == 5:
          use_data_of_scenario = [4, 0, 0]
          self.output_data_handler_worst_case = OutputDataHandler()
          self.output_dir_worst_case = self.output_data_handler_worst_case.create_output_dir(
                                         self.net_name,
                                         use_data_of_scenario,
                                         self.time_scope)
          self.grid_reinforce = GridReinforce(
                                         self.grid,
                                         self.output_dir_worst_case,
                                         self.output_dir,
                                         use_data_of_scenario)
          #self.grid = self.grid_reinforce.reinforce_transformer(self.grid)
          #self.grid = self.grid_reinforce.reinforce_lines(self.grid)
          self.grid_reinforce.final_grid_check()
          sys.exit(0)

        self.output_data_handler.create_output_dataframes(self.grid)

        # Save net to pickle
        #pp.to_pickle(self.grid.net, 'networks/'+self.net_name+'.p')

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

        #  run powerflow
        self.pf.run_power_flow_through_timeseries(df=self.df,
                                                  grid=self.grid,
                                                  pv_controller=self.pv_controller,
                                                  hp_controller=self.hp_controller,
                                                  ev_controller=self.ev_controller,
                                                  bss_controller=self.bss_controller,
                                                  curtail_controller=self.curtail_controller,
                                                  energy_manager=self.energy_manager,
                                                  output_data_handler=self.output_data_handler)

        self.run_time('end', 'run pf')

    ####################################################
    ### initiate evaluation object for a single case ###
    ####################################################
    def initiate_evaluation(self):
        self.eva = EvaluationSingleCase(self.grid, self.output_dir, self.net_name, self.scenario[0], self.time_scope)

    ####################################################
    ### initiate evaluation object for a single case ###
    ####################################################
    def initiate_BSS_sizing(self):
        self.bss_sizing = EvaBSSsizing(self.grid, self.output_dir, self.net_name, self.scenario[0], self.time_scope)

    ############################
    ### calculate time delta ###
    ############################
    def run_time(self, button, string=''):
        if button == 'start':
          self.start = time.time()
        elif button == 'end':
          self.end = time.time()
          print(tt.text1('Processing time ' + string + ': ') + '%s seconds' % (str(round(self.end - self.start, 1))))
        else:
          print('Error: no start or end time defined. run_time()')

    ##############################################
    ### print object parameter in command line ###
    ##############################################
    def print_object_parameter(self):
        print(tt.text1('Grid: ') + str(self.grid.net_name) + ', ' + str(self.grid.category) + tt.text1('   Scenario: ') + str(self.scenario))
        print(tt.text1('Daterange: ') + str(self.input_data_handler.dates))


