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
'''
scenarios = ['4101110', '8133310']
eva = load_scenario_data(scenarios, grids=['n8'], seasons=['winter', 'summer'])
evaluation.plot_residualload_subplot_overall_eva(eva['s4101110n8summer'], eva['s4101110n8winter'], save_fig_dir=save_fig_dir+'res_s4101110n8summer_s4101110n8winter.png')
evaluation.plot_residualload_subplot_overall_eva(eva['s4101110n8winter'], eva['s8133310n8winter'], save_fig_dir=save_fig_dir+'res_s4101110n8winter_s8133310n8winter.png')
'''

# --- Components loading --- #
'''
scenarios = ['4101110', '8133310']
eva = load_scenario_data(scenarios, grids=['n8'], seasons=['summer','winter'])
evaluation.plot_grid_issus_over_time_subplot(eva1=eva['s4101110n8summer'], eva2=eva['s4101110n8winter'], detailed=True, save_fig_dir=save_fig_dir+ 'grid_s4101110n8summer_s4101110n8winter.png')
evaluation.plot_grid_issus_over_time_subplot(eva1=eva['s4101110n8winter'], eva2=eva['s8133310n8winter'], detailed=True, save_fig_dir=save_fig_dir+ 'grid_s4101110n8winter_s8133310n8winter.png')
evaluation.plot_grid_issus_over_time(eva['s4101110n8summer'], save_fig_dir=save_fig_dir+ 'n8_summer_plot_grid_issus_over_time_subplot_n8_winter_full.png')
'''
# --- Power and Components loading --- #
#'''
#scenarios = ['4101110', '6111110', '6121110', '6131110']
#scenarios = ['1000000', '4101110', '6131110', '8133310']
scenarios = ['C111010', 'C111410', 'C111510', 'C111610', 'C111710', 'B111410','A111410']
eva = load_scenario_data(scenarios, grids=['n8'], seasons=['winter'])
#evaluation.plot_residualload_grid_issues_subplot_overall_eva(eva1=eva['s4101110n8summer'], eva2=eva['s4101110n8winter'], save_fig_dir=save_fig_dir+ 'res_grid_s4101110n8summer_s4101110n8winter.png')


evaluation.plot_residualload_grid_issues_subplot_overall_eva_3_plots(eva1=eva['sA111410n8winter'], eva2=eva['sB111410n8winter'], eva3=eva['sC111410n8winter'], save_fig_dir=save_fig_dir+ 'res_grid_sABC_noBEV_winter_3plots.png')
evaluation.plot_residualload_grid_issues_subplot_overall_eva_4_plots(eva1=eva['sC111410n8winter'], eva2=eva['sC111510n8winter'], eva3=eva['sC111610n8winter'], eva4=eva['sC111710n8winter'], save_fig_dir=save_fig_dir+ 'res_grid_s4567_C_winter_4plots.png')
#'''


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
#scenarios = ['1000000', '2001110', '3100010', '4101110', '6111110', '6121110', '6131110', '6141110', '6151110', '7103310', '8133310']
scenarios = ['4101110', '6111110', '6121110', '6131110', '6141110', '6151110']
x_ticklabels      = scenarios#['Conv'   , 'EV+HP'  , 'PV'     , 'PV+EV+HP']
eva = load_scenario_data(scenarios)
evaluation.plot_heatmap_grid_issus(eva, net_name, scenarios, x_ticklabels, n, save_fig_dir=save_fig_dir)
'''

# --- Componentloading mean, peak (Scenario - Grid) --- #
'''
#scenarios = ['1000000', '2001110', '3100010', '4101110', '6131110', '7103310', '8133310']
#scenarios = ['1000000', '2001110', '3100010', '4101110']
#scenarios = ['4101110', '6111110', '6121110', '6131110', '6141110', '6151110']
scenarios = ['4101110', '6131110', '7103310', '8133310']
eva = load_scenario_data(scenarios)
#evaluation.plot_heatmap_componentloading_mean_peak(eva, net_name, columns_scenarios = ['1000000', '2001110', '3100010', '4101110', '6131110', '7103310', '8133310'], x_ticklabels = ['1', '2', '3', '4', '5', '6', '7'], save_fig_dir=save_fig_dir+'3_')
#evaluation.plot_heatmap_componentloading_mean_peak(eva, net_name, columns_scenarios = ['1000000', '2001110', '3100010', '4101110'], x_ticklabels = ['1', '2', '3', '4'], save_fig_dir=save_fig_dir+'2_')
evaluation.plot_heatmap_componentloading_mean_peak(eva, net_name, columns_scenarios = ['4101110', '6131110', '7103310', '8133310'], x_ticklabels = ['4', '5', '6', '7'], save_fig_dir=save_fig_dir+'1_')
'''

# --- Curtailment: PV-Power and Load (Scenario - Grid) --- #
#'''
scenarios = ['A111410', 'B111410','C111410', 'A111510', 'B111510','C111510', 'A111610', 'B111610','C111610', 'A111710', 'B111710','C111710']
eva = load_scenario_data(scenarios)
evaluation.plot_heatmap_curtailed_power(eva, net_name, columns_scenarios = ['A111410', 'B111410','C111410'], x_ticklabels = ['2022_gre', '2037_gre', '2045_gre'], save_fig_dir=save_fig_dir+'4')
evaluation.plot_heatmap_curtailed_power(eva, net_name, columns_scenarios = ['A111510', 'B111510','C111510'], x_ticklabels = ['2022_bal', '2037_bal', '2045_bal'], save_fig_dir=save_fig_dir+'5')
evaluation.plot_heatmap_curtailed_power(eva, net_name, columns_scenarios = ['A111610', 'B111610','C111610'], x_ticklabels = ['2022_mar', '2037_mar', '2045_mar'], save_fig_dir=save_fig_dir+'6')
evaluation.plot_heatmap_curtailed_power(eva, net_name, columns_scenarios = ['A111710', 'B111710','C111710'], x_ticklabels = ['2022_sch', '2037_sch', '2045_sch'], save_fig_dir=save_fig_dir+'7')
evaluation.plot_heatmap_curtailed_power(eva, net_name, columns_scenarios = ['A111410', 'A111510', 'A111610', 'A111710'], x_ticklabels = ['2022_gre', '2022_bal', '2022_mar', '2022_sch'], save_fig_dir=save_fig_dir+'A')
evaluation.plot_heatmap_curtailed_power(eva, net_name, columns_scenarios = ['B111410', 'B111510', 'B111610', 'B111710'], x_ticklabels = ['2037_gre', '2037_bal', '2037_mar', '2037_sch'], save_fig_dir=save_fig_dir+'B')
evaluation.plot_heatmap_curtailed_power(eva, net_name, columns_scenarios = ['C111410', 'C111510', 'C111610', 'C111710'], x_ticklabels = ['2045_gre', '2045_bal', '2045_mar', '2045_sch'], save_fig_dir=save_fig_dir+'C')
#'''

# --- Self-Sufficiancy and PV Consumption --- #
#'''
#scenarios = ['1000000', '2001110', '3100010', '4101110', '6111110', '6121110', '6131110', '6141110', '6151110', '7103310', '8133310']
#scenarios = ['4101110', '6111110', '6121110', '6131110', '6141110', '6151110']
#scenarios = ['4101110', '6131110', '7103310', '8133310']
#eva = load_scenario_data(scenarios)
#evaluation.plot_heatmap_self_sufficiency(eva, net_name, columns_scenarios=['1000000', '2001110', '3100010', '4101110'], x_ticklabels = ['1', '2', '3', '4'], n=n, save_fig_dir=save_fig_dir+'0')
#evaluation.plot_heatmap_self_sufficiency(eva, net_name, columns_scenarios=['4101110', '6111110', '6121110', '6131110', '6141110', '6151110'], x_ticklabels = ['Reference', 'd-HBSS', 'p-HBSS', 'pc-HBSS', 'pc-CBSS-LVBB', 'pc-CBSS-line'], n=n, save_fig_dir=save_fig_dir+'1')
#evaluation.plot_heatmap_self_sufficiency(eva, net_name, columns_scenarios=['4101110', '6131110', '7103310', '8133310'], x_ticklabels = ['4', '5', '6', '7'], n=n, save_fig_dir=save_fig_dir+'2')
#evaluation.plot_heatmap_self_sufficiency(eva, net_name, columns_scenarios=['4101110', '6111110', '6121110', '6131110', '6141110', '6151110', '7103310', '8133310'], x_ticklabels = ['4', '5a', '5b', '5c HH', '5c CBSS-LV', '5c CBSS feeder', '6', '7'], n=n, save_fig_dir=save_fig_dir+'3')
#evaluation.plot_heatmap_self_sufficiency(eva, net_name, columns_scenarios=['4101110', '6131110', '7103310', '8133310'], x_ticklabels = ['Reference', 'Home\nBSS', 'Smarte\nconsumers', 'BSS +\nsmarte Con.'], n=n, save_fig_dir=save_fig_dir+'4')

evaluation.plot_heatmap_self_sufficiency(eva, net_name, columns_scenarios = ['A111410', 'B111410','C111410'], x_ticklabels = ['2022_gre', '2037_gre', '2045_gre'], n=n, save_fig_dir=save_fig_dir+'4')
evaluation.plot_heatmap_self_sufficiency(eva, net_name, columns_scenarios = ['A111510', 'B111510','C111510'], x_ticklabels = ['2022_bal', '2037_bal', '2045_bal'], n=n, save_fig_dir=save_fig_dir+'5')
evaluation.plot_heatmap_self_sufficiency(eva, net_name, columns_scenarios = ['A111610', 'B111610','C111610'], x_ticklabels = ['2022_mar', '2037_mar', '2045_mar'], n=n, save_fig_dir=save_fig_dir+'6')
evaluation.plot_heatmap_self_sufficiency(eva, net_name, columns_scenarios = ['A111710', 'B111710','C111710'], x_ticklabels = ['2022_sch', '2037_sch', '2045_sch'], n=n, save_fig_dir=save_fig_dir+'7')
evaluation.plot_heatmap_self_sufficiency(eva, net_name, columns_scenarios = ['A111410', 'A111510', 'A111610', 'A111710'], x_ticklabels = ['2022_gre', '2022_bal', '2022_mar', '2022_sch'], n=n, save_fig_dir=save_fig_dir+'A')
evaluation.plot_heatmap_self_sufficiency(eva, net_name, columns_scenarios = ['B111410', 'B111510', 'B111610', 'B111710'], x_ticklabels = ['2037_gre', '2037_bal', '2037_mar', '2037_sch'], n=n, save_fig_dir=save_fig_dir+'B')
evaluation.plot_heatmap_self_sufficiency(eva, net_name, columns_scenarios = ['C111410', 'C111510', 'C111610', 'C111710'], x_ticklabels = ['2045_gre', '2045_bal', '2045_mar', '2045_sch'], n=n, save_fig_dir=save_fig_dir+'C')
#'''

# --- Curtailment: PV-Power and Load (Season - Grid) --- #
'''
scenarios = ['4101110']
eva = load_scenario_data(scenarios)
evaluation.plot_heatmap_curtailed_power_per_season(eva, scenarios, net_name, save_fig_dir=save_fig_dir)
'''

# --- Curtailment: Self-Sufficiancy and PV Consumption (Season - Grid) --- #
'''
scenario = ['8133310']
#eva = load_scenario_data(scenario)
evaluation.plot_heatmap_self_sufficiency_per_season(eva, scenario, net_name, save_fig_dir=save_fig_dir)
'''

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
