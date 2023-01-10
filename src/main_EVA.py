import os
import csv
import sys
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

#############################
### Define all gird names ###
sfh_name = ["SFH15", 	#A
            "SFH45", 	#B
            "SFH100" ] 	#C
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


##################################
########## Print Output ##########
##################################
# --- Power --- #
'''
scenarios = ['4101110']
eva = load_scenario_data(scenarios)
for grid in ['n7','n8','n9','n10','n11']:
  evaluation.calculate_outputdata(eva, scenarios, grid, save_fig_dir=save_fig_dir+'calculated_data.png')
'''

#sys.exit(0)


###############################
########## Timeplots ##########
###############################

# --- Power --- #

# --- Power and Components loading --- #
#scenarios = [C008010, 'C106010', 'C107010', 'C108010']

scenarios = ['A006010', 'A306010', 'A106010', 'A007010', 'A307010', 'A107010', 'A008010', 'A308010', 'A108010', \
              'B006010', 'B306010', 'B106010', 'B007010', 'B307010', 'B107010', 'B008010', 'B308010', 'B108010', \
              'C006010', 'C306010', 'C106010', 'C007010', 'C307010', 'C107010', 'C008010', 'C308010', 'C108010']

#eva = load_scenario_data(scenarios, grids=['n8'], seasons=['winter'])
#evaluation.plot_residualload_grid_issues_subplot_overall_eva_3_plots(eva1=eva['sC106010n8winter'], eva2=eva['sC107010n8winter'], eva3=eva['sC108010n8winter'], save_fig_dir=save_fig_dir+ 'res_grid_sfh100_winter_all_tes_3plots.png')
#evaluation.plot_residualload_grid_issues_subplot_overall_eva_3_plots(eva1=eva['sA108010n8winter'], eva2=eva['sB108010n8winter'], eva3=eva['sC108010n8winter'], save_fig_dir=save_fig_dir+ 'res_grid_sfhs_winter_large_tes_large_pv.png')


#eva = load_scenario_data(scenarios, grids=['n8'], seasons=['summer', 'winter', 'spring', 'autumn'])
#evaluation.plot_residualload_grid_issues_subplot_overall_eva_3_plots(eva1=eva['sC108010n8winter'], eva2=eva['sC108010n8spring'], eva3=eva['sC108010n8summer'], save_fig_dir=save_fig_dir+ 'res_grid_sfh100_all_seas_large_tes_large_pv.png')
#evaluation.plot_residualload_grid_issues_subplot_overall_eva_3_plots(eva1=eva['sC106010n8spring'], eva2=eva['sC107010n8spring'], eva3=eva['sC108010n8spring'], save_fig_dir=save_fig_dir+ 'res_grid_sfh100_spring_all_tes_large_pv.png')
#evaluation.plot_residualload_grid_issues_subplot_overall_eva_3_plots(eva1=eva['sC008010n8winter'], eva2=eva['sC308010n8winter'], eva3=eva['sC108010n8winter'], save_fig_dir=save_fig_dir+ 'res_grid_sfh100_winter_large_tes_all_pv.png')
#evaluation.plot_residualload_grid_issues_subplot_overall_eva_3_plots(eva1=eva['sC106010n8winter'], eva2=eva['sC107010n8winter'], eva3=eva['sC108010n8winter'], save_fig_dir=save_fig_dir+ 'res_grid_sfh100_winter_all_tes_large_pv.png')
#evaluation.plot_residualload_grid_issues_subplot_overall_eva_3_plots(eva1=eva['sA108010n8winter'], eva2=eva['sB108010n8winter'], eva3=eva['sC108010n8winter'], save_fig_dir=save_fig_dir+ 'res_grid_sfhs_winter_large_tes_large_pv.png')

# --- Curtailment: Self-Sufficiancy and PV Consumption (Season - Grid) --- #
scenario = scenarios

#eva = load_scenario_data(scenario, seasons=['winter'])
#evaluation.plot_heatmap_self_sufficiency_tes_to_pv(eva, scenario, net_name, save_fig_dir=save_fig_dir + 'heatmap_mean_self_suff_winter_tes_to_pv.png')
#evaluation.plot_heatmap_curtailed_load_tes_to_pv(eva, scenario, net_name, save_fig_dir=save_fig_dir + 'heatmap_mean_curtailed_winter_tes_to_pv.png')
#evaluation.plot_heatmap_mean_trafo_load_tes_to_pv(eva, scenario, net_name, save_fig_dir= save_fig_dir + 'heatmap_mean_trafo_winter_tes_to_pv.png')

#eva = load_scenario_data(scenario, seasons=['summer'])
#evaluation.plot_heatmap_self_sufficiency_tes_to_pv(eva, scenario, net_name, save_fig_dir=save_fig_dir + 'heatmap_mean_self_suff_summer_tes_to_pv.png')
#evaluation.plot_heatmap_curtailed_load_tes_to_pv(eva, scenario, net_name, save_fig_dir=save_fig_dir + 'heatmap_mean_curtailed_summer_tes_to_pv.png')
#evaluation.plot_heatmap_mean_trafo_load_tes_to_pv(eva, scenario, net_name, save_fig_dir= save_fig_dir + 'heatmap_mean_trafo_summer_tes_to_pv.png')

#eva = load_scenario_data(scenario, seasons=['spring'])
#evaluation.plot_heatmap_self_sufficiency_tes_to_pv(eva, scenario, net_name, save_fig_dir=save_fig_dir + 'heatmap_mean_self_suff_spring_tes_to_pv.png')
#evaluation.plot_heatmap_curtailed_load_tes_to_pv(eva, scenario, net_name, save_fig_dir=save_fig_dir + 'heatmap_mean_curtailed_load_spring_tes_to_pv.png')
#evaluation.plot_heatmap_mean_trafo_load_tes_to_pv(eva, scenario, net_name, save_fig_dir= save_fig_dir + 'heatmap_mean_trafo_load_spring_tes_to_pv.png')

#eva = load_scenario_data(scenario, seasons=['spring', 'autumn'])
#evaluation.plot_heatmap_self_sufficiency_tes_to_pv(eva, scenario, net_name, save_fig_dir=save_fig_dir + 'heatmap_mean_self_suff_spring_autumn_tes_to_pv.png')
#evaluation.plot_heatmap_curtailed_load_tes_to_pv(eva, scenario, net_name, save_fig_dir=save_fig_dir + 'heatmap_mean_curtailed_load_spring_autumn_tes_to_pv.png')
#evaluation.plot_heatmap_mean_trafo_load_tes_to_pv(eva, scenario, net_name, save_fig_dir= save_fig_dir + 'heatmap_mean_trafo_load_spring_autumn_tes_to_pv.png')

eva = load_scenario_data(scenario, seasons=['spring', 'autumn', 'summer', 'winter'])
evaluation.plot_heatmap_self_sufficiency_tes_to_pv(eva, scenario, net_name, save_fig_dir=save_fig_dir + 'heatmap_mean_self_suff_all_seasons_tes_to_pv.png')
#evaluation.plot_heatmap_curtailed_load_tes_to_pv(eva, scenario, net_name, save_fig_dir=save_fig_dir + 'heatmap_mean_curtailed_load_all_seasons_tes_to_pv.png')
#evaluation.plot_heatmap_curtailed_pv_tes_to_pv(eva, scenario, net_name, save_fig_dir=save_fig_dir + 'heatmap_mean_curtailed_pv_all_seasons_tes_to_pv.png')
#evaluation.plot_heatmap_mean_trafo_load_tes_to_pv(eva, scenario, net_name, save_fig_dir= save_fig_dir + 'heatmap_mean_trafo_load_all_seasons_tes_to_pv.png')


#evaluation.plot_residualload_grid_issues_subplot_overall_eva_3_plots(eva1=eva['sA106110n8winter'], eva2=eva['sA107110n8winter'], eva3=eva['sA108110n8winter'], save_fig_dir=save_fig_dir+ 'res_grid_winter_sfh15_all_tes_4plots.png')
#evaluation.plot_residualload_grid_issues_subplot_overall_eva_3_plots(eva1=eva['sB106110n8winter'], eva2=eva['sB107110n8winter'], eva3=eva['sB108110n8winter'], save_fig_dir=save_fig_dir+ 'res_grid_winter_sfh45_all_tes_4plots.png')
#evaluation.plot_residualload_grid_issues_subplot_overall_eva_3_plots(eva1=eva['sC106110n8winter'], eva2=eva['sC107110n8winter'], eva3=eva['sC108110n8winter'], save_fig_dir=save_fig_dir+ 'res_grid_winter_sfh100_all_tes_4plots.png')
#evaluation.plot_residualload_grid_issues_subplot_overall_eva_3_plots(eva1=eva['sC008110n8winter'], eva2=eva['sC308110n8winter'], eva3=eva['sC108110n8winter'], save_fig_dir=save_fig_dir+ 'res_grid_winter_sfh100_all_pv_4plots.png')
#evaluation.plot_residualload_grid_issues_subplot_overall_eva_3_plots(eva1=eva['sA008110n8winter'], eva2=eva['sA308110n8winter'], eva3=eva['sA108110n8winter'], save_fig_dir=save_fig_dir+ 'res_grid_winter_sfh15_all_pv_4plots.png')


################################
########## Bar charts ##########
################################
# --- PV Power (curtailed, feed-in, consumed) and Load (curtailed, grid obtained, direct consumed) --- #
'''
scenario = '4101110'
seasons = ['spring','summer','autumn','winter']
eva = load_scenario_data(scenario, seasons=seasons)
evaluation.plot_bar_curtailed_power(eva, scenario=scenario, seasons = seasons, save_fig_dir=save_fig_dir)
'''

'''
scenarios = ['4101110', '6111110', '6121110', '6131110', '6141110', '6151110']
seasons = ['spring','summer','autumn','winter']
#eva = load_scenario_data(scenarios, seasons=seasons)
evaluation.plot_bar_chart_percent(eva, scenarios=scenarios, seasons = seasons, save_fig_dir=save_fig_dir)
'''

#################################
########## Other plots ##########
#################################
'''
scenarios = ['6111110', '6121110', '6131110', '6141110']
eva = load_scenario_data(scenarios)
evaluation.plot_barplots_overall_eva(eva, m, save_fig_dir=save_fig_dir)
evaluation.plot_hist_grid_issus_voltage(eva['s6111110n9summer'], eva['s6111110n9winter'], save_fig_dir+ 'hist_grid_issus_voltage.png')
'''
