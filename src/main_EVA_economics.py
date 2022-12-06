import os
import csv
import sys
import time
import itertools
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib as mpl
import matplotlib.patches as mpatches
import pandapower.plotting.plotly as ppply
import seaborn as sns
from datetime import datetime, timedelta

# Handle date time conversions between pandas and matplotlib
from pandas.plotting import register_matplotlib_converters
register_matplotlib_converters()

import tools.tools as tt

import bz2
import _pickle as cPickle

#######################
time_scope_winter = { 'start_time' : '2017-01-03 00:00:00+01:00',
                      'end_time'   : '2017-01-10 00:00:00+01:00',
                      't_freq'     : '1T',
                      'name'       : 'winter'
                    }


time_scope_summer = { 'start_time' : '2017-05-27 00:00:00+02:00',
                      'end_time'   : '2017-06-03 00:00:00+02:00',
                      't_freq'     : '1T',
                      'name'       : 'summer'
                    }

time_scope_autumn = { 'start_time' : '2017-10-20 00:00:00+02:00',
                      'end_time'   : '2017-10-27 00:00:00+02:00',
                      't_freq'     : '1T',
                      'name'       : 'autumn'
                    }

time_scope_spring = { 'start_time' : '2017-03-05 00:00:00+01:00',
                      'end_time'   : '2017-03-12 00:00:00+01:00',
                      't_freq'     : '1T',
                      'name'       : 'spring'
                    }

time_scope_all_seasons = [
                      time_scope_spring,
                      time_scope_summer,
                      time_scope_autumn,
                      time_scope_winter
                      ]

#######################
scenarios = [
        #[1,0,0,0,0,0,0],
        #[2,0,0,1,1,0,0],
        #[2,0,0,1,1,1,0],
        #[3,1,0,0,0,0,0],
        #[3,1,0,0,0,1,0],
        [4,1,0,1,1,1,0],
        [4,1,0,1,1,0,1],
        #[6,1,1,1,1,0,0],
        #[6,1,1,1,1,1,0],
        #[6,1,2,1,1,0,0],
        #[6,1,2,1,1,1,0],
        #[6,1,3,1,1,0,0],
        [6,1,3,1,1,1,0],
        #[6,1,4,1,1,0,0],
        #[6,1,4,1,1,1,0],
        #[6,1,5,1,1,0,0],
        #[6,1,5,1,1,1,0],
        #[7,1,0,3,3,0,0],
        [7,1,0,3,3,1,0],
        #[8,1,3,3,3,0,0],
        [8,1,3,3,3,1,0],
        [8,1,3,3,3,1,1],
        [8,1,4,3,3,1,0],
        [8,1,4,3,3,1,1],
                      ]
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

save_fig_dir = 'img/economics/'
dpi = 500

scenario_names = {
  '4101110' : '4\nRef',
  '4101101' : '5\nGrid\nRein.',
  '6131110' : '6\nHBSS',
  '7103310' : '7\nFlexC',
  '8133310' : '8\nHBSS+\nFlexC',
  '8133311' : '8\nHBSS+\nFlexC+\nGridRein',
  '8143310' : '8\nCBSS+\nFlexC',
  '8143311' : '8\nCBSS+\nFlexC+\nGridRein',
}

############################
def load_scenario_data(scenarios, grids=[7,8,9,10,11]):
  print('Load eva dicts ...')
  #files = os.listdir(output_df_dir)
  economics_folder = None
  eva = {}
  eva['_grids'] = grids
  eva['_scenarios'] = []
  for s in scenarios:
    eva['_scenarios'].append(''.join(str(num) for num in s))
  for n in grids:
    for s in scenarios:
      scenario = ''.join(str(num) for num in s)
      index = 's' + str(scenario) + 'n' + str(n)
      economics_folder_before = economics_folder
      economics_folder = os.path.join("./", "output-files/001_economics/"+str(scenario)+"/"+str(net_name[n])+"/")

      check_economic_parameter(economics_folder, economics_folder_before)

      #print('Load: '+str(index))
      eva[index] = {}
      eva[index]['grid'] = n
      eva[index]['scenario'] = scenario
      eva[index]['total_HH'] = pd.read_csv(economics_folder + '10_conclusion_economics_HH.csv', delimiter = ',', low_memory=False).drop('Unnamed: 0', axis=1)
      eva[index]['total_ECM'] = pd.read_csv(economics_folder + '10_conclusion_economics_ECM.csv', delimiter = ',', low_memory=False).drop('Unnamed: 0', axis=1)
      eva[index]['energy_costs_HH'] = pd.read_csv(economics_folder + '03_Costs_per_HH_in_Euro.csv', delimiter = ',', low_memory=False).drop('Unnamed: 0', axis=1)
      eva[index]['energy_costs_ECM'] = pd.read_csv(economics_folder + '03_Costs_ECM_in_Euro.csv', delimiter = ',', low_memory=False).drop('Unnamed: 0', axis=1)
      eva[index]['energy_reven_HH'] = pd.read_csv(economics_folder + '03_Revenues_per_HH_in_Euro.csv', delimiter = ',', low_memory=False).drop('Unnamed: 0', axis=1)
      eva[index]['energy_reven_ECM'] = pd.read_csv(economics_folder + '03_Revenues_ECM_in_Euro.csv', delimiter = ',', low_memory=False).drop('Unnamed: 0', axis=1)

  return eva

def check_economic_parameter(economics_folder, economics_folder_before):
  if economics_folder_before != None:
    eco_para = pd.read_csv(economics_folder + '00_control_paramters.csv', delimiter = ',', low_memory=False, header=None)
    eco_para_before = pd.read_csv(economics_folder_before + '00_control_paramters.csv', delimiter = ',', low_memory=False, header=None)
    if not eco_para.equals(eco_para_before):
      print('Warning: Different economic parameter used!')
      print(economics_folder_before)
      print(economics_folder)

def get_component_data(scenarios, time_scope_all_seasons, grids=[7,8,9,10,11]):
  print('Load component dict ...')
  folder = None
  cd = {} # cd = component dict
  cd['_grids'] = grids
  cd['_scenarios'] = []
  for s in scenarios:
    cd['_scenarios'].append(''.join(str(num) for num in s))
  t = time_scope_winter
  for n in grids:
   for s in scenarios:
    #for t in time_scope_all_seasons:
      scenario = ''.join(str(num) for num in s)
      index = 's' + str(scenario) + 'n' + str(n)
      folder = os.path.join("./", "output-files/"+''.join(str(num) for num in s)+"/"+str(net_name[n])+"/"+t['start_time'][0:10]+"_"+t['end_time'][0:10]+"_"+t['t_freq']+"/")
      economics_folder = os.path.join("./", "output-files/001_economics/"+str(scenario)+"/"+str(net_name[n])+"/")

      cd[index] = {}
      cd[index]['grid'] = n
      cd[index]['scenario'] = scenario
      cd[index]['installed'] = pd.read_csv(folder + '02_component_data.csv', delimiter = ',', low_memory=False).drop('Unnamed: 0', axis=1)
      df = pd.read_csv(economics_folder + 'energy_share_MWh.csv', delimiter = ',', low_memory=False).drop('Unnamed: 0', axis=1)
      df['gen'] = 0
      df['con'] = 0
      for c in df.columns:
        #print(c[0:1])
        if (c[0:3] == 'Ec_') or (c == 'Ecur_load'):
          df['con'] += df[c]
        elif (c[0:3] == 'Eg_') or (c == 'Ecur_pv'):
          df['gen'] += df[c]
        else:
          pass#print('WARNING: ' + c + ' is not identified as generation or consumption')

      cd[index]['gen'] = df['gen']
      cd[index]['con'] = df['con']

  return cd


def generate_bar_plot_df(df, column):
    for index, c in enumerate(column):
      if index > 0:
        df[column[index]] += df[column[index - 1]]
    return df

def change_df_rows(df, row_ref):
  df_helper = df.loc[row_ref]
  df.loc[row_ref] = df.loc[0]
  df.loc[0] = df_helper
  return df

def rename_scenarios(df):
  for index, s in enumerate(df['scenario']):
    df['scenario'].loc[index] = scenario_names[s]
  return df


### Start evaluation methods ###
def boxplot_diff_costs_reven_HH(eva, save_fig_dir=save_fig_dir):
  ref = '4101110'

  df_sns = pd.DataFrame(columns=['hh', 'scenario', 'data', 'data_diff', 'grid'])
  for i in eva.keys():
    df_sns_helper = pd.DataFrame(columns=['hh', 'scenario', 'data', 'data_diff', 'grid'])
    if i[0] != '_':
      df_sns_helper['data'] = eva[i]['total_HH'].sum(axis=1)
      j = i[:1] + ref + i[8:]
      df_sns_helper['data_diff'] = eva[i]['total_HH'].sum(axis=1) - eva[j]['total_HH'].sum(axis=1)
      df_sns_helper['scenario'] = eva[i]['scenario']
      df_sns_helper['grid'] = eva[i]['grid']
      df_sns_helper['hh'] = eva[i]['total_HH'].index
      df_sns = pd.concat([df_sns, df_sns_helper])

  df_sns = rename_scenarios(df_sns.reset_index())

  #'''
  fig1, ax1 = plt.subplots()
  sns.boxplot(data=df_sns, y='data_diff', x='scenario', orient='v')
  ax1.set(xlabel='Scenario', ylabel='Difference of annualized costs in euro per year')
  ax1.set_title(' ')
  
  if save_fig_dir is not None:
     plt.savefig(save_fig_dir + '00a_boxplot_diff_annualized_costs_HH.png', bbox_inches='tight', dpi=dpi)

  fig2, ax2 = plt.subplots()
  sns.boxplot(data=df_sns, y='data', x='scenario', orient='v')
  ax2.set(xlabel='Scenario', ylabel='Annualized costs in euro per year')
  ax2.set_title(' ')
  
  if save_fig_dir is not None:
     plt.savefig(save_fig_dir + '00b_boxplot_annualized_costs_HH.png', bbox_inches='tight', dpi=dpi)

  fig3, ax3 = plt.subplots()
  sns.boxplot(data=df_sns, y='data_diff', x='scenario', orient='v', hue='grid')
  ax3.set(xlabel='Scenario', ylabel='Difference of annualized costs in euro per year')
  ax3.set_title(' ')
  
  if save_fig_dir is not None:
     plt.savefig(save_fig_dir + '00c_boxplot_diff_annualized_costs_grids_HH.png', bbox_inches='tight', dpi=dpi)

  fig4, ax4 = plt.subplots()
  sns.boxplot(data=df_sns, y='data', x='scenario', orient='v', hue='grid')
  ax4.set(xlabel='Scenario', ylabel='Annualized costs in euro per year')
  ax4.set_title(' ')
  
  if save_fig_dir is not None:
     plt.savefig(save_fig_dir + '00d_boxplot_annualized_costs_grids_HH.png', bbox_inches='tight', dpi=dpi)

  fig5, ax5 = plt.subplots()
  sns.boxplot(data=df_sns, y='data_diff', x='grid', orient='v', hue='scenario')
  ax5.set(xlabel='Scenario', ylabel='Difference of annualized costs in euro per year')
  ax5.set_title(' ')
  
  if save_fig_dir is not None:
     plt.savefig(save_fig_dir + '00e_boxplot_diff_annualized_costs_grids_HH.png', bbox_inches='tight', dpi=dpi)

  fig6, ax6 = plt.subplots()
  sns.boxplot(data=df_sns, y='data', x='grid', orient='v', hue='scenario')
  ax6.set(xlabel='Scenario', ylabel='Annualized costs in euro per year')
  ax6.set_title(' ')
  
  if save_fig_dir is not None:
     plt.savefig(save_fig_dir + '00f_boxplot_annualized_costs_grids_HH.png', bbox_inches='tight', dpi=dpi)
  #'''

def boxplot_diff_costs_reven_ECM(eva, save_fig_dir=save_fig_dir):
  ref = '4101110'

  print(eva['s4101101n8']['total_ECM'].sum(axis=1))

  df_sns = pd.DataFrame(columns=['hh', 'scenario', 'data', 'data_diff', 'grid'])
  for i in eva.keys():
    df_sns_helper = pd.DataFrame(columns=['hh', 'scenario', 'data', 'data_diff', 'grid'])
    if i[0] != '_':
      df_sns_helper['data'] = eva[i]['total_ECM'].sum(axis=1)
      j = i[:1] + ref + i[8:]
      df_sns_helper['data_diff'] = eva[i]['total_ECM'].sum(axis=1) - eva[j]['total_ECM'].sum(axis=1)
      df_sns_helper['scenario'] = eva[i]['scenario']
      df_sns_helper['grid'] = eva[i]['grid']
      df_sns_helper['hh'] = eva[i]['total_ECM'].index
      df_sns = pd.concat([df_sns, df_sns_helper])

  df_sns = rename_scenarios(df_sns.reset_index())

  #print(df_sns)

  #'''
  fig1, ax1 = plt.subplots()
  sns.boxplot(data=df_sns, y='data_diff', x='scenario', orient='v')
  ax1.set(xlabel='Scenario', ylabel='Difference of annualized costs in euro per year')
  ax1.set_title(' ')
  
  if save_fig_dir is not None:
     plt.savefig(save_fig_dir + '00g_boxplot_diff_annualized_costs_ECM.png', bbox_inches='tight', dpi=dpi)

  fig2, ax2 = plt.subplots()
  sns.boxplot(data=df_sns, y='data', x='scenario', orient='v')
  ax2.set(xlabel='Scenario', ylabel='Annualized costs in euro per year')
  ax2.set_title(' ')
  
  if save_fig_dir is not None:
     plt.savefig(save_fig_dir + '00h_boxplot_annualized_costs_ECM.png', bbox_inches='tight', dpi=dpi)

  fig3, ax3 = plt.subplots()
  sns.boxplot(data=df_sns, y='data_diff', x='scenario', orient='v', hue='grid')
  ax3.set(xlabel='Scenario', ylabel='Difference of annualized costs in euro per year')
  ax3.set_title(' ')
  
  if save_fig_dir is not None:
     plt.savefig(save_fig_dir + '00i_boxplot_diff_annualized_costs_grids_ECM.png', bbox_inches='tight', dpi=dpi)

  fig4, ax4 = plt.subplots()
  sns.boxplot(data=df_sns, y='data', x='scenario', orient='v', hue='grid')
  ax4.set(xlabel='Scenario', ylabel='Annualized costs in euro per year')
  ax4.set_title(' ')
  
  if save_fig_dir is not None:
     plt.savefig(save_fig_dir + '00j_boxplot_annualized_costs_grids_ECM.png', bbox_inches='tight', dpi=dpi)

  fig5, ax5 = plt.subplots()
  sns.boxplot(data=df_sns, y='data_diff', x='grid', orient='v', hue='scenario')
  ax5.set(xlabel='Scenario', ylabel='Difference of annualized costs in euro per year')
  ax5.set_title(' ')
  
  if save_fig_dir is not None:
     plt.savefig(save_fig_dir + '00k_boxplot_diff_annualized_costs_grids_ECM.png', bbox_inches='tight', dpi=dpi)

  fig6, ax6 = plt.subplots()
  sns.boxplot(data=df_sns, y='data', x='grid', orient='v', hue='scenario')
  ax6.set(xlabel='Scenario', ylabel='Annualized costs in euro per year')
  ax6.set_title(' ')
  
  if save_fig_dir is not None:
     plt.savefig(save_fig_dir + '00l_boxplot_annualized_costs_grids_ECM.png', bbox_inches='tight', dpi=dpi)
  #'''

def bar_revenue_costs_HH(eva, save_fig_dir=save_fig_dir):
  # get all column names of costs and revenues
  for i in list(eva.keys()):
    if i[0] != '_':
      break

  columns_total = list(eva[i]['total_HH'].columns[:-2])
  columns_costs = list(eva[i]['energy_costs_HH'].columns)
  columns_reven = list(eva[i]['energy_reven_HH'].columns)
  l = ['scenario','grid'] + columns_total + columns_costs + columns_reven
  
  df = pd.DataFrame(columns=l, index=range(0,len(eva['_scenarios'])*len(eva['_grids'])))

  k = 0
  for i in list(eva.keys()):
    if i[0] != '_':
      df['scenario'].loc[k] = eva[i]['scenario']
      df['grid'].loc[k] = eva[i]['grid']
      for c in columns_total:
        df[c].loc[k] = eva[i]['total_HH'].sum()[c]
      for c in columns_costs:
        df[c].loc[k] = -eva[i]['energy_costs_HH'].sum()[c]
      for c in columns_reven:
        df[c].loc[k] = eva[i]['energy_reven_HH'].sum()[c]
      k += 1

  # colors
  bright = sns.color_palette("bright", 10)
  dark = sns.color_palette("dark", 10)
  colors = ['red', dark[3], 'blue', dark[0], 'green', 'yellow']
  rocket = sns.color_palette("rocket")

  #'''
  ### SCENARIO - detailed ###
  # costs
  columns_costs_barplot = ['scenario', 'grid'] + columns_total + columns_costs
  df_barplot1 = df[columns_costs_barplot].groupby(['scenario']).sum().reset_index()

  column = ['Ec_LV_costs', 'Ec_LV_gc_costs', 'Ec_MV_gc_costs', 'Ec_MV_costs', 'PV_capex', 'PV_opex', 'BSS_capex', 'BSS_opex', 'TES_capex', 'TES_opex', 'SG_capex', 'SG_opex']

  df_barplot1 = generate_bar_plot_df(df_barplot1, column)
  df_barplot1 = rename_scenarios(df_barplot1)
  df_barplot1 = change_df_rows(df_barplot1, row_ref=1)

  fig7, ax7 = plt.subplots()

  s16 = sns.barplot(x = df_barplot1['scenario'], y = 'SG_opex',     data = df_barplot1, color = dark[7])
  s15 = sns.barplot(x = df_barplot1['scenario'], y = 'SG_capex',    data = df_barplot1, color = dark[6])
  s14 = sns.barplot(x = df_barplot1['scenario'], y = 'TES_opex',    data = df_barplot1, color = dark[5])
  s13 = sns.barplot(x = df_barplot1['scenario'], y = 'TES_capex',   data = df_barplot1, color = dark[4])
  s12 = sns.barplot(x = df_barplot1['scenario'], y = 'BSS_opex',    data = df_barplot1, color = dark[3])
  s11 = sns.barplot(x = df_barplot1['scenario'], y = 'BSS_capex',   data = df_barplot1, color = dark[2])
  s12b = sns.barplot(x = df_barplot1['scenario'], y = 'PV_opex',     data = df_barplot1, color = dark[1])
  s11b = sns.barplot(x = df_barplot1['scenario'], y = 'PV_capex',    data = df_barplot1, color = dark[0])
  s10 = sns.barplot(x = df_barplot1['scenario'], y = 'Ec_MV_costs',    data = df_barplot1, color = dark[1])
  s10 = sns.barplot(x = df_barplot1['scenario'], y = 'Ec_MV_gc_costs', data = df_barplot1, color = dark[1])
  s9  = sns.barplot(x = df_barplot1['scenario'], y = 'Ec_LV_gc_costs', data = df_barplot1, color = dark[0])
  s9  = sns.barplot(x = df_barplot1['scenario'], y = 'Ec_LV_costs',    data = df_barplot1, color = dark[0])

  num_locations = len(df_barplot1.scenario.unique())
  hatches = itertools.cycle(['', '', '', '', '', '', '', '', '', '////', '////', ''])
  for i, bar in enumerate(ax7.patches):
    if i % num_locations == 0:
        hatch = next(hatches)
    bar.set_hatch(hatch)

  SG_opex_bar   = mpatches.Patch(color=dark[7], label='SG opex')
  SG_capex_bar  = mpatches.Patch(color=dark[6], label='SG capex')
  TES_opex_bar  = mpatches.Patch(color=dark[5], label='TES opex')
  TES_capex_bar = mpatches.Patch(color=dark[4], label='TES capex')
  PV_opex_bar  = mpatches.Patch(color=dark[1], label='PV opex')
  PV_capex_bar = mpatches.Patch(color=dark[0], label='PV capex')
  BSS_opex_bar  = mpatches.Patch(color=dark[3], label='BSS opex')
  BSS_capex_bar = mpatches.Patch(color=dark[2], label='BSS capex')
  #Ec_MV_gc_bar  = mpatches.Patch(color=dark[1], label='MV obtained')
  Ec_MV_bar     = mpatches.Patch(color=dark[1], label='MV obtained')
  #Ec_LV_gc_bar  = mpatches.Patch(color=dark[0], label='LV obtained')
  Ec_LV_bar     = mpatches.Patch(color=dark[0], label='LV obtained')
  grid_charge   = mpatches.Patch(label='grid charges')
  grid_charge.set_alpha(.1)
  grid_charge.set_hatch('////')
  handle_costs  = [Ec_LV_bar, Ec_MV_bar, PV_capex_bar, PV_opex_bar, BSS_capex_bar, BSS_opex_bar, TES_capex_bar, TES_opex_bar, SG_capex_bar, SG_opex_bar, grid_charge]

  # revenues
  columns_reven_barplot = ['scenario', 'grid'] + columns_reven
  df_barplot2 = df[columns_reven_barplot].groupby(['scenario']).sum().reset_index()

  df_barplot2['Ec_self_flex_reven'] += df_barplot2['Eg_self_flex_reven']
  df_barplot2['Eg_LV_flex_reven']   += df_barplot2['Ec_self_flex_reven']
  df_barplot2['Ec_LV_flex_reven']   += df_barplot2['Eg_LV_flex_reven']
  df_barplot2['Eg_LV_reven']        += df_barplot2['Ec_LV_flex_reven']
  df_barplot2['Eg_MV_reven']        += df_barplot2['Eg_LV_reven']
  df_barplot2['Eg_cur_pv_reven']    += df_barplot2['Eg_MV_reven']
  df_barplot2['Ec_cur_load_reven']  += df_barplot2['Eg_cur_pv_reven']

  df_barplot2 = rename_scenarios(df_barplot2)
  df_barplot2 = change_df_rows(df_barplot2, row_ref=1)

  s8 = sns.barplot(x = df_barplot2['scenario'], y = 'Ec_cur_load_reven',  data = df_barplot2, color = bright[7])
  s7 = sns.barplot(x = df_barplot2['scenario'], y = 'Eg_cur_pv_reven',    data = df_barplot2, color = bright[6])
  s6 = sns.barplot(x = df_barplot2['scenario'], y = 'Eg_MV_reven',        data = df_barplot2, color = bright[5])
  s5 = sns.barplot(x = df_barplot2['scenario'], y = 'Eg_LV_reven',        data = df_barplot2, color = bright[4])
  s4 = sns.barplot(x = df_barplot2['scenario'], y = 'Ec_LV_flex_reven',   data = df_barplot2, color = bright[3])
  s3 = sns.barplot(x = df_barplot2['scenario'], y = 'Eg_LV_flex_reven',   data = df_barplot2, color = bright[2])
  s2 = sns.barplot(x = df_barplot2['scenario'], y = 'Ec_self_flex_reven', data = df_barplot2, color = bright[1])
  s1 = sns.barplot(x = df_barplot2['scenario'], y = 'Eg_self_flex_reven', data = df_barplot2, color = bright[0])

  Ec_cur_load_bar    = mpatches.Patch(color=bright[7], label='curtailed load')
  Eg_cur_pv_flex_bar = mpatches.Patch(color=bright[6], label='curtailed pv')
  Eg_MV_bar          = mpatches.Patch(color=bright[5], label='MV feed-in')
  Eg_LV_bar          = mpatches.Patch(color=bright[4], label='LV traded')
  Ec_LV_flex_bar     = mpatches.Patch(color=bright[3], label='LV flex con')
  Eg_LV_flex_bar     = mpatches.Patch(color=bright[2], label='LV flex gen')
  Ec_self_flex_bar   = mpatches.Patch(color=bright[1], label='self flex con')
  Eg_self_flex_bar   = mpatches.Patch(color=bright[0], label='self flex gen')
  handle_reven       = [Eg_self_flex_bar, Ec_self_flex_bar, Eg_LV_flex_bar, Ec_LV_flex_bar, Eg_LV_bar, Eg_MV_bar, Eg_cur_pv_flex_bar, Ec_cur_load_bar]

  # plt
  plt.legend(handles = handle_reven[::-1] + handle_costs, loc="lower right" , bbox_to_anchor=(1.4, 0.22))
  plt.xlabel('Scenario')
  plt.ylabel('Revenue / Costs in Euro per Year')
  #plt.show()

  if save_fig_dir is not None:
     plt.savefig(save_fig_dir + '01a_RevenueCosts_Scenarios_detailed_HH.png', bbox_inches='tight', dpi=dpi)
  #'''
  #'''
  ### SCENARIO - aggregated ###
  # costs
  columns_costs_barplot = ['scenario', 'grid'] + columns_total + columns_costs
  df_barplot1 = (df[columns_costs_barplot].groupby(['scenario']).sum()/1000).reset_index()

  column = ['Ec_LV_costs', 'Ec_LV_gc_costs', 'Ec_MV_gc_costs', 'Ec_MV_costs', 'PV_capex', 'PV_opex', 'BSS_capex', 'BSS_opex', 'TES_capex', 'TES_opex', 'SG_capex', 'SG_opex']

  df_barplot1 = generate_bar_plot_df(df_barplot1, column)
  df_barplot1 = rename_scenarios(df_barplot1)
  df_barplot1 = change_df_rows(df_barplot1, row_ref=1)

  fig8, ax8 = plt.subplots()

  s16 = sns.barplot(x = df_barplot1['scenario'], y = 'SG_opex',     data = df_barplot1, color = rocket[1])
  #s15 = sns.barplot(x = df_barplot1['scenario'], y = 'SG_capex',    data = df_barplot1, color = dark[6])
  s14 = sns.barplot(x = df_barplot1['scenario'], y = 'TES_opex',    data = df_barplot1, color = rocket[3])
  #s13 = sns.barplot(x = df_barplot1['scenario'], y = 'TES_capex',   data = df_barplot1, color = dark[4])
  s12 = sns.barplot(x = df_barplot1['scenario'], y = 'BSS_opex',    data = df_barplot1, color = rocket[5])
  #s11 = sns.barplot(x = df_barplot1['scenario'], y = 'BSS_capex',   data = df_barplot1, color = dark[2])
  s12b = sns.barplot(x = df_barplot1['scenario'], y = 'PV_opex',    data = df_barplot1, color = rocket[0])
  #s11b = sns.barplot(x = df_barplot1['scenario'], y = 'PV_capex',   data = df_barplot1, color = dark[0])
  s10 = sns.barplot(x = df_barplot1['scenario'], y = 'Ec_MV_costs', data = df_barplot1, color = dark[0])
  s10 = sns.barplot(x = df_barplot1['scenario'], y = 'Ec_MV_gc_costs', data = df_barplot1, color = dark[0])
  s9  = sns.barplot(x = df_barplot1['scenario'], y = 'Ec_LV_gc_costs', data = df_barplot1, color = dark[8])
  s9  = sns.barplot(x = df_barplot1['scenario'], y = 'Ec_LV_costs', data = df_barplot1, color = dark[8])

  num_locations = len(df_barplot1.scenario.unique())
  hatches = itertools.cycle(['', '', '', '', '', '////', '////', ''])
  for i, bar in enumerate(ax8.patches):
    if i % num_locations == 0:
        hatch = next(hatches)
    bar.set_hatch(hatch)

  SG_opex_bar   = mpatches.Patch(color=rocket[1], label='SG')
  #SG_capex_bar  = mpatches.Patch(color=dark[6], label='SG capex')
  TES_opex_bar  = mpatches.Patch(color=rocket[3], label='TES')
  #TES_capex_bar = mpatches.Patch(color=dark[4], label='TES capex')
  PV_opex_bar  = mpatches.Patch(color=rocket[0], label='PV')
  #PV_capex_bar = mpatches.Patch(color=dark[0], label='PV capex')
  BSS_opex_bar  = mpatches.Patch(color=rocket[5], label='BSS')
  #BSS_capex_bar = mpatches.Patch(color=dark[2], label='BSS capex')
  Ec_MV_bar     = mpatches.Patch(color=dark[0], label='MV obtained')
  Ec_LV_bar     = mpatches.Patch(color=dark[8], label='LV obtained')
  grid_charge   = mpatches.Patch(label='grid charges')
  grid_charge.set_alpha(.1)
  grid_charge.set_hatch('////')
  handle_costs  = [Ec_LV_bar, Ec_MV_bar, PV_opex_bar, BSS_opex_bar, TES_opex_bar, SG_opex_bar, grid_charge]

  # revenues
  columns_reven_barplot = ['scenario', 'grid'] + columns_reven
  df_barplot2 = (df[columns_reven_barplot].groupby(['scenario']).sum()/1000).reset_index()

  df_barplot2['Eg_MV_reven']        += df_barplot2['Eg_LV_reven']
  df_barplot2['Eg_self_flex_reven'] += df_barplot2['Eg_MV_reven']
  df_barplot2['Ec_self_flex_reven'] += df_barplot2['Eg_self_flex_reven']
  df_barplot2['Eg_LV_flex_reven']   += df_barplot2['Ec_self_flex_reven']
  df_barplot2['Ec_LV_flex_reven']   += df_barplot2['Eg_LV_flex_reven']
  df_barplot2['Eg_cur_pv_reven']    += df_barplot2['Ec_LV_flex_reven']
  df_barplot2['Ec_cur_load_reven']  += df_barplot2['Eg_cur_pv_reven']

  df_barplot2 = rename_scenarios(df_barplot2)
  df_barplot2 = change_df_rows(df_barplot2, row_ref=1)

  s8 = sns.barplot(x = df_barplot2['scenario'], y = 'Ec_cur_load_reven',  data = df_barplot2, color = bright[7])
  #s7 = sns.barplot(x = df_barplot2['scenario'], y = 'Eg_cur_pv_reven',    data = df_barplot2, color = bright[6])
  s4 = sns.barplot(x = df_barplot2['scenario'], y = 'Ec_LV_flex_reven',   data = df_barplot2, color = bright[6])
  s6 = sns.barplot(x = df_barplot2['scenario'], y = 'Eg_MV_reven',        data = df_barplot2, color = bright[0])
  s5 = sns.barplot(x = df_barplot2['scenario'], y = 'Eg_LV_reven',        data = df_barplot2, color = bright[8])
  #s3 = sns.barplot(x = df_barplot2['scenario'], y = 'Eg_LV_flex_reven',   data = df_barplot2, color = bright[2])
  #s2 = sns.barplot(x = df_barplot2['scenario'], y = 'Ec_self_flex_reven', data = df_barplot2, color = bright[1])
  #s1 = sns.barplot(x = df_barplot2['scenario'], y = 'Eg_self_flex_reven', data = df_barplot2, color = bright[0])

  Ec_cur_load_bar    = mpatches.Patch(color=bright[7], label='Curtailed PV + load')
  #Eg_cur_pv_flex_bar = mpatches.Patch(color=bright[6], label='curtailed pv')
  Eg_MV_bar          = mpatches.Patch(color=bright[0], label='MV feed-in')
  Eg_LV_bar          = mpatches.Patch(color=bright[8], label='LV traded')
  Ec_LV_flex_bar     = mpatches.Patch(color=bright[6], label='Flexibility')
  #Eg_LV_flex_bar     = mpatches.Patch(color=bright[2], label='LV flex gen')
  #Ec_self_flex_bar   = mpatches.Patch(color=bright[1], label='self flex con')
  #Eg_self_flex_bar   = mpatches.Patch(color=bright[0], label='self flex gen')
  handle_reven       = [Eg_LV_bar, Eg_MV_bar, Ec_LV_flex_bar, Ec_cur_load_bar]

  # plt
  plt.legend(handles = handle_reven[::-1] + handle_costs, loc="lower right" , bbox_to_anchor=(1.4, 0.22))
  plt.xlabel('Scenario')
  plt.ylabel('Revenue / Costs in TEuro per Year')
  #plt.show()

  if save_fig_dir is not None:
     plt.savefig(save_fig_dir + '01b_RevenueCosts_Scenarios_HH.png', bbox_inches='tight', dpi=dpi)
  #'''

def bar_revenue_costs_HH_each_HH(eva, save_fig_dir=save_fig_dir):
  # get all column names of costs and revenues
  for i in list(eva.keys()):
    if i[0] != '_':
      break

  columns_total = list(eva[i]['total_HH'].columns[:-2])
  columns_costs = list(eva[i]['energy_costs_HH'].columns)
  columns_reven = list(eva[i]['energy_reven_HH'].columns)
  l = ['scenario','grid','hh'] + columns_total + columns_costs + columns_reven
  
  df = pd.DataFrame(columns=l)


  for i in list(eva.keys()):
    df_helper = pd.DataFrame(columns=l)
    if i[0] != '_':
      for c in columns_total:
        df_helper[c] = eva[i]['total_HH'][c]
      for c in columns_costs:
        df_helper[c] = -eva[i]['energy_costs_HH'][c]
      for c in columns_reven:
        df_helper[c] = eva[i]['energy_reven_HH'][c]
      df_helper['scenario'] = eva[i]['scenario']
      df_helper['grid'] = eva[i]['grid']
      df_helper['hh'] = df_helper.index

      df = pd.concat([df, df_helper])
  df = df.reset_index()

  # colors
  bright = sns.color_palette("bright", 10)
  dark = sns.color_palette("dark", 10)
  colors = ['red', dark[3], 'blue', dark[0], 'green', 'yellow']
  rocket = sns.color_palette("rocket")

  #'''
  ### SCENARIO - detailed ###
  # costs
  columns_costs_barplot = ['scenario', 'grid', 'hh'] + columns_total + columns_costs
  columns_reven_barplot = ['scenario', 'grid','hh'] + columns_reven

  for g in [7,8,9,10,11]:
    print('Grid: '+str(g))
    df_bar = df[df['grid'] == g]
    df_barplot_one = df_bar[columns_costs_barplot]# df[columns_costs_barplot].groupby(['scenario']).sum().reset_index()
    df_barplot_two = df_bar[columns_reven_barplot]#(df[columns_reven_barplot].groupby(['scenario']).sum()/1000).reset_index()
    for hh in range(df_barplot_one['hh'][df_barplot_one['grid'] == g].max()+1):
      print('HoHo: '+str(hh))
      df_barplot1 = df_barplot_one[df_barplot_one['hh'] == hh].reset_index()
      df_barplot2 = df_barplot_two[df_barplot_two['hh'] == hh].reset_index()
      

      column = ['Ec_LV_costs', 'Ec_LV_gc_costs', 'Ec_MV_gc_costs', 'Ec_MV_costs', 'PV_capex', 'PV_opex', 'BSS_capex', 'BSS_opex', 'TES_capex', 'TES_opex', 'SG_capex', 'SG_opex']

      df_barplot1 = generate_bar_plot_df(df_barplot1, column)
      df_barplot1 = rename_scenarios(df_barplot1)
      df_barplot1 = change_df_rows(df_barplot1, row_ref=0)

      fig8, ax8 = plt.subplots()

      s16 = sns.barplot(x = df_barplot1['scenario'], y = 'SG_opex',     data = df_barplot1, color = rocket[1])
      s14 = sns.barplot(x = df_barplot1['scenario'], y = 'TES_opex',    data = df_barplot1, color = rocket[3])
      s12 = sns.barplot(x = df_barplot1['scenario'], y = 'BSS_opex',    data = df_barplot1, color = rocket[5])
      s12b = sns.barplot(x = df_barplot1['scenario'], y = 'PV_opex',    data = df_barplot1, color = rocket[0])
      s10 = sns.barplot(x = df_barplot1['scenario'], y = 'Ec_MV_costs', data = df_barplot1, color = dark[0])
      s10 = sns.barplot(x = df_barplot1['scenario'], y = 'Ec_MV_gc_costs', data = df_barplot1, color = dark[0])
      s9  = sns.barplot(x = df_barplot1['scenario'], y = 'Ec_LV_gc_costs', data = df_barplot1, color = dark[8])
      s9  = sns.barplot(x = df_barplot1['scenario'], y = 'Ec_LV_costs', data = df_barplot1, color = dark[8])

      num_locations = len(df_barplot1.scenario.unique())
      hatches = itertools.cycle(['', '', '', '', '', '////', '////', ''])
      for i, bar in enumerate(ax8.patches):
        if i % num_locations == 0:
            hatch = next(hatches)
        bar.set_hatch(hatch)

      SG_opex_bar   = mpatches.Patch(color=rocket[1], label='SG')
      #SG_capex_bar  = mpatches.Patch(color=dark[6], label='SG capex')
      TES_opex_bar  = mpatches.Patch(color=rocket[3], label='TES')
      #TES_capex_bar = mpatches.Patch(color=dark[4], label='TES capex')
      PV_opex_bar  = mpatches.Patch(color=rocket[0], label='PV')
      #PV_capex_bar = mpatches.Patch(color=dark[0], label='PV capex')
      BSS_opex_bar  = mpatches.Patch(color=rocket[5], label='BSS')
      #BSS_capex_bar = mpatches.Patch(color=dark[2], label='BSS capex')
      Ec_MV_bar     = mpatches.Patch(color=dark[0], label='MV obtained')
      Ec_LV_bar     = mpatches.Patch(color=dark[8], label='LV obtained')
      grid_charge   = mpatches.Patch(label='grid charges')
      grid_charge.set_alpha(.1)
      grid_charge.set_hatch('////')
      handle_costs  = [Ec_LV_bar, Ec_MV_bar, PV_opex_bar, BSS_opex_bar, TES_opex_bar, SG_opex_bar, grid_charge]

      # revenues
      df_barplot2['Eg_MV_reven']        += df_barplot2['Eg_LV_reven']
      df_barplot2['Eg_self_flex_reven'] += df_barplot2['Eg_MV_reven']
      df_barplot2['Ec_self_flex_reven'] += df_barplot2['Eg_self_flex_reven']
      df_barplot2['Eg_LV_flex_reven']   += df_barplot2['Ec_self_flex_reven']
      df_barplot2['Ec_LV_flex_reven']   += df_barplot2['Eg_LV_flex_reven']
      df_barplot2['Eg_cur_pv_reven']    += df_barplot2['Ec_LV_flex_reven']
      df_barplot2['Ec_cur_load_reven']  += df_barplot2['Eg_cur_pv_reven']

      df_barplot2 = rename_scenarios(df_barplot2)
      df_barplot2 = change_df_rows(df_barplot2, row_ref=0)

      s8 = sns.barplot(x = df_barplot2['scenario'], y = 'Ec_cur_load_reven',  data = df_barplot2, color = bright[7])
      #s7 = sns.barplot(x = df_barplot2['scenario'], y = 'Eg_cur_pv_reven',    data = df_barplot2, color = bright[6])
      s4 = sns.barplot(x = df_barplot2['scenario'], y = 'Ec_LV_flex_reven',   data = df_barplot2, color = bright[6])
      s6 = sns.barplot(x = df_barplot2['scenario'], y = 'Eg_MV_reven',        data = df_barplot2, color = bright[0])
      s5 = sns.barplot(x = df_barplot2['scenario'], y = 'Eg_LV_reven',        data = df_barplot2, color = bright[8])
      #s3 = sns.barplot(x = df_barplot2['scenario'], y = 'Eg_LV_flex_reven',   data = df_barplot2, color = bright[2])
      #s2 = sns.barplot(x = df_barplot2['scenario'], y = 'Ec_self_flex_reven', data = df_barplot2, color = bright[1])
      #s1 = sns.barplot(x = df_barplot2['scenario'], y = 'Eg_self_flex_reven', data = df_barplot2, color = bright[0])

      Ec_cur_load_bar    = mpatches.Patch(color=bright[7], label='Curtailed PV + load')
      #Eg_cur_pv_flex_bar = mpatches.Patch(color=bright[6], label='curtailed pv')
      Eg_MV_bar          = mpatches.Patch(color=bright[0], label='MV feed-in')
      Eg_LV_bar          = mpatches.Patch(color=bright[8], label='LV traded')
      Ec_LV_flex_bar     = mpatches.Patch(color=bright[6], label='Flexibility')
      #Eg_LV_flex_bar     = mpatches.Patch(color=bright[2], label='LV flex gen')
      #Ec_self_flex_bar   = mpatches.Patch(color=bright[1], label='self flex con')
      #Eg_self_flex_bar   = mpatches.Patch(color=bright[0], label='self flex gen')
      handle_reven       = [Eg_LV_bar, Eg_MV_bar, Ec_LV_flex_bar, Ec_cur_load_bar]

      # plt
      plt.legend(handles = handle_reven[::-1] + handle_costs, loc="lower right" , bbox_to_anchor=(1.4, 0.22))
      plt.xlabel('Scenario')
      plt.ylabel('Revenue / Costs in TEuro per Year')
      #plt.show()

      if save_fig_dir is not None:
         plt.savefig(save_fig_dir + '01e_RevenueCosts_Scenarios_grid'+str(g)+'_hh'+str(hh)+'.png', bbox_inches='tight', dpi=dpi)
  #'''



def bar_revenue_costs_ECM(eva, save_fig_dir=save_fig_dir):
  # get all column names of costs and revenues
  for i in list(eva.keys()):
    if i[0] != '_':
      break

  columns_total = list(eva[i]['total_ECM'].columns[:-2])
  columns_costs = list(eva[i]['energy_costs_ECM'].columns)
  columns_reven = list(eva[i]['energy_reven_ECM'].columns)
  l = ['scenario','grid'] + columns_total + columns_costs + columns_reven
  
  df = pd.DataFrame(columns=l, index=range(0,len(eva['_scenarios'])*len(eva['_grids'])))

  k = 0
  for i in list(eva.keys()):
    if i[0] != '_':
      df['scenario'].loc[k] = eva[i]['scenario']
      df['grid'].loc[k] = eva[i]['grid']
      for c in columns_total:
        df[c].loc[k] = eva[i]['total_ECM'].sum()[c]
      for c in columns_costs:
        df[c].loc[k] = -eva[i]['energy_costs_ECM'].sum()[c]
      for c in columns_reven:
        df[c].loc[k] = eva[i]['energy_reven_ECM'].sum()[c]
      k += 1

  # colors
  bright = sns.color_palette("bright", 10)
  dark = sns.color_palette("dark", 10)
  colors = ['red', dark[3], 'blue', dark[0], 'green', 'yellow']
  rocket = sns.color_palette("rocket")

  #'''
  ### SCENARIO - detailed ###
  # costs
  columns_costs_barplot = ['scenario', 'grid'] + columns_total + columns_costs
  df_barplot1 = df[columns_costs_barplot].groupby(['scenario']).sum().reset_index()

  column = ['bss_LV_costs', 'curtailed_load', 'curtailed_pv', 'flex_LV', 'flex_self', 'Grid_Trafo_capex', 'Grid_Trafo_opex', 'Grid_Lines_capex', 'Grid_Lines_opex', 'BSS_capex', 'BSS_opex']

  df_barplot1 = generate_bar_plot_df(df_barplot1, column)
  df_barplot1 = change_df_rows(df_barplot1, row_ref=1)
  df_barplot1 = rename_scenarios(df_barplot1)

  fig7, ax7 = plt.subplots()

  s16 = sns.barplot(x = df_barplot1['scenario'], y = column[-1], data = df_barplot1, color = dark[7])
  s15 = sns.barplot(x = df_barplot1['scenario'], y = column[-2], data = df_barplot1, color = dark[6])
  s14 = sns.barplot(x = df_barplot1['scenario'], y = column[-3], data = df_barplot1, color = dark[5])
  s13 = sns.barplot(x = df_barplot1['scenario'], y = column[-4], data = df_barplot1, color = dark[4])
  s12 = sns.barplot(x = df_barplot1['scenario'], y = column[-5], data = df_barplot1, color = dark[3])
  s11 = sns.barplot(x = df_barplot1['scenario'], y = column[-6], data = df_barplot1, color = dark[2])
  s10 = sns.barplot(x = df_barplot1['scenario'], y = column[-7], data = df_barplot1, color = dark[1])
  s9  = sns.barplot(x = df_barplot1['scenario'], y = column[-8], data = df_barplot1, color = dark[0])
  s8  = sns.barplot(x = df_barplot1['scenario'], y = column[-9], data = df_barplot1, color = dark[8])
  s7  = sns.barplot(x = df_barplot1['scenario'], y = column[-10], data = df_barplot1, color = dark[9])
  s6  = sns.barplot(x = df_barplot1['scenario'], y = column[-11], data = df_barplot1, color = dark[0])

  BSS_opex_bar    = mpatches.Patch(color=dark[7], label=column[-1])
  BSS_capex_bar   = mpatches.Patch(color=dark[6], label=column[-2])
  Lines_opex_bar  = mpatches.Patch(color=dark[5], label=column[-3])
  Lines_capex_bar = mpatches.Patch(color=dark[4], label=column[-4])
  Trafo_opex_bar  = mpatches.Patch(color=dark[3], label=column[-5])
  Trafo_capex_bar = mpatches.Patch(color=dark[2], label=column[-6])
  flex_self_bar   = mpatches.Patch(color=dark[1], label=column[-7])
  flex_LV_bar     = mpatches.Patch(color=dark[0], label=column[-8])
  cur_pv_bar      = mpatches.Patch(color=dark[8], label=column[-9])
  cur_load_bar    = mpatches.Patch(color=dark[9], label=column[-10])
  bss_LV_costs_bar= mpatches.Patch(color=dark[0], label=column[-11])
  handle_costs    = [bss_LV_costs_bar,cur_load_bar, cur_pv_bar, flex_LV_bar, flex_self_bar, Trafo_capex_bar, Trafo_opex_bar, Lines_capex_bar, Lines_opex_bar, BSS_capex_bar, BSS_opex_bar]

  # revenues
  columns_reven_barplot = ['scenario', 'grid'] + columns_reven
  df_barplot2 = df[columns_reven_barplot].groupby(['scenario']).sum().reset_index()

  column = ['bss_LV_reven', 'grid_charges']

  df_barplot2 = generate_bar_plot_df(df_barplot2, column)
  df_barplot2 = change_df_rows(df_barplot2, row_ref = 1)
  df_barplot2 = rename_scenarios(df_barplot2)

  s2 = sns.barplot(x = df_barplot2['scenario'], y = column[-1], data = df_barplot2, color = bright[1])
  s1 = sns.barplot(x = df_barplot2['scenario'], y = column[-2], data = df_barplot2, color = bright[0])

  grid_charges_bar   = mpatches.Patch(color=bright[1], label=column[-1])
  bss_LV_reven_bar   = mpatches.Patch(color=bright[0], label=column[-2])
  handle_reven       = [bss_LV_reven_bar, grid_charges_bar]

  # plt
  plt.legend(handles = handle_reven[::-1] + handle_costs, loc="lower right" , bbox_to_anchor=(1.4, 0.22))
  plt.xlabel('Scenario')
  plt.ylabel('Revenue / Costs in Euro per Year')
  #plt.show()

  if save_fig_dir is not None:
     plt.savefig(save_fig_dir + '01c_RevenueCosts_Scenarios_detailed_ECM.png', bbox_inches='tight', dpi=dpi)
  #'''
  #'''
  ### SCENARIO - aggregated ###
  # costs
  columns_costs_barplot = ['scenario', 'grid'] + columns_total + columns_costs
  df_barplot1 = (df[columns_costs_barplot].groupby(['scenario']).sum()/1000).reset_index()

  column = ['bss_LV_costs', 'curtailed_load', 'curtailed_pv', 'flex_LV', 'flex_self', 'Grid_Trafo_capex', 'Grid_Trafo_opex', 'Grid_Lines_capex', 'Grid_Lines_opex', 'BSS_capex', 'BSS_opex']

  df_barplot1 = generate_bar_plot_df(df_barplot1, column)
  df_barplot1 = change_df_rows(df_barplot1, row_ref=1)
  df_barplot1 = rename_scenarios(df_barplot1)

  fig8, ax8 = plt.subplots()

  s16 = sns.barplot(x = df_barplot1['scenario'], y = column[-1], data = df_barplot1, color = dark[7])
  #s15 = sns.barplot(x = df_barplot1['scenario'], y = column[-2], data = df_barplot1, color = dark[6])
  s14 = sns.barplot(x = df_barplot1['scenario'], y = column[-3], data = df_barplot1, color = dark[5])
  #s13 = sns.barplot(x = df_barplot1['scenario'], y = column[-4], data = df_barplot1, color = dark[4])
  s12 = sns.barplot(x = df_barplot1['scenario'], y = column[-5], data = df_barplot1, color = dark[3])
  #s11 = sns.barplot(x = df_barplot1['scenario'], y = column[-6], data = df_barplot1, color = dark[2])
  s10 = sns.barplot(x = df_barplot1['scenario'], y = column[-7], data = df_barplot1, color = dark[1])
  #s9  = sns.barplot(x = df_barplot1['scenario'], y = column[-8], data = df_barplot1, color = dark[0])
  s8  = sns.barplot(x = df_barplot1['scenario'], y = column[-9], data = df_barplot1, color = dark[8])
  #s7  = sns.barplot(x = df_barplot1['scenario'], y = column[-10], data = df_barplot1, color = dark[9])
  s6  = sns.barplot(x = df_barplot1['scenario'], y = column[-11], data = df_barplot1, color = dark[0])

  BSS_opex_bar    = mpatches.Patch(color=dark[7], label='CBSS')
  #BSS_capex_bar   = mpatches.Patch(color=dark[6], label=column[-2])
  Lines_opex_bar  = mpatches.Patch(color=dark[5], label='Lines')
  #Lines_capex_bar = mpatches.Patch(color=dark[4], label=column[-4])
  Trafo_opex_bar  = mpatches.Patch(color=dark[3], label='Trafo')
  #Trafo_capex_bar = mpatches.Patch(color=dark[2], label=column[-6])
  flex_self_bar   = mpatches.Patch(color=dark[1], label='Flexibility')
  #flex_LV_bar     = mpatches.Patch(color=dark[0], label=column[-8])
  cur_pv_bar      = mpatches.Patch(color=dark[8], label='Curtailment')
  #cur_load_bar    = mpatches.Patch(color=dark[9], label=column[-10])
  bss_LV_costs_bar= mpatches.Patch(color=dark[0], label='Energy LV costs')
  handle_costs    = [bss_LV_costs_bar, cur_pv_bar, flex_self_bar, Trafo_opex_bar, Lines_opex_bar, BSS_opex_bar]

  # revenues
  columns_reven_barplot = ['scenario', 'grid'] + columns_reven
  df_barplot2 = (df[columns_reven_barplot].groupby(['scenario']).sum()/1000).reset_index()

  column = ['bss_LV_reven', 'grid_charges']

  df_barplot2 = generate_bar_plot_df(df_barplot2, column)
  df_barplot2 = change_df_rows(df_barplot2, row_ref=1)
  df_barplot2 = rename_scenarios(df_barplot2)

  s2 = sns.barplot(x = df_barplot2['scenario'], y = column[-1], data = df_barplot2, color = bright[1])
  s1 = sns.barplot(x = df_barplot2['scenario'], y = column[-2], data = df_barplot2, color = bright[0])

  grid_charges_bar   = mpatches.Patch(color=bright[1], label=column[-1])
  bss_LV_reven_bar   = mpatches.Patch(color=bright[0], label='Energy LV revenues')
  handle_reven       = [bss_LV_reven_bar, grid_charges_bar]

  # plt
  plt.legend(handles = handle_reven[::-1] + handle_costs, loc="lower right", bbox_to_anchor=(1.4, 0.22))
  plt.xlabel('Scenario')
  plt.ylabel('Revenue / Costs in TEuro per Year')
  #plt.show()

  if save_fig_dir is not None:
     plt.savefig(save_fig_dir + '01d_RevenueCosts_Scenarios_ECM.png', bbox_inches='tight', dpi=dpi)
  #'''



def plot_dot_anu_costs_over_component_data(eva, cd):
  df = pd.DataFrame(columns=['grid', 'scenario', 'x', 'y', 'z']) # x = PV energy / consumption, y = BSS capacity / consuption, z = anulised costs

  plot_scenario = '8133310'
  #plot_scenario = '4101110'
  ref_scenario = '4101110'
  #	ref_scenario = '2001110'


  for i in eva.keys():
   if i[0] != '_':
    if eva[i]['scenario'] == plot_scenario:
      df_helper = pd.DataFrame(columns=['grid', 'scenario', 'x', 'y', 'z'], index=eva[i]['total_HH'].index)
      df_helper['grid'] = eva[i]['grid']
      df_helper['scenario'] = eva[i]['scenario']
      df_helper['x'] = cd[i]['gen'] / cd[i]['con']
      df_helper['y'] = cd[i]['installed']['BSS_energy']# / cd[i]['con']
      j = i[:1] + ref_scenario + i[8:]
      df_helper['z_diff'] = eva[i]['total_HH'].sum(axis=1) - eva[j]['total_HH'].sum(axis=1)
      df_helper['z'] = eva[i]['total_HH'].sum(axis=1)
      df = pd.concat([df, df_helper])

  df = df.reset_index()
  '''
  xlabel = 'PV_Generation'
  ylabel = 'Consumption'
  zlabel = 'AnnuCosts'
  '''

  xlabel = 'PV_GenerationPerConsumption'
  ylabel = 'BSScapa'
  zlabel = 'AnnuCosts'

  for g in [7,8,9,10,11]:
    df_grid = df[df['grid'] == g]
    zzz = df_grid.eval('z_diff').rename(zlabel+' in Euro')

    f, ax = plt.subplots(figsize=(6.5, 6.5))
    sns.scatterplot(x='x', y='y', hue=zzz, size='grid', sizes=(100, 200), linewidth=0, data=df_grid, ax=ax)
    #sns.scatterplot(x='x', y='y', sizes=(100, 200), linewidth=0, data=df_grid, ax=ax)
    plt.xlabel(xlabel + ' in MWh/MWh')
    plt.ylabel(ylabel + ' in MWh')
    #plt.show()
    plt.savefig(save_fig_dir + '02_'+zlabel+'_'+xlabel+'_'+ylabel+'_grid'+str(g)+'.png', bbox_inches='tight', dpi=dpi)


def plot_anu_costs_over_component_data(eva, cd):
  df = pd.DataFrame(columns=['grid', 'scenario', 'x', 'y', 'z'])

  plot_scenario = '8133310'
  #plot_scenario = '4101110'
  ref_scenario = '4101110'
  #	ref_scenario = '2001110'


  for i in eva.keys():
   if i[0] != '_':
    if eva[i]['scenario'] == plot_scenario:
      df_helper = pd.DataFrame(columns=['grid', 'scenario', 'x', 'y', 'z'], index=eva[i]['total_HH'].index)
      df_helper['grid'] = eva[i]['grid']
      df_helper['scenario'] = eva[i]['scenario']
      j = i[:1] + ref_scenario + i[8:]
      df_helper['x'] = eva[i]['total_HH'].sum(axis=1) - eva[j]['total_HH'].sum(axis=1)#cd[i]['gen'] / cd[i]['con']
      df_helper['y'] = cd[i]['installed']['BSS_energy']# / cd[i]['con']
      df_helper['z_diff'] = eva[i]['total_HH'].sum(axis=1) - eva[j]['total_HH'].sum(axis=1)
      df_helper['z'] = eva[i]['total_HH'].sum(axis=1)
      df = pd.concat([df, df_helper])

  df = df.reset_index()

  xlabel = 'AnnuCosts'
  ylabel = 'BSScapa'
  zlabel = 'AnnuCosts'

  for g in [7,8,9,10,11]:
    df_grid = df[df['grid'] == g]
    zzz = df_grid.eval('z_diff').rename(zlabel+' in Euro')

    f, ax = plt.subplots(figsize=(6.5, 6.5))
    sns.scatterplot(x='x', y='y', size='grid', sizes=(100, 200), linewidth=0, data=df_grid, ax=ax)
    plt.xlabel(xlabel + ' in Euro')
    plt.ylabel(ylabel + ' in MWh')
    #plt.show()
    plt.savefig(save_fig_dir + '02b_'+zlabel+'_'+xlabel+'_'+ylabel+'_grid'+str(g)+'.png', bbox_inches='tight', dpi=dpi)

def evaluate_bss_sizing(eva, cd):
  df = pd.DataFrame(columns=['grid', 'scenario'])

  plot_scenario = '8133310'
  #plot_scenario = '4101110'
  ref_scenario = '4101110'
  #	ref_scenario = '2001110'


  for i in eva.keys():
   if i[0] != '_':
    if eva[i]['scenario'] == plot_scenario:
      df_helper = pd.DataFrame(columns=['grid', 'scenario'], index=eva[i]['total_HH'].index)
      df_helper['grid'] = eva[i]['grid']
      df_helper['scenario'] = eva[i]['scenario']
      df_helper['pv_power'] = cd[i]['installed']['PV_power']
      df_helper['consumption'] = cd[i]['con']
      df_helper['bss_capa'] = cd[i]['installed']['BSS_energy']*1000
      j = i[:1] + ref_scenario + i[8:]
      df_helper['annuCosts'] = eva[i]['total_HH'].sum(axis=1) - eva[j]['total_HH'].sum(axis=1)
      df = pd.concat([df, df_helper])

  df = df.reset_index()

  df['hh'] = df.index

  # Bedingung erfüllt für BSS
  df['proBSS'] = ((df['pv_power']/df['consumption']) > .5/1000)

  #print(df[df['proBSS'] != True])

  # Auslegung nach PV
  df['BSS_PV'] = 1.5*df['pv_power']*1000

  # Auslegung nach Verbrauch
  df['BSS_con'] = 1.5*df['consumption']

  # min

  mini = df['BSS_PV'] < df['BSS_con']
  df['max_bss_capa'] = 0
  df['max_bss_capa'][mini==True] = df['BSS_PV'][mini==True]
  df['max_bss_capa'][mini==False] = df['BSS_con'][mini==False]

  df['to_big'] = False
  df['to_big'] = (df['bss_capa'] > df['max_bss_capa'])

  print('BSS capacity sum    : ' + str(df['bss_capa'].sum()))
  print('max BSS capacity sum: ' + str(df['max_bss_capa'].sum()))


  f, ax = plt.subplots(figsize=(6.5, 6.5))
  sns.scatterplot(x='hh', y='bss_capa', hue='to_big', sizes=(100, 200), linewidth=0, data=df, ax=ax)
  sns.scatterplot(x='hh', y='max_bss_capa', sizes=(100, 200), linewidth=0, data=df, ax=ax, c=['#2ca02c'])
  plt.xlabel('Household')
  plt.ylabel('BSS capacity in kWh')
  #plt.legend(['BSS capacity', 'max BSS_capacity'])
  #plt.show()
  plt.savefig(save_fig_dir + '03_BSS_sizing.png', bbox_inches='tight', dpi=dpi)

  xlabel = 'AnnuCosts'
  ylabel = 'BSScapa'

  for g in [7,8,9,10,11]:
    f, ax = plt.subplots(figsize=(6.5, 6.5))
    sns.scatterplot(x='annuCosts', y='bss_capa', hue='to_big', size='grid', sizes=(100, 200), linewidth=0, data=df[df['grid']==g], ax=ax)
    plt.xlabel(xlabel + ' in Euro')
    plt.ylabel(ylabel + ' in MWh')
    #plt.show()
    plt.savefig(save_fig_dir + '03b_BSS_sizing_annuiCosts_grid'+str(g)+'.png', bbox_inches='tight', dpi=dpi)



eva = load_scenario_data(scenarios)

#boxplot_diff_costs_reven_HH(eva)
#boxplot_diff_costs_reven_ECM(eva)
#bar_revenue_costs_HH(eva)
#bar_revenue_costs_HH_each_HH(eva)
#bar_revenue_costs_ECM(eva)

cd = get_component_data(scenarios, time_scope_all_seasons)

#plot_dot_anu_costs_over_component_data(eva, cd)
#plot_anu_costs_over_component_data(eva, cd)
evaluate_bss_sizing(eva, cd)

