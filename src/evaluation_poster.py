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

import tools.tool_data_analysis as tda

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
    data['timestamp'] = pd.to_datetime(data['timestamp'], utc=True)
    data = data.set_index('timestamp')
    #data.index = pd.DatetimeIndex(data.index, tz=None, ambiguous='infer')
    #data.index = pd.to_datetime(data.index)
    #data.index = data.index.tz_localize(tz=None, ambiguous='infer')
    #data.index = data.index.tz_convert('UTC')
    #data.index = data.index.tz_localize(None)

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
                      't_freq'     : 'H',
                      'name'       : 'winter'
                    }


time_scope_summer = { 'start_time' : '2017-05-26 00:00:00+02:00', 
                      'end_time'   : '2017-06-02 00:00:00+02:00',
                      't_freq'     : 'H',
                      'name'       : 'summer'
                    }

eva = {}
df_eva_v = pd.DataFrame(columns=['time', 'voltage', 'scenario', 'timescope', 'gridID', 'busID'])
df_helper_v = pd.DataFrame(columns=['time', 'voltage', 'scenario', 'timescope', 'gridID', 'busID'])

df_eva_l = pd.DataFrame(columns=['time', 'lineloading', 'scenario', 'timescope', 'gridID', 'lineID'])
df_helper_l = pd.DataFrame(columns=['time', 'lineloading', 'scenario', 'timescope', 'gridID', 'lineID'])

for time_scope_i in [time_scope_winter, time_scope_summer]:
  for net_name_i in [7, 8, 9, 10, 11]:
    for scenario_i in [1, 2, 3, 4]:

        output_dir = os.path.join("./", "output-files/"+str(scenario_i)+"/"+str(net_name[net_name_i])+"/"+time_scope_i['start_time'][0:10]+"_"+time_scope_i['end_time'][0:10]+"_"+time_scope_i['t_freq']+"/")
        index = 's' + str(scenario_i) + 'n' + str(net_name_i) + str(time_scope_i['name'])

        #print(index)

        eva[index] = {}
        eva[index]['scenario'] = scenario_i
        eva[index]['net_name'] = net_name[net_name_i]
        eva[index]['net_name_i'] = net_name_i
        eva[index]['time_scope_name'] = time_scope_i['name']
        eva[index]['power'] = read_data(output_dir+'power_total_MW.csv')
        eva[index]['v'] = read_data(output_dir+'res_bus_vm_pu.csv')
        eva[index]['ll'] = read_data(output_dir+'res_line_load_percent.csv')
        eva[index]['tl'] = read_data(output_dir+'res_trafo_load_percent.csv')
        eva[index]['SelfSufficiancy'], eva[index]['PVConsumption']= tda.calculate_relevant_outputdata_overall_eva(eva[index]['power'])
        eva[index]['v_under'], eva[index]['v_over'], eva[index]['v_events'], eva[index]['ll_over'], eva[index]['l_events'], eva[index]['tl_over'], eva[index]['t_events'] = tda.calculate_net_problems_overall_eva(eva[index]['v'], eva[index]['ll'], eva[index]['tl'])

      
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

n = 2*4 # Number of timescopes * Number of scenarios


'''
### Violin plots ###
plt.figure()
ax = sns.violinplot(x="gridID", y="voltage", hue='timescope', data=df_eva_v, palette="muted", split=True, inner="quartile", cut=0)

plt.figure()
ax = sns.violinplot(x="gridID", y="lineloading", hue='timescope', data=df_eva_l, palette="muted", split=True, inner="quartile", cut=0)

plt.show()
'''

### Barplot ###
df_bar = pd.DataFrame(index=range(len(eva.keys())*4), columns=['type', 'value', 'scenario', 'gridID', 'timescope'])

v_events = 0
l_events = 0
t_events = 0

j = 0
j1 = 0
j2 = 0
for index in eva:
  j2 = 0
  for k in ['v_over','v_under','ll_over','tl_over']:
    j = j1 + j2
    df_bar['type'].iloc[j] = k
    if (k == 'v_over') | (k == 'v_under'):
     df_bar['value'].iloc[j] = eva[index][k]
    elif k == 'll_over':
     df_bar['value'].iloc[j] = eva[index][k]
    elif k == 'tl_over':
     df_bar['value'].iloc[j] = eva[index][k]
    df_bar['scenario'].iloc[j] = eva[index]['scenario']
    df_bar['gridID'].iloc[j] = eva[index]['net_name_i']
    df_bar['timescope'].iloc[j] = eva[index]['time_scope_name']
    j2 += 1
  j1 += j2
  v_events += len(eva[index]['v'].columns)/n
  l_events += len(eva[index]['ll'].columns)/n
  t_events += len(eva[index]['tl'].columns)/n

df_bar.loc[df_bar['type'] == 'v_over', 'value']  = df_bar.loc[df_bar['type'] == 'v_over', 'value']/v_events
df_bar.loc[df_bar['type'] == 'v_under', 'value'] = df_bar.loc[df_bar['type'] == 'v_under', 'value']/v_events
df_bar.loc[df_bar['type'] == 'll_over', 'value'] = df_bar.loc[df_bar['type'] == 'll_over', 'value']/l_events
df_bar.loc[df_bar['type'] == 'tl_over', 'value'] = df_bar.loc[df_bar['type'] == 'tl_over', 'value']/t_events

df_bar_1 = df_bar.groupby(['scenario', 'type'])['value'].sum()/n
df_bar_1 = df_bar_1.reset_index()

df_bar_2 = df_bar.groupby(['gridID', 'type'])['value'].sum()/n
df_bar_2 = df_bar_2.reset_index()

plt.figure()
ax = sns.barplot(x = 'scenario', y = 'value', hue = 'type', data = df_bar_1)
plt.show()

plt.figure()
ax = sns.barplot(x = 'gridID', y = 'value', hue = 'type', data = df_bar_2)
plt.show()


### Heatmaps ###
df_v_heatmap = pd.DataFrame(index=[net_name[7:12]], columns=[1,2,3,4]).fillna(0)
df_l_heatmap = pd.DataFrame(index=[net_name[7:12]], columns=[1,2,3,4]).fillna(0)
df_t_heatmap = pd.DataFrame(index=[net_name[7:12]], columns=[1,2,3,4]).fillna(0)
v_events = 0
l_events = 0
t_events = 0

for index in eva:
  df_v_heatmap[eva[index]['scenario']].loc[eva[index]['net_name']] += (eva[index]['v_under'] + eva[index]['v_over'])/n
  df_l_heatmap[eva[index]['scenario']].loc[eva[index]['net_name']] += eva[index]['ll_over']/n
  df_t_heatmap[eva[index]['scenario']].loc[eva[index]['net_name']] += eva[index]['tl_over']/n
  v_events += len(eva[index]['v'].columns)/n
  l_events += len(eva[index]['ll'].columns)/n
  t_events += len(eva[index]['tl'].columns)/n

plt.figure()
ax = sns.heatmap(df_v_heatmap/v_events, annot=True)

plt.figure()
ax = sns.heatmap(df_l_heatmap/l_events, annot=True)

plt.show()


### Others ###
#tda.plot_residualload_overall_eva(eva['s4n9winter']['power'])
#tda.plot_residualload_overall_eva(eva['s4n9summer']['power'])

#tda.plot_generation_consumption_as_heat_map_overall_eva(eva['s4n9winter']['power'])
