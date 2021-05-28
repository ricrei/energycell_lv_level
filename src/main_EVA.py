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

output_df_dir = 'output-files/'
print('Load eva dict ...')
eva = tt.decompress_pickle(output_df_dir + 'evaluation_dict.pbz2')
'''
print('Load eva df_eva_v ...')
df_eva_v = tt.decompress_pickle(output_df_dir + 'evaluation_df_v.pbz2')
print('Load eva df_eva_l ...')
df_eva_l = tt.decompress_pickle(output_df_dir + 'evaluation_df_l.pbz2')
print('Load eva df_eva_t ...')
df_eva_t = tt.decompress_pickle(output_df_dir + 'evaluation_df_t.pbz2')
'''

n = 2    # Number of timescopes
m = 2*4  # Number of timescopes * Number of scenarios


### Violin plots ###
#evaluation.plot_violin_overall_eva(df_eva_v=df_eva_v, df_eva_l=df_eva_l, save_fig_dir=save_fig_dir)


### Barplot ###
evaluation.plot_barplots_overall_eva(eva, m, save_fig_dir=save_fig_dir)

### Heatmaps ###
evaluation.plot_heatmap_grid_issus(eva, net_name, n, save_fig_dir=save_fig_dir)

### Others ###
print('Create Other plots')
evaluation.plot_residualload_subplot_overall_eva(eva['s40n8summer']['power'], eva['s40n8winter']['power'], save_fig_dir=save_fig_dir+'plot_res_load_subplot_s40n8.png')
evaluation.plot_residualload_subplot_overall_eva(eva['s41n8summer']['power'], eva['s41n8winter']['power'], save_fig_dir=save_fig_dir+'plot_res_load_subplot_s41n8.png')

evaluation.plot_generation_consumption_as_heat_map_overall_eva(eva['s40n9winter']['power'], save_fig_dir=save_fig_dir+'gen_con_heatmap_winter.png')
evaluation.plot_generation_consumption_as_heat_map_overall_eva(eva['s40n9summer']['power'], save_fig_dir=save_fig_dir+'gen_con_heatmap_summer.png')

evaluation.plot_grid_issus_over_power(eva['s40n8winter'], save_fig_dir=save_fig_dir + 'plot_grid_issus_over_power.png')

evaluation.plot_curtailed_power(eva, save_fig_dir=save_fig_dir+'curtailed_power.png')

#evaluation.plot_grid_issus_over_time(eva['s4n9winter'], save_fig_dir+ 'plot_grid_issus_over_time_winter.png')
#evaluation.plot_grid_issus_over_time(eva['s4n9summer'], save_fig_dir+ 'plot_grid_issus_over_time_summer.png')
evaluation.plot_grid_issus_over_time_subplot(eva['s40n8summer'], eva['s40n8winter'], save_fig_dir+ 'plot_grid_issus_over_time_subplot_s40n8.png')
evaluation.plot_grid_issus_over_time_subplot(eva['s41n8summer'], eva['s41n8winter'], save_fig_dir+ 'plot_grid_issus_over_time_subplot_s41n8.png')


evaluation.plot_curtailed_power(eva, save_fig_dir=save_fig_dir)

#evaluation.plot_hist_grid_issus_voltage(eva['s40n9summer'], eva['s40n9winter'], save_fig_dir+ 'hist_grid_issus_voltage.png')
