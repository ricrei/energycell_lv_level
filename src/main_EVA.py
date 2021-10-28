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

### RUN in develpment mode ###
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
#output_df_dir = 'output-files/000_evaluation_dicts_shortened_data/' #Tabea

print('Load eva dicts ...')
files = os.listdir(output_df_dir)

eva = {}
for index in files:
  print('Load: '+str(index))
  name = index[0:-5]
  eva[str(name)] = tt.decompress_pickle(output_df_dir + index)

'''
#print('Load eva df_eva_v ...')
#df_eva_v = tt.decompress_pickle(output_df_dir + 'evaluation_df_v.pbz2')
#print('Load eva df_eva_l ...')
#df_eva_l = tt.decompress_pickle(output_df_dir + 'evaluation_df_l.pbz2')
#print('Load eva df_eva_t ...')
#df_eva_t = tt.decompress_pickle(output_df_dir + 'evaluation_df_t.pbz2')
'''

n = 2    # Number of timescopes
m = 2*4  # Number of timescopes * Number of scenarios

### Calculations ###


### Violin plots ###
#evaluation.plot_violin_overall_eva(df_eva_v=df_eva_v, df_eva_l=df_eva_l, save_fig_dir=save_fig_dir)
#evaluation.plot_heatmap_self_sufficiency(eva, net_name, n, save_fig_dir=save_fig_dir)

### Barplot ###
#evaluation.plot_barplots_overall_eva(eva, m, save_fig_dir=save_fig_dir)

### Heatmaps ###
#plot_generation_consumption_as_heat_map_overall_eva(power, save_fig_dir=None) ###
#evaluation.plot_heatmap_grid_issus(eva, net_name, n, save_fig_dir=save_fig_dir)
#evaluation.plot_heatmap_grid_issus_with_bss(eva, net_name, n, save_fig_dir=save_fig_dir)
#evaluation.plot_heatmap_grid_issus_with_bss_curtailed(eva, net_name, n, save_fig_dir=save_fig_dir)
evaluation.plot_heatmap_curtailed_power(eva, net_name, n, save_fig_dir=save_fig_dir)
#evaluation.plot_heatmap_self_sufficiency(eva, net_name, n, save_fig_dir=save_fig_dir)

### Others ###
#####evaluation.plot_grid_issus_over_time(eva, save_fig_dir=save_fig_dir)
print('Create Other plots')

#evaluation.plot_residualload_subplot_overall_eva(eva['s400n8summer'], eva['s400n8winter'], save_fig_dir=save_fig_dir+'plot_res_load_subplot_s40n8.png')
#evaluation.plot_residualload_subplot_overall_eva(eva['s401n8summer'], eva['s401n8winter'], save_fig_dir=save_fig_dir+'plot_res_load_subplot_s41n8.png')

#Poster
evaluation.plot_residualload_subplot_overall_eva(eva['s401n9winter'], eva['s621n9winter'], save_fig_dir=save_fig_dir+'n9_winter_plot_res_load_subplot_n9_winter.png')
#Poster
evaluation.plot_grid_issus_over_time_subplot(eva_summer=eva['s401n9winter'], eva_winter=eva['s621n9winter'], detailed=True, save_fig_dir=save_fig_dir+ 'n9_winter_plot_grid_issus_over_time_subplot_n9_winter.png')

#evaluation.plot_residualload_subplot_overall_eva_timeslot(eva['s400n8summer']['power'], eva['s400n8winter']['power'], save_fig_dir=save_fig_dir+'plot_res_load_subplot_s40n8_detailed.png')
#evaluation.plot_residualload_subplot_overall_eva_timeslot(eva['s401n8summer']['power'], eva['s401n8winter']['power'], save_fig_dir=save_fig_dir+'plot_res_load_subplot_s41n8_detailed.png')

'''
#evaluation.plot_residualload_subplot_overall_eva(eva['s600n11summer']['power'], eva['s600n11winter']['power'], save_fig_dir=save_fig_dir+'plot_res_load_subplot_s600n11.png')
#evaluation.plot_residualload_subplot_overall_eva(eva['s601n11summer']['power'], eva['s601n11winter']['power'], save_fig_dir=save_fig_dir+'plot_res_load_subplot_s601n11.png')
evaluation.plot_residualload_subplot_overall_eva(eva['s600n7summer']['power'], eva['s600n7winter']['power'], save_fig_dir=save_fig_dir+'plot_res_load_subplot_s600n7.svg')
evaluation.plot_residualload_subplot_overall_eva(eva['s600n8summer']['power'], eva['s600n8winter']['power'], save_fig_dir=save_fig_dir+'plot_res_load_subplot_s600n8.svg')
evaluation.plot_residualload_subplot_overall_eva(eva['s600n9summer']['power'], eva['s600n9winter']['power'], save_fig_dir=save_fig_dir+'plot_res_load_subplot_s600n9.svg')
evaluation.plot_residualload_subplot_overall_eva(eva['s600n10summer']['power'], eva['s600n10winter']['power'], save_fig_dir=save_fig_dir+'plot_res_load_subplot_s600n10.svg')
evaluation.plot_residualload_subplot_overall_eva(eva['s600n11summer']['power'], eva['s600n11winter']['power'], save_fig_dir=save_fig_dir+'plot_res_load_subplot_s600n11.svg')
'''

#evaluation.plot_generation_consumption_as_heat_map_overall_eva(eva['s400n8winter']['power'], save_fig_dir=save_fig_dir+'gen_con_heatmap_winter.png')
#evaluation.plot_generation_consumption_as_heat_map_overall_eva(eva['s400n8summer']['power'], save_fig_dir=save_fig_dir+'gen_con_heatmap_summer.png')

#evaluation.plot_grid_issus_over_power(eva['s400n8winter'], save_fig_dir=save_fig_dir + 'plot_grid_issus_over_power.png')
#evaluation.plot_grid_issus_over_power(eva['s400n8summer'], save_fig_dir=save_fig_dir + 'plot_grid_issus_over_power.png')

#evaluation.plot_grid_issus_over_time_subplot(eva_summer=eva['s600n11summer'], eva_winter=eva['s600n11winter'], save_fig_dir=save_fig_dir+ 'plot_grid_issus_over_time_subplot_s600n11.png')
#evaluation.plot_grid_issus_over_time_subplot(eva_summer=eva['s601n11summer'], eva_winter=eva['s601n11winter'], save_fig_dir=save_fig_dir+ 'plot_grid_issus_over_time_subplot_s601n11.png')

#evaluation.plot_grid_issus_over_time_subplot(eva_summer=eva['s600n11summer'], eva_winter=eva['s600n11winter'], detailed=True, save_fig_dir=save_fig_dir+ 'plot_grid_issus_over_time_subplot_s600n11.png')
#evaluation.plot_grid_issus_over_time_subplot(eva_summer=eva['s601n11summer'], eva_winter=eva['s601n11winter'], detailed=True, save_fig_dir=save_fig_dir+ 'plot_grid_issus_over_time_subplot_s601n11.png')

#evaluation.plot_curtailed_power(eva, scenario=401 , save_fig_dir=save_fig_dir)
'''
evaluation.plot_curtailed_power(eva, scenario=601 , save_fig_dir=save_fig_dir)
evaluation.plot_curtailed_power(eva, scenario=611 , save_fig_dir=save_fig_dir)
evaluation.plot_curtailed_power(eva, scenario=621 , save_fig_dir=save_fig_dir)
evaluation.plot_curtailed_power(eva, scenario=631 , save_fig_dir=save_fig_dir)
#evaluation.plot_curtailed_power(eva, scenario=641 , save_fig_dir=save_fig_dir)
'''
#evaluation.state_of_charge(eva, net_name, n, save_fig_dir=save_fig_dir)

'''
evaluation.plot_hist_grid_issus_voltage(eva['s40n9summer'], eva['s40n9winter'], save_fig_dir+ 'hist_grid_issus_voltage.png')
'''
