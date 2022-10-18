import os
import csv
import sys
import time
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
scenarios = [
        #[1,0,0,0,0,0,0],
        #[2,0,0,1,1,0,0],
        #[2,0,0,1,1,1,0],
        #[3,1,0,0,0,0,0],
        #[3,1,0,0,0,1,0],
        #[4,1,0,1,1,0,1],
        [4,1,0,1,1,1,0],
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
        #[8,1,5,3,3,1,0],
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

############################
def load_scenario_data(scenarios, grids=[7,8,9,10,11]):
  print('Load eva dicts ...')
  #files = os.listdir(output_df_dir)

  eva = {}
  eva['_grids'] = grids
  eva['_scenarios'] = []
  for s in scenarios:
    eva['_scenarios'].append(''.join(str(num) for num in s))
  for n in grids:
    for s in scenarios:
      scenario = ''.join(str(num) for num in s)
      index = 's' + str(scenario) + 'n' + str(n)
      economics_folder = os.path.join("./", "output-files/001_economics/"+str(scenario)+"/"+str(net_name[n])+"/")
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


def boxplot_diff_costs_reven(eva, save_fig_dir=save_fig_dir):
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

  #'''
  fig1, ax1 = plt.subplots()
  sns.boxplot(data=df_sns, y='data_diff', x='scenario', orient='v')
  ax1.set(xlabel='Scenario', ylabel='Difference of annualized costs in euro per year')
  ax1.set_title(' ')
  
  if save_fig_dir is not None:
     plt.savefig(save_fig_dir + '00a_boxplot_diff_annualized_costs.png', bbox_inches='tight', dpi=dpi)

  fig2, ax2 = plt.subplots()
  sns.boxplot(data=df_sns, y='data', x='scenario', orient='v')
  ax2.set(xlabel='Scenario', ylabel='Annualized costs in euro per year')
  ax2.set_title(' ')
  
  if save_fig_dir is not None:
     plt.savefig(save_fig_dir + '00b_boxplot_annualized_costs.png', bbox_inches='tight', dpi=dpi)

  fig3, ax3 = plt.subplots()
  sns.boxplot(data=df_sns, y='data_diff', x='scenario', orient='v', hue='grid')
  ax3.set(xlabel='Scenario', ylabel='Difference of annualized costs in euro per year')
  ax3.set_title(' ')
  
  if save_fig_dir is not None:
     plt.savefig(save_fig_dir + '00c_boxplot_diff_annualized_costs_grids.png', bbox_inches='tight', dpi=dpi)

  fig4, ax4 = plt.subplots()
  sns.boxplot(data=df_sns, y='data', x='scenario', orient='v', hue='grid')
  ax4.set(xlabel='Scenario', ylabel='Annualized costs in euro per year')
  ax4.set_title(' ')
  
  if save_fig_dir is not None:
     plt.savefig(save_fig_dir + '00d_boxplot_annualized_costs_grids.png', bbox_inches='tight', dpi=dpi)

  fig5, ax5 = plt.subplots()
  sns.boxplot(data=df_sns, y='data_diff', x='grid', orient='v', hue='scenario')
  ax5.set(xlabel='Scenario', ylabel='Difference of annualized costs in euro per year')
  ax5.set_title(' ')
  
  if save_fig_dir is not None:
     plt.savefig(save_fig_dir + '00e_boxplot_diff_annualized_costs_grids.png', bbox_inches='tight', dpi=dpi)

  fig6, ax6 = plt.subplots()
  sns.boxplot(data=df_sns, y='data', x='grid', orient='v', hue='scenario')
  ax6.set(xlabel='Scenario', ylabel='Annualized costs in euro per year')
  ax6.set_title(' ')
  
  if save_fig_dir is not None:
     plt.savefig(save_fig_dir + '00f_boxplot_annualized_costs_grids.png', bbox_inches='tight', dpi=dpi)
  #'''

def bar_revenue_costs(eva, save_fig_dir=save_fig_dir):
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
  '''
  ### SCENARIO - detailed ###
  # costs
  columns_costs_barplot = ['scenario', 'grid'] + columns_total + columns_costs
  df_barplot1 = df[columns_costs_barplot].groupby(['scenario']).sum().reset_index()

  df_barplot1['Ec_MV_costs'] += df_barplot1['Ec_LV_costs']
  df_barplot1['BSS_capex']   += df_barplot1['Ec_MV_costs']
  df_barplot1['BSS_opex']    += df_barplot1['BSS_capex']
  df_barplot1['TES_capex']   += df_barplot1['BSS_opex']
  df_barplot1['TES_opex']    += df_barplot1['TES_capex']
  df_barplot1['SG_capex']    += df_barplot1['TES_opex']
  df_barplot1['SG_opex']     += df_barplot1['SG_capex']

  s16 = sns.barplot(x = df_barplot1['scenario'], y = 'SG_opex',     data = df_barplot1, color = dark[7])
  s15 = sns.barplot(x = df_barplot1['scenario'], y = 'SG_capex',    data = df_barplot1, color = dark[6])
  s14 = sns.barplot(x = df_barplot1['scenario'], y = 'TES_opex',    data = df_barplot1, color = dark[5])
  s13 = sns.barplot(x = df_barplot1['scenario'], y = 'TES_capex',   data = df_barplot1, color = dark[4])
  s12 = sns.barplot(x = df_barplot1['scenario'], y = 'BSS_opex',    data = df_barplot1, color = dark[3])
  s11 = sns.barplot(x = df_barplot1['scenario'], y = 'BSS_capex',   data = df_barplot1, color = dark[2])
  s10 = sns.barplot(x = df_barplot1['scenario'], y = 'Ec_MV_costs', data = df_barplot1, color = dark[1])
  s9  = sns.barplot(x = df_barplot1['scenario'], y = 'Ec_LV_costs', data = df_barplot1, color = dark[0])

  SG_opex_bar   = mpatches.Patch(color=dark[7], label='SG opex')
  SG_capex_bar  = mpatches.Patch(color=dark[6], label='SG capex')
  TES_opex_bar  = mpatches.Patch(color=dark[5], label='TES opex')
  TES_capex_bar = mpatches.Patch(color=dark[4], label='TES capex')
  BSS_opex_bar  = mpatches.Patch(color=dark[3], label='BSS opex')
  BSS_capex_bar = mpatches.Patch(color=dark[2], label='BSS capex')
  Ec_MV_bar     = mpatches.Patch(color=dark[1], label='MV obtained')
  Ec_LV_bar     = mpatches.Patch(color=dark[0], label='LV obtained')
  handle_costs  = [Ec_LV_bar, Ec_MV_bar, BSS_capex_bar, BSS_opex_bar, TES_capex_bar, TES_opex_bar, SG_capex_bar, SG_opex_bar]

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
  plt.legend(handles = handle_reven[::-1] + handle_costs)
  plt.xlabel('Scenario')
  plt.ylabel('Revenue / Costs in Euro per Year')
  plt.show()
  '''
  #'''
  ### SCENARIO - aggregated ###
  # costs
  columns_costs_barplot = ['scenario', 'grid'] + columns_total + columns_costs
  df_barplot1 = (df[columns_costs_barplot].groupby(['scenario']).sum()/1000).reset_index()

  df_barplot1['Ec_MV_costs'] += df_barplot1['Ec_LV_costs']
  df_barplot1['BSS_capex']   += df_barplot1['Ec_MV_costs']
  df_barplot1['BSS_opex']    += df_barplot1['BSS_capex']
  df_barplot1['TES_capex']   += df_barplot1['BSS_opex']
  df_barplot1['TES_opex']    += df_barplot1['TES_capex']
  df_barplot1['SG_capex']    += df_barplot1['TES_opex']
  df_barplot1['SG_opex']     += df_barplot1['SG_capex']

  s16 = sns.barplot(x = df_barplot1['scenario'], y = 'SG_opex',     data = df_barplot1, color = rocket[1])
  #s15 = sns.barplot(x = df_barplot1['scenario'], y = 'SG_capex',    data = df_barplot1, color = dark[6])
  s14 = sns.barplot(x = df_barplot1['scenario'], y = 'TES_opex',    data = df_barplot1, color = rocket[3])
  #s13 = sns.barplot(x = df_barplot1['scenario'], y = 'TES_capex',   data = df_barplot1, color = dark[4])
  s12 = sns.barplot(x = df_barplot1['scenario'], y = 'BSS_opex',    data = df_barplot1, color = rocket[5])
  #s11 = sns.barplot(x = df_barplot1['scenario'], y = 'BSS_capex',   data = df_barplot1, color = dark[2])
  s10 = sns.barplot(x = df_barplot1['scenario'], y = 'Ec_MV_costs', data = df_barplot1, color = dark[0])
  s9  = sns.barplot(x = df_barplot1['scenario'], y = 'Ec_LV_costs', data = df_barplot1, color = dark[8])

  SG_opex_bar   = mpatches.Patch(color=rocket[1], label='SG')
  #SG_capex_bar  = mpatches.Patch(color=dark[6], label='SG capex')
  TES_opex_bar  = mpatches.Patch(color=rocket[3], label='TES')
  #TES_capex_bar = mpatches.Patch(color=dark[4], label='TES capex')
  BSS_opex_bar  = mpatches.Patch(color=rocket[5], label='BSS')
  #BSS_capex_bar = mpatches.Patch(color=dark[2], label='BSS capex')
  Ec_MV_bar     = mpatches.Patch(color=dark[0], label='MV obtained')
  Ec_LV_bar     = mpatches.Patch(color=dark[8], label='LV obtained')
  handle_costs  = [Ec_LV_bar, Ec_MV_bar, BSS_opex_bar, TES_opex_bar, SG_opex_bar]

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
  plt.legend(handles = handle_reven[::-1] + handle_costs)
  plt.xlabel('Scenario')
  plt.ylabel('Revenue / Costs in TEuro per Year')
  #plt.show()

  if save_fig_dir is not None:
     plt.savefig(save_fig_dir + '01a_RevenueCosts_Scenarios.png', bbox_inches='tight', dpi=dpi)
  #'''
  '''
  ### GRID ###
  # costs
  columns_costs_barplot = ['scenario', 'grid'] + columns_total + columns_costs
  df_barplot1 = df[columns_costs_barplot].groupby(['grid']).sum().reset_index()

  df_barplot1['Ec_MV_costs'] += df_barplot1['Ec_LV_costs']
  df_barplot1['BSS_capex']   += df_barplot1['Ec_MV_costs']
  df_barplot1['BSS_opex']    += df_barplot1['BSS_capex']
  df_barplot1['TES_capex']   += df_barplot1['BSS_opex']
  df_barplot1['TES_opex']    += df_barplot1['TES_capex']
  df_barplot1['SG_capex']    += df_barplot1['TES_opex']
  df_barplot1['SG_opex']     += df_barplot1['SG_capex']

  s16 = sns.barplot(x = df_barplot1['grid'], y = 'SG_opex',     data = df_barplot1, color = dark[7])
  s15 = sns.barplot(x = df_barplot1['grid'], y = 'SG_capex',    data = df_barplot1, color = dark[6])
  s14 = sns.barplot(x = df_barplot1['grid'], y = 'TES_opex',    data = df_barplot1, color = dark[5])
  s13 = sns.barplot(x = df_barplot1['grid'], y = 'TES_capex',   data = df_barplot1, color = dark[4])
  s12 = sns.barplot(x = df_barplot1['grid'], y = 'BSS_opex',    data = df_barplot1, color = dark[3])
  s11 = sns.barplot(x = df_barplot1['grid'], y = 'BSS_capex',   data = df_barplot1, color = dark[2])
  s10 = sns.barplot(x = df_barplot1['grid'], y = 'Ec_MV_costs', data = df_barplot1, color = dark[1])
  s9  = sns.barplot(x = df_barplot1['grid'], y = 'Ec_LV_costs', data = df_barplot1, color = dark[0])

  SG_opex_bar   = mpatches.Patch(color=dark[7], label='SG opex')
  SG_capex_bar  = mpatches.Patch(color=dark[6], label='SG capex')
  TES_opex_bar  = mpatches.Patch(color=dark[5], label='TES opex')
  TES_capex_bar = mpatches.Patch(color=dark[4], label='TES capex')
  BSS_opex_bar  = mpatches.Patch(color=dark[3], label='BSS opex')
  BSS_capex_bar = mpatches.Patch(color=dark[2], label='BSS capex')
  Ec_MV_bar     = mpatches.Patch(color=dark[1], label='MV obtained')
  Ec_LV_bar     = mpatches.Patch(color=dark[0], label='LV obtained')
  handle_costs  = [Ec_LV_bar, Ec_MV_bar, BSS_capex_bar, BSS_opex_bar, TES_capex_bar, TES_opex_bar, SG_capex_bar, SG_opex_bar]

  # revenues
  columns_reven_barplot = ['scenario', 'grid'] + columns_reven
  df_barplot2 = df[columns_reven_barplot].groupby(['grid']).sum().reset_index()

  df_barplot2['Ec_self_flex_reven'] += df_barplot2['Eg_self_flex_reven']
  df_barplot2['Eg_LV_flex_reven']   += df_barplot2['Ec_self_flex_reven']
  df_barplot2['Ec_LV_flex_reven']   += df_barplot2['Eg_LV_flex_reven']
  df_barplot2['Eg_LV_reven']        += df_barplot2['Ec_LV_flex_reven']
  df_barplot2['Eg_MV_reven']        += df_barplot2['Eg_LV_reven']
  df_barplot2['Eg_cur_pv_reven']    += df_barplot2['Eg_MV_reven']
  df_barplot2['Ec_cur_load_reven']  += df_barplot2['Eg_cur_pv_reven']

  s8 = sns.barplot(x = df_barplot2['grid'], y = 'Ec_cur_load_reven',  data = df_barplot2, color = bright[7])
  s7 = sns.barplot(x = df_barplot2['grid'], y = 'Eg_cur_pv_reven',    data = df_barplot2, color = bright[6])
  s6 = sns.barplot(x = df_barplot2['grid'], y = 'Eg_MV_reven',        data = df_barplot2, color = bright[5])
  s5 = sns.barplot(x = df_barplot2['grid'], y = 'Eg_LV_reven',        data = df_barplot2, color = bright[4])
  s4 = sns.barplot(x = df_barplot2['grid'], y = 'Ec_LV_flex_reven',   data = df_barplot2, color = bright[3])
  s3 = sns.barplot(x = df_barplot2['grid'], y = 'Eg_LV_flex_reven',   data = df_barplot2, color = bright[2])
  s2 = sns.barplot(x = df_barplot2['grid'], y = 'Ec_self_flex_reven', data = df_barplot2, color = bright[1])
  s1 = sns.barplot(x = df_barplot2['grid'], y = 'Eg_self_flex_reven', data = df_barplot2, color = bright[0])

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
  plt.legend(handles = handle_reven[::-1] + handle_costs)
  plt.xlabel('grid')
  plt.ylabel('Revenue / Costs in Euro per Year')
  plt.show()

  ### GRID - aggregated ###
  df_hh_per_grid = pd.Series([12, 98, 118, 41, 102])
  # costs
  columns_costs_barplot = ['scenario', 'grid'] + columns_total + columns_costs
  df_barplot1 = (df[columns_costs_barplot].drop('scenario', axis=1).groupby(['grid']).sum()/1000).reset_index()
  for i in df_barplot1.index:
   for c in df_barplot1.columns:
    if c != 'grid':
     df_barplot1[c].loc[i] = df_barplot1[c].loc[i]/df_hh_per_grid.loc[i]

  df_barplot1['Ec_MV_costs'] += df_barplot1['Ec_LV_costs']
  df_barplot1['BSS_capex']   += df_barplot1['Ec_MV_costs']
  df_barplot1['BSS_opex']    += df_barplot1['BSS_capex']
  df_barplot1['TES_capex']   += df_barplot1['BSS_opex']
  df_barplot1['TES_opex']    += df_barplot1['TES_capex']
  df_barplot1['SG_capex']    += df_barplot1['TES_opex']
  df_barplot1['SG_opex']     += df_barplot1['SG_capex']

  s16 = sns.barplot(x = df_barplot1['grid'], y = 'SG_opex',     data = df_barplot1, color = rocket[1])
  #s15 = sns.barplot(x = df_barplot1['grid'], y = 'SG_capex',    data = df_barplot1, color = dark[6])
  s14 = sns.barplot(x = df_barplot1['grid'], y = 'TES_opex',    data = df_barplot1, color = rocket[3])
  #s13 = sns.barplot(x = df_barplot1['grid'], y = 'TES_capex',   data = df_barplot1, color = dark[4])
  s12 = sns.barplot(x = df_barplot1['grid'], y = 'BSS_opex',    data = df_barplot1, color = rocket[5])
  #s11 = sns.barplot(x = df_barplot1['grid'], y = 'BSS_capex',   data = df_barplot1, color = dark[2])
  s10 = sns.barplot(x = df_barplot1['grid'], y = 'Ec_MV_costs', data = df_barplot1, color = dark[0])
  s9  = sns.barplot(x = df_barplot1['grid'], y = 'Ec_LV_costs', data = df_barplot1, color = dark[8])

  SG_opex_bar   = mpatches.Patch(color=rocket[1], label='SG')
  #SG_capex_bar  = mpatches.Patch(color=dark[6], label='SG capex')
  TES_opex_bar  = mpatches.Patch(color=rocket[3], label='TES')
  #TES_capex_bar = mpatches.Patch(color=dark[4], label='TES capex')
  BSS_opex_bar  = mpatches.Patch(color=rocket[5], label='BSS')
  #BSS_capex_bar = mpatches.Patch(color=dark[2], label='BSS capex')
  Ec_MV_bar     = mpatches.Patch(color=dark[0], label='MV obtained')
  Ec_LV_bar     = mpatches.Patch(color=dark[8], label='LV obtained')
  handle_costs  = [Ec_LV_bar, Ec_MV_bar, BSS_opex_bar, TES_opex_bar, SG_opex_bar]

  # revenues
  columns_reven_barplot = ['scenario', 'grid'] + columns_reven
  df_barplot2 = (df[columns_reven_barplot].drop('scenario', axis=1).groupby(['grid']).sum()/1000).reset_index()
  for i in df_barplot2.index:
   for c in df_barplot2.columns:
    if c != 'grid':
     df_barplot2[c].loc[i] = df_barplot2[c].loc[i]/df_hh_per_grid.loc[i]

  df_barplot2['Eg_MV_reven']        += df_barplot2['Eg_LV_reven']
  df_barplot2['Eg_self_flex_reven'] += df_barplot2['Eg_MV_reven']
  df_barplot2['Ec_self_flex_reven'] += df_barplot2['Eg_self_flex_reven']
  df_barplot2['Eg_LV_flex_reven']   += df_barplot2['Ec_self_flex_reven']
  df_barplot2['Ec_LV_flex_reven']   += df_barplot2['Eg_LV_flex_reven']
  df_barplot2['Eg_cur_pv_reven']    += df_barplot2['Ec_LV_flex_reven']
  df_barplot2['Ec_cur_load_reven']  += df_barplot2['Eg_cur_pv_reven']

  s8 = sns.barplot(x = df_barplot2['grid'], y = 'Ec_cur_load_reven',  data = df_barplot2, color = bright[7])
  #s7 = sns.barplot(x = df_barplot2['grid'], y = 'Eg_cur_pv_reven',    data = df_barplot2, color = bright[6])
  s4 = sns.barplot(x = df_barplot2['grid'], y = 'Ec_LV_flex_reven',   data = df_barplot2, color = bright[6])
  s6 = sns.barplot(x = df_barplot2['grid'], y = 'Eg_MV_reven',        data = df_barplot2, color = bright[0])
  s5 = sns.barplot(x = df_barplot2['grid'], y = 'Eg_LV_reven',        data = df_barplot2, color = bright[8])
  #s3 = sns.barplot(x = df_barplot2['grid'], y = 'Eg_LV_flex_reven',   data = df_barplot2, color = bright[2])
  #s2 = sns.barplot(x = df_barplot2['grid'], y = 'Ec_self_flex_reven', data = df_barplot2, color = bright[1])
  #s1 = sns.barplot(x = df_barplot2['grid'], y = 'Eg_self_flex_reven', data = df_barplot2, color = bright[0])

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
  plt.legend(handles = handle_reven[::-1] + handle_costs)
  plt.xlabel('Grid')
  plt.ylabel('Revenue / Costs in TEuro per Year')
  plt.show()
  '''

eva = load_scenario_data(scenarios)

#boxplot_diff_costs_reven(eva)
bar_revenue_costs(eva)

