import os
import csv
import time
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib as mpl
import pandapower.plotting.plotly as ppply
import seaborn as sns
from datetime import datetime, timedelta

import tools.evaluation.Evaluation as evaluation

# Handle date time conversions between pandas and matplotlib
from pandas.plotting import register_matplotlib_converters
register_matplotlib_converters()

import tools.tools as tt

import bz2
import _pickle as cPickle

### RUN in development mode ###
'''
run script to load data
  python -i main_EVA.py
import importlib once
  import importlib
to excecute method run this command everytime
  importlib.reload(evaluation), evaluation.plot_curtailed_power(eva, save_fig_dir=save_fig_dir)
'''

#############################
### Define all gird names ###
net_name = ["kerber_rural_1", #0
            "kerber_rural_2", #1
            "kerber_rural_3", #2
            "kerber_rural_4",  #3
            "kerber_village",  #4
            "kerber_suburb_1", #5
            "kerber_suburb_2",  #6
            "simbench_rural_1", #7
            "simbench_rural_2", #8
            "simbench_rural_3", #9
            "simbench_suburb_4", #10
            "simbench_suburb_5", #11
            "simbench_urban_6",  #12
            "test_net_one_load_branch"]  #13
############################

# Image output directory
save_fig_dir = 'img/'

output_df_dir = 'output-files/000_evaluation_dicts/'

def load_scenario_data(scenarios, grids=['n7','n8','n9','n10','n11'], seasons=['spring','summer','autumn','winter']):
  print('Load eva dicts ...')
  files = os.listdir(output_df_dir)

  eva = {}
  for index in files:
    if index[1:8] in scenarios:
      for n in grids:
        if n in index:
          for s in seasons:
            if s in index:
              print('Load: '+str(index))
              name = index[0:-5]
              eva[str(name)] = tt.decompress_pickle(output_df_dir + index)

  return eva

n = 4    # Number of timescopes
m = 4*4  # Number of timescopes * Number of scenarios



###############################
########## Timeplots ##########
###############################

# --- Power --- #
'''
scenarios = ['6131110', '8133310']
eva = load_scenario_data(scenarios, grids=['n8'], seasons=['summer'])
evaluation.plot_residualload_subplot_overall_eva(eva['s6131110n8summer'], eva['s8133310n8summer'], save_fig_dir=save_fig_dir+'n8_summer_plot_res_load_subplot.png')
'''

# --- Components loading --- #
'''
scenarios = ['6111110', '6121110', '6131110', '6141110']
eva = load_scenario_data(scenarios, grids=['n9'], seasons=['summer','winter'])
evaluation.plot_grid_issus_over_time_subplot(eva1=eva['s6111110n9winter'], eva2=eva['s6111110n9winter'], detailed=True, save_fig_dir=save_fig_dir+ 'n9_winter_plot_grid_issus_over_time_subplot_n9_winter.png')
evaluation.plot_grid_issus_over_time(eva['s6111110n9winter'], save_fig_dir=save_fig_dir+ 'n9_winter_plot_grid_issus_over_time_subplot_n9_winter_full.png')
'''
# --- SOCs --- #
'''
### To-Do: @Tabea: Wird das noch benötigt? Falls ja, anpassen. Falls nein, löschen auch in Evaluation.py
evaluation.state_of_charge(eva, net_name, n, save_fig_dir=save_fig_dir)
'''

##############################
########## Heatmaps ##########
##############################
# --- Generation / consumption --- #
'''
scenarios = ['6111110']
eva = load_scenario_data(scenarios, grids=['n9'], seasons=['summer','winter'])
evaluation.plot_generation_consumption_as_heat_map_overall_eva(eva['s6111110n9winter']['power'], save_fig_dir=save_fig_dir+'gen_con_heatmap_winter.png')
evaluation.plot_generation_consumption_as_heat_map_overall_eva(eva['s6111110n9summer']['power'], save_fig_dir=save_fig_dir+'gen_con_heatmap_summer.png')
'''
# --- Components loading: Trafo, Lines, Bus-Voltages --- #
'''
scenarios = ['1000000', '2001110', '3100010', '4101110', '6131110', '7103310', '8133310']
x_ticklabels      = scenarios#['Conv'   , 'EV+HP'  , 'PV'     , 'PV+EV+HP']
eva = load_scenario_data(scenarios)
evaluation.plot_heatmap_grid_issus(eva, net_name, scenarios, x_ticklabels, n, save_fig_dir=save_fig_dir)
'''

# --- Curtailment: PV-Power and Load (Scenario - Grid) --- #
#'''
scenarios = ['1000000', '2001110', '3100010', '4101110', '6111110', '6121110', '6131110', '6141110', '6151110', '7103310', '8133310']
eva = load_scenario_data(scenarios)
evaluation.plot_heatmap_curtailed_power(eva, net_name, columns_scenarios = ['1000000', '2001110', '3100010', '4101110'], x_ticklabels = ['1', '2', '3', '4'], save_fig_dir=save_fig_dir+'0')
evaluation.plot_heatmap_curtailed_power(eva, net_name, columns_scenarios = ['4101110', '6111110', '6121110', '6131110', '6141110', '6151110'], x_ticklabels = ['4', '5a', '5b', '5c HH', '5c CBSS-LV', '5c CBSS feeder'], save_fig_dir=save_fig_dir+'1')
evaluation.plot_heatmap_curtailed_power(eva, net_name, columns_scenarios = ['4101110', '6131110', '7103310', '8133310'], x_ticklabels = ['4', '5c HH', '6', '7'], save_fig_dir=save_fig_dir+'2')

# --- Self-Sufficiancy and PV Consumption --- #

#scenarios = ['1000000', '2001110', '3100010', '4101110', '6111110', '6121110', '6131110', '6141110', '6151110', '7103310', '8133310']
#eva = load_scenario_data(scenarios)
evaluation.plot_heatmap_self_sufficiency(eva, net_name, columns_scenarios=['1000000', '2001110', '3100010', '4101110'], x_ticklabels = ['1', '2', '3', '4'], n=n, save_fig_dir=save_fig_dir+'0')
evaluation.plot_heatmap_self_sufficiency(eva, net_name, columns_scenarios=['4101110', '6111110', '6121110', '6131110', '6141110', '6151110'], x_ticklabels = ['4', '5a', '5b', '5c HH', '5c CBSS-LV', '5c CBSS feeder'], n=n, save_fig_dir=save_fig_dir+'1')
evaluation.plot_heatmap_self_sufficiency(eva, net_name, columns_scenarios=['4101110', '6131110', '7103310', '8133310'], x_ticklabels = ['4', '5c HH', '6', '7'], n=n, save_fig_dir=save_fig_dir+'2')
#'''

# --- Curtailment: PV-Power and Load (Season - Grid) --- #

#scenarios = ['8133310']
#eva = load_scenario_data(scenarios)
evaluation.plot_heatmap_curtailed_power_per_season(eva, scenarios, net_name, save_fig_dir=save_fig_dir)

# --- Curtailment: Self-Sufficiancy and PV Consumption (Season - Grid) --- #

#'''
scenario = ['8133310']
eva = load_scenario_data(scenario)
evaluation.plot_heatmap_self_sufficiency_per_season(eva, scenario, net_name, save_fig_dir=save_fig_dir)
#'''

################################
########## Bar charts ##########
################################
# --- PV Power (curtailed, feed-in, consumed) and Load (curtailed, grid obtained, direct consumed) --- #
#'''
scenario = '4101110'
seasons = ['spring','summer','autumn','winter']
eva = load_scenario_data(scenario, seasons=seasons)
evaluation.plot_curtailed_power(eva, scenario=scenario, seasons = seasons, save_fig_dir=save_fig_dir)
#'''

#'''
scenarios = ['4101110', '6131110', '7103310', '8133310']
seasons = ['spring','summer','autumn','winter']
eva = load_scenario_data(scenarios, seasons=seasons)
evaluation.plot_bar_chart_percent(eva, scenarios=scenarios, seasons = seasons, save_fig_dir=save_fig_dir)
#'''

#################################
########## Other plots ##########
#################################
'''
scenarios = ['6111110', '6121110', '6131110', '6141110']
eva = load_scenario_data(scenarios)
evaluation.plot_barplots_overall_eva(eva, m, save_fig_dir=save_fig_dir)
evaluation.plot_hist_grid_issus_voltage(eva['s6111110n9summer'], eva['s6111110n9winter'], save_fig_dir+ 'hist_grid_issus_voltage.png')
'''
