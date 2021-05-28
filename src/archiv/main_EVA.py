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

import tools.Evaluation as evaluation

# Handle date time conversions between pandas and matplotlib
from pandas.plotting import register_matplotlib_converters
register_matplotlib_converters()


### Helper Methods ###

def read_data(filename):
    data = pd.read_csv(filename, delimiter = ',', low_memory=False)#, engine='python')
    #data = data.drop(['Unnamed: 0'], axis=1)
    #data['TIMESTAMP'] = pd.to_datetime(times['TIMESTAMP'], utc=True)
    #data['timestamp'] = data['timestamp'][0:19]
    #data['timestamp'] = data['timestamp'].tz_localize()
    data['timestamp'] = pd.to_datetime(data['timestamp'], utc=False)
    data = data.set_index('timestamp')
    #data.index = pd.DatetimeIndex(data.index, tz=None, ambiguous='infer')
    #data.index = pd.to_datetime(data.index)
    #data.index = data.index.tz_localize(tz=None, ambiguous='infer')
    #data.index = data.index.tz_convert('UTC')
    data.index = data.index.tz_localize(None)

    return data

def shorted_data(data, t_freq):
    data_shorted = data.resample(t_freq).mean()
    data_shorted = data_shorted.round(4)
    data_shorted.index = pd.DatetimeIndex(data_shorted.index, tz=None, ambiguous='infer')

    return data_shorted

# Define all gird names
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
            "simbench_urban_6"]  #12

# timescopes to examine
time_scope_winter = { 'start_time' : '2017-01-04 00:00:00+01:00', 
                      'end_time'   : '2017-01-11 00:00:00+01:00',
                      't_freq'     : '1T',
                      'name'       : 'winter'
                    }


time_scope_summer = { 'start_time' : '2017-05-26 00:00:00+02:00', 
                      'end_time'   : '2017-06-02 00:00:00+02:00',
                      't_freq'     : '1T',
                      'name'       : 'summer'
                    }

# Image output directory
save_fig_dir = 'img/'


eva = {}
df_eva_v = pd.DataFrame(columns=['time', 'voltage', 'scenario', 'timescope', 'gridID', 'busID'])
df_helper_v = pd.DataFrame(columns=['time', 'voltage', 'scenario', 'timescope', 'gridID', 'busID'])

df_eva_l = pd.DataFrame(columns=['time', 'lineloading', 'scenario', 'timescope', 'gridID', 'lineID'])
df_helper_l = pd.DataFrame(columns=['time', 'lineloading', 'scenario', 'timescope', 'gridID', 'lineID'])

print('Load Data')
for time_scope_i in [time_scope_winter, time_scope_summer]:
  for net_name_i in [7, 8, 9, 10, 11]:
    for scenario_i in [10, 20, 30, 40, 41]:
        output_dir = os.path.join("./", "output-files/"+str(scenario_i)+"/"+str(net_name[net_name_i])+"/"+time_scope_i['start_time'][0:10]+"_"+time_scope_i['end_time'][0:10]+"_"+time_scope_i['t_freq']+"/")
        index = 's' + str(scenario_i) + 'n' + str(net_name_i) + str(time_scope_i['name'])
        print(index)
        eva[index] = {}
        eva[index]['scenario'] = scenario_i
        eva[index]['net_name'] = net_name[net_name_i]
        eva[index]['net_name_i'] = net_name_i
        eva[index]['time_scope_name'] = time_scope_i['name']
        eva[index]['power'] = read_data(output_dir+'power_total_MW.csv')
        eva[index]['v'] = read_data(output_dir+'res_bus_vm_pu.csv')
        eva[index]['ll'] = read_data(output_dir+'res_line_load_percent.csv')
        eva[index]['tl'] = read_data(output_dir+'res_trafo_load_percent.csv')
        eva[index]['SelfSufficiancy'], eva[index]['PVConsumption']= evaluation.calculate_relevant_outputdata_overall_eva(eva[index]['power'])
        eva[index]['v_under'], eva[index]['v_over'], eva[index]['v_events'], eva[index]['ll_over'], eva[index]['l_events'], eva[index]['tl_over'], eva[index]['t_events'] = evaluation.calculate_net_problems_overall_eva(eva[index]['v'], eva[index]['ll'], eva[index]['tl'])

      
        v = read_data(output_dir+'res_bus_vm_pu.csv')
        v = v.stack().reset_index()
        df_helper_v['voltage'] = v[0]
        df_helper_v['time'] = v['timestamp']
        df_helper_v['busID'] = v['level_1']
        df_helper_v['scenario'] = scenario_i
        df_helper_v['gridID'] = net_name_i
        df_helper_v['timescope'] = time_scope_i['name']
        df_eva_v = pd.concat([df_eva_v,df_helper_v], axis=0)

        l = read_data(output_dir+'res_line_load_percent.csv')
        l = l.stack().reset_index()
        df_helper_l['lineloading'] = l[0]
        df_helper_l['time'] = l['timestamp']
        df_helper_l['lineID'] = l['level_1']
        df_helper_l['scenario'] = scenario_i
        df_helper_l['gridID'] = net_name_i
        df_helper_l['timescope'] = time_scope_i['name']
        df_eva_l = pd.concat([df_eva_l,df_helper_l], axis=0)

df_eva_v.reset_index(drop=True, inplace=True)
df_eva_l.reset_index(drop=True, inplace=True)

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
#evaluation.plot_residualload_overall_eva(eva['s4n8winter']['power'], save_fig_dir=save_fig_dir+'plot_res_load_winter.png')
#evaluation.plot_residualload_overall_eva(eva['s4n8summer']['power'], save_fig_dir=save_fig_dir+'plot_res_load_summer.png')
evaluation.plot_residualload_subplot_overall_eva(eva['s40n8summer']['power'], eva['s40n8winter']['power'], save_fig_dir=save_fig_dir+'plot_res_load_subplot.png')

evaluation.plot_generation_consumption_as_heat_map_overall_eva(eva['s40n9winter']['power'], save_fig_dir=save_fig_dir+'gen_con_heatmap_winter.png')
evaluation.plot_generation_consumption_as_heat_map_overall_eva(eva['s40n9summer']['power'], save_fig_dir=save_fig_dir+'gen_con_heatmap_summer.png')

evaluation.plot_grid_issus_over_power(eva['s40n8winter'], save_fig_dir=save_fig_dir + 'plot_grid_issus_over_power.png')

#evaluation.plot_grid_issus_over_time(eva['s4n9winter'], save_fig_dir+ 'plot_grid_issus_over_time_winter.png')
#evaluation.plot_grid_issus_over_time(eva['s4n9summer'], save_fig_dir+ 'plot_grid_issus_over_time_summer.png')
evaluation.plot_grid_issus_over_time_subplot(eva['s40n8summer'], eva['s40n8winter'], save_fig_dir+ 'plot_grid_issus_over_time_subplot.png')

#evaluation.plot_hist_grid_issus_voltage(eva['s40n9summer'], eva['s40n9winter'], save_fig_dir+ 'hist_grid_issus_voltage.png')
