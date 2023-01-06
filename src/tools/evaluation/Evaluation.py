import sys
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import matplotlib as mpl
import numpy as np
import pandapower.plotting.plotly as ppply
import seaborn as sns
from datetime import datetime, timedelta

# Handle date time conversions between pandas and matplotlib
from pandas.plotting import register_matplotlib_converters
register_matplotlib_converters()

SMALL_SIZE = 8
MEDIUM_SIZE = 10
BIGGER_SIZE = 12

plt.rc('font', size=MEDIUM_SIZE)          # controls default text sizes
plt.rc('axes', titlesize=MEDIUM_SIZE)     # fontsize of the axes title
plt.rc('axes', labelsize=MEDIUM_SIZE)    # fontsize of the x and y labels
plt.rc('xtick', labelsize=MEDIUM_SIZE)    # fontsize of the tick labels
plt.rc('ytick', labelsize=MEDIUM_SIZE)    # fontsize of the tick labels
plt.rc('legend', fontsize=MEDIUM_SIZE)    # legend fontsize
plt.rc('figure', titlesize=BIGGER_SIZE)  # fontsize of the figure title

# Latex font
mpl.rcParams['mathtext.fontset'] = 'stix'
mpl.rcParams['font.family'] = 'STIXGeneral'

fig_x, fig_y = 5., 2.

image_format = 'png'
dpi = 500

lan = 'DE' # 'EN', 'DE'

if lan == 'DE':
  y_ticklabels = ['Land- \nnetz 1', 'Land- \nnetz 2', 'Land- \nnetz 3', 'Vorstadt-\nnetz 1  ', 'Vorstadt-\nnetz 2  ']
elif lan == 'EN':
  #y_ticklabels = ['Grid  \nRural 1', 'Grid  \nRural 2', 'Grid  \nRural 3', 'Grid    \nSuburb 1', 'Grid    \nSuburb 2']
  y_ticklabels = ['Rural 1', 'Rural 2', 'Rural 3', 'Suburb 1', 'Suburb 2']

### Helper Methods ###
def shorted_data(data, t_freq):
    data_shorted = data.resample(t_freq).mean()
    data_shorted = data_shorted.round(4)
    data_shorted.index = pd.DatetimeIndex(data_shorted.index, tz=None, ambiguous='infer')

    return data_shorted

### Calculate Output Data ###

def calculate_outputdata(eva, scenarios, grid, save_fig_dir=None):

  for index in eva:
   if grid in index:
    if 'spring' in index:
      power_spring = eva[index]['power']
      curtailed_power_spring = eva[index]['curtailed_power']
      power_spring['load_sum'] = power_spring.load + power_spring.hp + power_spring.ev + curtailed_power_spring.load
      power_spring['pv'] += curtailed_power_spring.pv
    if 'summer' in index:
      power_summer = eva[index]['power']
      curtailed_power_summer = eva[index]['curtailed_power']
      power_summer['load_sum'] = power_summer.load + power_summer.hp + power_summer.ev + curtailed_power_summer.load
      power_summer['pv'] += curtailed_power_summer.pv
    if 'autumn' in index:
      power_autumn = eva[index]['power']
      curtailed_power_autumn = eva[index]['curtailed_power']
      power_autumn['load_sum'] = power_autumn.load + power_autumn.hp + power_autumn.ev + curtailed_power_autumn.load
      power_autumn['pv'] += curtailed_power_autumn.pv
    if 'winter' in index:
      power_winter = eva[index]['power']
      curtailed_power_winter = eva[index]['curtailed_power']
      power_winter['load_sum'] = power_winter.load + power_winter.hp + power_winter.ev + curtailed_power_winter.load
      power_winter['pv'] += curtailed_power_winter.pv

  power = (power_spring.reset_index(drop=True) + power_summer.reset_index(drop=True) + power_autumn.reset_index(drop=True) + power_winter.reset_index(drop=True)).sum()/60
  power['load_sum'] = power.load + power.hp + power.ev
  print(' ')
  print('Grid:       ' + str(grid))
  print('PV Power:   ' + str(power.pv))
  print('Load Power: ' + str(power.load_sum))
  print('PV/Load')
  print(' year     : ' + str(power.pv/power.load_sum))
  print(' summer   : ' + str(power_summer.sum().pv/power_summer.sum().load_sum))
  print(' winter   : ' + str(power_winter.sum().pv/power_winter.sum().load_sum))

### Output plots ###
def plot_generation_consumption_as_heat_map_overall_eva(power, save_fig_dir=None):

  power_pivot = power.pivot_table(columns=power.index.dayofyear, index=power.index.hour + power.index.minute/60)

  plt.figure(figsize=(10,8))
  ax = sns.heatmap(power_pivot.pv - power_pivot.load - power_pivot.hp - power_pivot.ev, center=0)
  ax.set_xlabel('Day').set_size(20)
  ax.set_ylabel('Hour').set_size(20)
  if save_fig_dir is not None:
     plt.savefig(save_fig_dir, bbox_inches='tight', dpi=dpi)

def plot_residualload_overall_eva(power, save_fig_dir=None):

  power = -power*1000

  fig, ax = plt.subplots()
  ax.fill_between(power.index, 0, power.pv, alpha=0.7)
  ax.plot(power.index, power.pv, lw=.6)
  ax.fill_between(power.index, 0, -power.ev, alpha=0.7)
  ax.plot(power.index, -power.ev, lw=.6)
  ax.fill_between(power.index, -power.ev, -power.load-power.ev, alpha=0.7)
  ax.plot(power.index, -power.load-power.ev, lw=.6)
  ax.fill_between(power.index, -power.load-power.ev, -power.hp-power.load-power.ev, alpha=0.7)
  ax.plot(power.index, -power.hp-power.load-power.ev, lw=.6)
  #power = shorted_data(power, 'W')
  ax.plot(power.index, power.pv-power.hp-power.load-power.ev, color='black', lw=1)
  ax.set_xlabel('Time')
  ax.set_ylabel('Power in kW')
  ax.set_xticks([i for i in power.index if (i.hour == 12) & (i.minute == 0)])
  ax.set_xticklabels(['  Day 1', '  Day 2', '  Day 3', '  Day 4', '  Day 5', '  Day 6', '  Day 7'])
  ax.set(xlim=(power.index[0], power.index[-1]), ylim=(-1750, 400))
  plt.legend(['Photovoltaic generation','E-vehicle load','Household load','Heat pump load', 'Residual Load'], loc='lower right')
  if save_fig_dir is not None:
     plt.savefig(save_fig_dir, bbox_inches='tight', dpi=dpi)

def plot_residualload_subplot_overall_eva(eva1, eva2, save_fig_dir=None):

  prop_cycle = plt.rcParams['axes.prop_cycle']
  c = prop_cycle.by_key()['color']

  power_1 = eva1['power']*1
  power_2 = eva2['power']*1
  power = [power_1, power_2]
  storage_1 = -eva1['storage_power']*1
  storage_2 = -eva2['storage_power']*1
  storage = [storage_1, storage_2]
  curtailed_power_1 = eva1['curtailed_power']
  curtailed_power_2 = eva2['curtailed_power']
  curtailed = [curtailed_power_1, curtailed_power_2]

  time1 = power_1.index
  time2 = power_2.index

  day = 3
  time_min_1 = time1[(day-1)*24*60] #pd.to_datetime('2017-03-05 00:00:00+00:00', utc=True)
  time_max_1 = time1[(day)*24*60-1]#pd.to_datetime('2017-03-05 23:59:00+00:00', utc=True)

  time_min_2 = time2[(day-1)*24*60] #pd.to_datetime('2017-03-05 00:00:00+00:00', utc=True)
  time_max_2 = time2[(day)*24*60-1]#pd.to_datetime('2017-03-05 23:59:00+00:00', utc=True)

  y_max_pos = [0, 0]
  y_max_neg = [0, 0]

  fig, ax = plt.subplots(1, 2, figsize=(8,4), sharey=True,  gridspec_kw={'wspace': .05})
  for i in [0,1]:
    storage_sum = storage[i].sum(axis=1)
    storage_charge = storage[i].copy()
    storage_charge[storage_charge > 0] = 0
    storage_charge = -storage_charge
    storage_charge = storage_charge.sum(axis=1)

    storage_discharge = storage[i].copy()
    storage_discharge[storage_discharge < 0] = 0
    storage_discharge = storage_discharge.sum(axis=1)

    ax[i].fill_between(power[i].index,                     -storage_discharge,                     -storage_discharge - power[i].pv, alpha=0.7, color=c[0])
    ax[i].fill_between(power[i].index,                         storage_charge,                         power[i].ev + storage_charge, alpha=0.7, color=c[1])
    ax[i].fill_between(power[i].index,              power[i].ev + storage_charge,            power[i].load + power[i].ev + storage_charge, alpha=0.7, color=c[2])
    ax[i].fill_between(power[i].index, power[i].load + power[i].ev + storage_charge, power[i].hp + power[i].load + power[i].ev + storage_charge, alpha=0.7, color=c[3])
    ax[i].fill_between(power[i].index, 0 , storage_charge     , alpha=0.7, color=c[4])
    ax[i].fill_between(power[i].index, 0 , -storage_discharge , alpha=0.7, color=c[4])
    # curtailed power
    ax[i].fill_between(power[i].index, power[i].hp + power[i].load + power[i].ev + storage_charge, power[i].hp + power[i].load + power[i].ev + storage_charge + curtailed[i].load, alpha=0.2, color=c[7])
    ax[i].fill_between(power[i].index,                     -storage_discharge - power[i].pv,                       -storage_discharge - power[i].pv - curtailed[i].pv, alpha=0.2, color=c[7])

    ax[i].plot(power[i].index, -storage_discharge-power[i].pv, lw=.6)
    ax[i].plot(power[i].index, storage_charge+power[i].ev, lw=.6)
    ax[i].plot(power[i].index, storage_charge+power[i].load+power[i].ev, lw=.6)
    ax[i].plot(power[i].index, storage_charge+power[i].hp+power[i].load+power[i].ev, lw=.6)
    ax[i].plot(storage[i].index, storage_charge    , lw=.6)
    ax[i].plot(storage[i].index, -storage_discharge, lw=.6)

    #power[i] = shorted_data(power[i], '5T')
    #storage_sum = shorted_data(storage_sum, '5T')

    ax[i].plot(power[i].index, -(power[i].pv-power[i].hp-power[i].load-power[i].ev+storage_sum), color='black', lw=1)

    if i == 0:
      y_max_pos[i] = (power[i].hp + power[i].load + power[i].ev + storage_charge + curtailed[i].load).loc[time_min_1:time_max_1].max()
      y_max_neg[i] = (-storage_discharge - power[i].pv - curtailed[i].pv).loc[time_min_1:time_max_1].min()
    else:
      y_max_pos[i] = (power[i].hp + power[i].load + power[i].ev + storage_charge + curtailed[i].load).loc[time_min_2:time_max_2].max()
      y_max_neg[i] = (-storage_discharge - power[i].pv - curtailed[i].pv).loc[time_min_2:time_max_2].min()
    
    #ax[i].set_xticks([k for k in power[i].index if (k.hour == 12) & (k.minute == 0)])
    #ax[i].set_xticklabels(['  Day 1', '  Day 2', '  Day 3', '  Day 4', '  Day 5', '  Day 6', '  Day 7'])
    ax[i].set_xticks([k for k in power[i].index if ((k.hour == 0) or (k.hour == 6) or (k.hour == 12) or (k.hour == 18)) & (k.minute == 0)])
    ax[i].set_xticklabels(['00:00', '06:00', '12:00', '18:00']*7 + ['00:00'])
    ax[i].set(xlim=(power[i].index[0], power[i].index[-1]))#, ylim=(-1.200, 1.200))#(-1.900, .400)
    if lan == 'DE':
      patch_list = [
         mpatches.Patch(color=c[0], alpha=0.7, label='Photovoltaik'),
         mpatches.Patch(color=c[1], alpha=0.7, label='E-Auto'),
         mpatches.Patch(color=c[2], alpha=0.7, label='Haushalt'),
         mpatches.Patch(color=c[3], alpha=0.7, label='Wärmepumpe'),
         mpatches.Patch(color=c[4], alpha=0.7, label='Speicher'),
         mpatches.Patch(color=c[7], alpha=0.2, label='Abregelung')
                 ]
    elif lan == 'EN':
      patch_list = [
         mpatches.Patch(color=c[0], alpha=0.7, label='Photovoltaic'),
         mpatches.Patch(color=c[1], alpha=0.7, label='E-vehicle'),
         mpatches.Patch(color=c[2], alpha=0.7, label='Household'),
         mpatches.Patch(color=c[3], alpha=0.7, label='Heatpump'),
         mpatches.Patch(color=c[4], alpha=0.7, label='Storage'),
         mpatches.Patch(color=c[7], alpha=0.2, label='Curtailment')
                 ]

    ax[0].legend(handles=patch_list, loc='lower left', shadow=True, prop={'size': 7.5})

  if lan == 'DE':
    ax[0].set_ylabel('\nLeistung in MW\n')
    ax[0].set_xlabel('Uhrzeit')
    ax[1].set_xlabel('Uhrzeit')
    #ax[0].set_title('1')
    #ax[1].set_title('2')
  elif lan == 'EN':
    ax[0].set_ylabel(' \n Power in MW \n ')
    ax[0].set_xlabel('Time')
    ax[1].set_xlabel('Time')
    #ax[0].set_title('1')
    #ax[1].set_title('2')
  
  y_max = max(y_max_pos)
  y_min = min(y_max_neg)

  y_max += max([abs(y_min), abs(y_max)])*.1
  y_min -= max([abs(y_min), abs(y_max)])*.1

  ax[0].set_xlim(time_min_1, time_max_1)
  ax[1].set_xlim(time_min_2, time_max_2)

  ax[0].set_ylim(y_min, y_max)
  ax[1].set_ylim(y_min, y_max)
  
  if save_fig_dir is not None:
     plt.savefig(save_fig_dir, format=image_format, bbox_inches='tight', dpi=dpi)


### with 2 plots ###
def plot_residualload_grid_issues_subplot_overall_eva(eva1, eva2, save_fig_dir=None):
  prop_cycle = plt.rcParams['axes.prop_cycle']
  c = prop_cycle.by_key()['color']

  if eva1['net_name_i'] == 7:
    trafo_s_n = 0.16
  elif eva1['net_name_i'] == 8:
    trafo_s_n = 0.25
  elif eva1['net_name_i'] == 9:
    trafo_s_n = 0.4
  elif eva1['net_name_i'] == 10:
    trafo_s_n = 0.4
  elif eva1['net_name_i'] == 11:
    trafo_s_n = 0.63
  else:
    trafo_s_n = 0

  # res load
  power_1 = eva1['power']*1
  power_2 = eva2['power']*1
  power = [power_1, power_2]
  storage_1 = -eva1['storage_power']*1
  storage_2 = -eva2['storage_power']*1
  storage = [storage_1, storage_2]
  curtailed_power_1 = eva1['curtailed_power']
  curtailed_power_2 = eva2['curtailed_power']
  curtailed = [curtailed_power_1, curtailed_power_2]

  time1 = power_1.index
  time2 = power_2.index

  day = 3
  time_min_1 = time1[(day-1)*24*60]
  time_max_1 = time1[(day)*24*60-1]

  time_min_2 = time2[(day-1)*24*60]
  time_max_2 = time2[(day)*24*60-1]

  time_min = [time_min_1, time_min_2]
  time_max = [time_max_1, time_max_2]

  y_max_pos = [0, 0]
  y_max_neg = [0, 0]

  for i in [0, 1]:
    storage_sum = storage[i].sum(axis=1)
    storage_charge = storage[i].copy()
    storage_charge[storage_charge > 0] = 0
    storage_charge = -storage_charge
    storage_charge = storage_charge.sum(axis=1)

    storage_discharge = storage[i].copy()
    storage_discharge[storage_discharge < 0] = 0
    storage_discharge = storage_discharge.sum(axis=1)
    if i == 0:
      y_max_pos[i] = (power[i].hp + power[i].load + power[i].ev + storage_charge + curtailed[i].load).loc[time_min_1:time_max_1].max()
      y_max_neg[i] = (-storage_discharge - power[i].pv - curtailed[i].pv).loc[time_min_1:time_max_1].min()
    else:
      y_max_pos[i] = (power[i].hp + power[i].load + power[i].ev + storage_charge + curtailed[i].load).loc[time_min_2:time_max_2].max()
      y_max_neg[i] = (-storage_discharge - power[i].pv - curtailed[i].pv).loc[time_min_2:time_max_2].min()

  # grid issues
  power_summer = eva1['power']
  storage_power_summer = eva1['storage_power']
  power_summer = power_summer.load+power_summer.hp+power_summer.ev-power_summer.pv+storage_power_summer.sum(axis=1)
  v_summer = eva1['v']
  ll_summer = eva1['ll']
  tl_summer = eva1['tl']

  power_winter = eva2['power']
  storage_power_winter = eva2['storage_power']
  power_winter = power_winter.load+power_winter.hp+power_winter.ev-power_winter.pv+storage_power_winter.sum(axis=1)
  v_winter = eva2['v']
  ll_winter = eva2['ll']
  tl_winter = eva2['tl']

  line_v_o_winter = power_winter*0 + 1.1
  line_v_u_winter = power_winter*0 + .9
  line_lt_winter = power_winter*0 + 1

  line_v_o_summer = power_summer*0 + 1.1
  line_v_u_summer = power_summer*0 + .9
  line_lt_summer = power_summer*0 + 1

  line_v_o = [line_v_o_summer, line_v_o_winter]
  line_v_u = [line_v_u_summer, line_v_u_winter]
  line_lt = [line_lt_summer, line_lt_winter]

  v_min = [v_summer.T.min().T, v_winter.T.min().T]
  v_max = [v_summer.T.max().T, v_winter.T.max().T]
  ll_max = [ll_summer.T.max().T, ll_winter.T.max().T]
  tl_max = [tl_summer.T.max().T, tl_winter.T.max().T]
  power_sum = [power_summer, power_winter]

  fig, (ax0, ax3, ax1, ax2) = plt.subplots(4, 2, figsize=(12,6), sharey = 'row', sharex = 'col', gridspec_kw={'wspace': .05, 'hspace': .05, 'height_ratios': [4, 1, 1, 1]}) #(8,10)
  for i in [0, 1]:
    #res
    storage_sum = storage[i].sum(axis=1)
    storage_charge = storage[i].copy()
    storage_charge[storage_charge > 0] = 0
    storage_charge = -storage_charge
    storage_charge = storage_charge.sum(axis=1)

    storage_discharge = storage[i].copy()
    storage_discharge[storage_discharge < 0] = 0
    storage_discharge = storage_discharge.sum(axis=1)

    ax0[i].fill_between(power[i].index,                     -storage_discharge,                     -storage_discharge - power[i].pv, alpha=0.7, color=c[0])
    ax0[i].fill_between(power[i].index,                         storage_charge,                         power[i].ev + storage_charge, alpha=0.7, color=c[1])
    ax0[i].fill_between(power[i].index,              power[i].ev + storage_charge,            power[i].load + power[i].ev + storage_charge, alpha=0.7, color=c[2])
    ax0[i].fill_between(power[i].index, power[i].load + power[i].ev + storage_charge, power[i].hp + power[i].load + power[i].ev + storage_charge, alpha=0.7, color=c[3])
    ax0[i].fill_between(power[i].index, 0 , storage_charge     , alpha=0.7, color=c[4])
    ax0[i].fill_between(power[i].index, 0 , -storage_discharge , alpha=0.7, color=c[4])
    # curtailed power
    ax0[i].fill_between(power[i].index, power[i].hp + power[i].load + power[i].ev + storage_charge, power[i].hp + power[i].load + power[i].ev + storage_charge + curtailed[i].load, alpha=0.2, color=c[7])
    ax0[i].fill_between(power[i].index,                     -storage_discharge - power[i].pv,                       -storage_discharge - power[i].pv - curtailed[i].pv, alpha=0.2, color=c[7])

    ax0[i].plot(power[i].index, -storage_discharge-power[i].pv, lw=.6)
    ax0[i].plot(power[i].index, storage_charge+power[i].ev, lw=.6)
    ax0[i].plot(power[i].index, storage_charge+power[i].load+power[i].ev, lw=.6)
    ax0[i].plot(power[i].index, storage_charge+power[i].hp+power[i].load+power[i].ev, lw=.6)
    ax0[i].plot(storage[i].index, storage_charge    , lw=.6)
    ax0[i].plot(storage[i].index, -storage_discharge, lw=.6)

    res_line, = ax0[i].plot(power[i].index, -(power[i].pv-power[i].hp-power[i].load-power[i].ev+storage_sum), color='black', lw=1, label='Residual load')

    ax0[i].set_xticks([k for k in power[i].index if ((k.hour == 0) or (k.hour == 6) or (k.hour == 12) or (k.hour == 18)) & (k.minute == 0)])
    ax0[i].set_xticklabels(['00:00', '06:00', '12:00', '18:00']*7 + ['00:00'])
    ax0[i].set(xlim=(power[i].index[0], power[i].index[-1]))
    if lan == 'DE':
      patch_list = [
         mpatches.Patch(color=c[0], alpha=0.7, label='Photovoltaik'),
         mpatches.Patch(color=c[1], alpha=0.7, label='E-Auto'),
         mpatches.Patch(color=c[2], alpha=0.7, label='Haushalt'),
         mpatches.Patch(color=c[3], alpha=0.7, label='Wärmepumpe'),
         mpatches.Patch(color=c[4], alpha=0.7, label='Speicher'),
         mpatches.Patch(color=c[7], alpha=0.2, label='Abregelung')
                 ]
    elif lan == 'EN':
      patch_list = [
         mpatches.Patch(color=c[0], alpha=0.7, label='Photovoltaic'),
         mpatches.Patch(color=c[1], alpha=0.7, label='E-vehicle'),
         mpatches.Patch(color=c[2], alpha=0.7, label='Household'),
         mpatches.Patch(color=c[3], alpha=0.7, label='Heatpump'),
         mpatches.Patch(color=c[4], alpha=0.7, label='Storage'),
         mpatches.Patch(color=c[7], alpha=0.2, label='Curtailment'),
         res_line
                 ]

    ax0[1].legend(handles=patch_list, loc='lower right', shadow=True, prop={'size': 7.5})

    if lan == 'DE':
      ax0[0].set_ylabel('Leistung in MW')
    elif lan == 'EN':
      ax0[0].set_ylabel('Power in MW')

    y_max = max(y_max_pos)
    y_min = min(y_max_neg)

    y_max += max([abs(y_min), abs(y_max)])*.1
    y_min -= max([abs(y_min), abs(y_max)])*.1

    ax0[0].set_xlim(time_min_1, time_max_1)
    ax0[1].set_xlim(time_min_2, time_max_2)

    ax0[0].set_ylim(y_min, y_max)
    ax0[1].set_ylim(y_min, y_max)

    #grid
    l1 = ax1[i].plot(v_min[i], 'r')[0]
    ax1[i].plot(line_v_u[i], '--k', lw=.5)
    l2 = ax1[i].plot(v_max[i], 'y')[0]
    l_limit = ax1[i].plot(line_v_o[i], '--k', lw=.5)[0]
    l3 = ax2[i].plot(tl_max[i]/100, 'g')[0]
    l4 = ax2[i].plot(ll_max[i]/100, 'b')[0]
    l_limit2 = ax2[i].plot(line_lt[i], '--k', lw=.5)[0]
    l5 = ax3[i].plot(power_sum[i], 'k')[0]
    ax3[i].plot(line_lt[i]*trafo_s_n, '--k', lw=.5)[0]
    l6 = ax3[i].plot(-line_lt[i]*trafo_s_n, '--k', lw=.5)[0]
    ax1[i].set_xticks([k for k in power_sum[i].index if ((k.hour == 0) or (k.hour == 6) or (k.hour == 12) or (k.hour == 18)) & (k.minute == 0)])
    ax1[i].set_xticklabels(['00:00', '06:00', '12:00', '18:00']*7 + ['00:00'])
    ax2[i].set_xticks([k for k in power_sum[i].index if ((k.hour == 0) or (k.hour == 6) or (k.hour == 12) or (k.hour == 18)) & (k.minute == 0)])
    ax2[i].set_xticklabels(['00:00', '06:00', '12:00', '18:00']*7 + ['00:00'])
    ax3[i].set_xticks([k for k in power_sum[i].index if ((k.hour == 0) or (k.hour == 6) or (k.hour == 12) or (k.hour == 18)) & (k.minute == 0)])
    ax3[i].set_xticklabels(['00:00', '06:00', '12:00', '18:00']*7 + ['00:00'])

    ax1[i].set(xlim=(time_min[i], time_max[i]), ylim=(.85, 1.15)) # voltage band
    ax2[i].set(xlim=(time_min[i], time_max[i]), ylim=(0, 1.1))    # line and trafo loading
    ax3[i].set(xlim=(time_min[i], time_max[i]), ylim=(-.3, .3))   # Res_load

    if lan == 'DE':
      ax1[1].legend(handles=[l2, l1, l_limit], labels=['Max', 'Min', 'Grenze'] ,loc="lower right", shadow=True, prop={'size': 7.5})
      ax2[1].legend(handles=[l4, l3, l_limit2], labels=['Leitung', 'Trafo', 'Grenze'] ,loc="lower right", shadow=True, prop={'size': 7.5})
      if trafo_s_n == 0:
        ax3[1].legend(handles=[l5], labels=['Residuallast'] ,loc="lower right", shadow=True, prop={'size': 7.5})
      else:
        ax3[1].legend(handles=[l5, l6], labels=['Residuallast', 'Trafogrenze'] ,loc="lower right", shadow=True, prop={'size': 7.5})
      ax2[0].set_xlabel('Uhrzeit')
      ax2[1].set_xlabel('Uhrzeit')
      ax1[0].set_ylabel('Spannung\nin p.u.\n')
      ax2[0].set_ylabel('Leitungs-\nund Trafo-\nbelastung in p.u.\n')
      ax3[0].set_ylabel('Leistung\nin MW')
    elif lan == 'EN':
      ax1[1].legend(handles=[l2, l1, l_limit], labels=['Max Voltage', 'Min Voltage', 'Voltage Limit'] ,loc="lower right", shadow=True, prop={'size': 7.5})
      ax2[1].legend(handles=[l4, l3, l_limit2], labels=['Max\nLineloading', 'Trafoloading', 'Limit'] ,loc="lower right", shadow=True, prop={'size': 7.5})
      if trafo_s_n == 0:
        ax3[1].legend(handles=[l5], labels=['Residual load'] ,loc="lower right", shadow=True, prop={'size': 7.5})
      else:
        ax3[1].legend(handles=[l5, l6], labels=['Residual load', 'Trafo limit'] ,loc="lower right", shadow=True, prop={'size': 7.5})
      ax2[0].set_xlabel('Time')
      ax2[1].set_xlabel('Time')
      ax1[0].set_ylabel('Voltage\nin p.u.')
      ax2[0].set_ylabel('Line- and Trafo-\nloading in p.u.')
      ax3[0].set_ylabel('Power in MW')

  if save_fig_dir is not None:
     plt.savefig(save_fig_dir, bbox_inches='tight', dpi=dpi) 


### with 3 plots ###
def plot_residualload_grid_issues_subplot_overall_eva_3_plots(eva1, eva2, eva3, save_fig_dir=None):
  prop_cycle = plt.rcParams['axes.prop_cycle']
  c = prop_cycle.by_key()['color']
  font_size_legend = 9
  framealpha_legend = 1
  shadow_legend = True
  x_pos_legend = .9 # default .9

  if eva1['net_name_i'] == 7:
    trafo_s_n = 0.16
  elif eva1['net_name_i'] == 8:
    trafo_s_n = 0.25
  elif eva1['net_name_i'] == 9:
    trafo_s_n = 0.4
  elif eva1['net_name_i'] == 10:
    trafo_s_n = 0.4
  elif eva1['net_name_i'] == 11:
    trafo_s_n = 0.63
  else:
    trafo_s_n = 0

  # res load
  power_1 = eva1['power']*1
  power_2 = eva2['power']*1
  power_3 = eva3['power']*1
  power = [power_1, power_2, power_3]
  storage_1 = -eva1['storage_power']*1
  storage_2 = -eva2['storage_power']*1
  storage_3 = -eva3['storage_power']*1
  storage = [storage_1, storage_2, storage_3]
  curtailed_power_1 = eva1['curtailed_power']
  curtailed_power_2 = eva2['curtailed_power']
  curtailed_power_3 = eva3['curtailed_power']
  curtailed = [curtailed_power_1, curtailed_power_2, curtailed_power_3]

  time1 = power_1.index
  time2 = power_2.index
  time3 = power_3.index

  day1 = 3
  day2 = 3
  time_min_1 = time1[(day1-1)*24*60]
  time_max_1 = time1[(day2)*24*60-1]

  time_min_2 = time2[(day1-1)*24*60]
  time_max_2 = time2[(day2)*24*60-1]

  time_min_3 = time3[(day1-1)*24*60]
  time_max_3 = time3[(day2)*24*60-1]

  time_min = [time_min_1, time_min_2, time_min_3]
  time_max = [time_max_1, time_max_2, time_max_3]

  y_max_pos = [0, 0, 0]
  y_max_neg = [0, 0, 0]

  for i in [0, 1, 2]:
    storage_sum = storage[i].sum(axis=1)
    storage_charge = storage[i].copy()
    storage_charge[storage_charge > 0] = 0
    storage_charge = -storage_charge
    storage_charge = storage_charge.sum(axis=1)

    storage_discharge = storage[i].copy()
    storage_discharge[storage_discharge < 0] = 0
    storage_discharge = storage_discharge.sum(axis=1)
    if i == 0:
      y_max_pos[i] = (power[i].hp + power[i].load + power[i].ev + storage_charge + curtailed[i].load).loc[time_min_1:time_max_1].max()
      y_max_neg[i] = (-storage_discharge - power[i].pv - curtailed[i].pv).loc[time_min_1:time_max_1].min()
    else:
      y_max_pos[i] = (power[i].hp + power[i].load + power[i].ev + storage_charge + curtailed[i].load).loc[time_min_2:time_max_2].max()
      y_max_neg[i] = (-storage_discharge - power[i].pv - curtailed[i].pv).loc[time_min_2:time_max_2].min()

  # grid issues
  power_plot1 = eva1['power']
  storage_power_plot1 = eva1['storage_power']
  power_plot1 = power_plot1.load+power_plot1.hp+power_plot1.ev-power_plot1.pv+storage_power_plot1.sum(axis=1)
  v_plot1 = eva1['v']
  ll_plot1 = eva1['ll']
  tl_plot1 = eva1['tl']

  power_plot2 = eva2['power']
  storage_power_plot2 = eva2['storage_power']
  power_plot2 = power_plot2.load+power_plot2.hp+power_plot2.ev-power_plot2.pv+storage_power_plot2.sum(axis=1)
  v_plot2 = eva2['v']
  ll_plot2 = eva2['ll']
  tl_plot2 = eva2['tl']

  power_plot3 = eva3['power']
  storage_power_plot3 = eva3['storage_power']
  power_plot3 = power_plot3.load+power_plot3.hp+power_plot3.ev-power_plot3.pv+storage_power_plot3.sum(axis=1)
  v_plot3 = eva3['v']
  ll_plot3 = eva3['ll']
  tl_plot3 = eva3['tl']

  line_v_o_plot1 = power_plot1*0 + 1.1
  line_v_u_plot1 = power_plot1*0 + .9
  line_lt_plot1 = power_plot1*0 + 1

  line_v_o_plot2 = power_plot2*0 + 1.1
  line_v_u_plot2 = power_plot2*0 + .9
  line_lt_plot2 = power_plot2*0 + 1

  line_v_o_plot3 = power_plot3*0 + 1.1
  line_v_u_plot3 = power_plot3*0 + .9
  line_lt_plot3 = power_plot3*0 + 1

  line_v_o = [line_v_o_plot1, line_v_o_plot2, line_v_o_plot3]
  line_v_u = [line_v_u_plot1, line_v_u_plot2, line_v_u_plot3]
  line_lt = [line_lt_plot1, line_lt_plot2, line_lt_plot3]

  v_min = [v_plot1.T.min().T, v_plot2.T.min().T, v_plot3.T.min().T]
  v_max = [v_plot1.T.max().T, v_plot2.T.max().T, v_plot3.T.max().T]
  ll_max = [ll_plot1.T.max().T, ll_plot2.T.max().T, ll_plot3.T.max().T]
  tl_max = [tl_plot1.T.max().T, tl_plot2.T.max().T, tl_plot3.T.max().T]
  power_sum = [power_plot1, power_plot2, power_plot3]

  # figsize=(10,10)
  fig, (ax0, ax3, ax1, ax2) = plt.subplots(4, 3, figsize=(10,6), sharey = 'row', sharex = 'col', gridspec_kw={'wspace': .05, 'hspace': .1, 'height_ratios': [4, 1, 1, 1]})
  for i in [0, 1, 2]:
    #res
    storage_sum = storage[i].sum(axis=1)
    storage_charge = storage[i].copy()
    storage_charge[storage_charge > 0] = 0
    storage_charge = -storage_charge
    storage_charge = storage_charge.sum(axis=1)

    storage_discharge = storage[i].copy()
    storage_discharge[storage_discharge < 0] = 0
    storage_discharge = storage_discharge.sum(axis=1)

    ax0[i].fill_between(power[i].index,                     -storage_discharge,                     -storage_discharge - power[i].pv, alpha=0.7, color=c[0])
    ax0[i].fill_between(power[i].index,                         storage_charge,                         power[i].ev + storage_charge, alpha=0.7, color=c[1])
    ax0[i].fill_between(power[i].index,              power[i].ev + storage_charge,            power[i].load + power[i].ev + storage_charge, alpha=0.7, color=c[2])
    ax0[i].fill_between(power[i].index, power[i].load + power[i].ev + storage_charge, power[i].hp + power[i].load + power[i].ev + storage_charge, alpha=0.7, color=c[3])
    ax0[i].fill_between(power[i].index, 0 , storage_charge     , alpha=0.7, color=c[4])
    ax0[i].fill_between(power[i].index, 0 , -storage_discharge , alpha=0.7, color=c[4])
    # curtailed power
    ax0[i].fill_between(power[i].index, power[i].hp + power[i].load + power[i].ev + storage_charge, power[i].hp + power[i].load + power[i].ev + storage_charge + curtailed[i].load, alpha=0.2, color=c[7])
    ax0[i].fill_between(power[i].index,                     -storage_discharge - power[i].pv,                       -storage_discharge - power[i].pv - curtailed[i].pv, alpha=0.2, color=c[7])

    ax0[i].plot(power[i].index, -storage_discharge-power[i].pv, lw=.6)
    ax0[i].plot(power[i].index, storage_charge+power[i].ev, lw=.6)
    ax0[i].plot(power[i].index, storage_charge+power[i].load+power[i].ev, lw=.6)
    ax0[i].plot(power[i].index, storage_charge+power[i].hp+power[i].load+power[i].ev, lw=.6)
    ax0[i].plot(storage[i].index, storage_charge    , lw=.6)
    ax0[i].plot(storage[i].index, -storage_discharge, lw=.6)

    res_line, = ax0[i].plot(power[i].index, -(power[i].pv-power[i].hp-power[i].load-power[i].ev+storage_sum), color='black', lw=1, label='Residual load')

    ax0[i].set_xticks([k for k in power[i].index if ((k.hour == 0) or (k.hour == 6) or (k.hour == 12) or (k.hour == 18)) & (k.minute == 0)])
    ax0[i].set_xticklabels(['00:00', '06:00', '12:00', '18:00']*7 + ['00:00'])
    ax0[i].set(xlim=(power[i].index[0], power[i].index[-1]))
    if lan == 'DE':
      patch_list = [
         mpatches.Patch(color=c[0], alpha=0.7, label='Photovoltaik'),
         mpatches.Patch(color=c[1], alpha=0.7, label='E-Auto'),
         mpatches.Patch(color=c[2], alpha=0.7, label='Haushalt'),
         mpatches.Patch(color=c[3], alpha=0.7, label='Wärmepumpe'),
         mpatches.Patch(color=c[4], alpha=0.7, label='Speicher'),
         mpatches.Patch(color=c[7], alpha=0.2, label='Abregelung')
                 ]

    elif lan == 'EN':
      patch_list = [
         mpatches.Patch(color=c[0], alpha=0.7, label='Photovoltaic'),
         mpatches.Patch(color=c[1], alpha=0.7, label='E-vehicle'),
         mpatches.Patch(color=c[2], alpha=0.7, label='Household'),
         mpatches.Patch(color=c[3], alpha=0.7, label='Heatpump'),
         mpatches.Patch(color=c[4], alpha=0.7, label='Storage'),
         mpatches.Patch(color=c[7], alpha=0.2, label='Curtailment'),
         res_line
                 ]

    ax0[2].legend(handles=patch_list, loc='lower left', shadow=shadow_legend, prop={'size': font_size_legend}, framealpha=framealpha_legend, bbox_to_anchor=(x_pos_legend, 0.455), bbox_transform=fig.transFigure)

    if lan == 'DE':
      ax0[0].set_ylabel('Leistung in MW')
    elif lan == 'EN':
      ax0[0].set_ylabel('Power in MW')
      ax0[0].set_title('Scenario 1')
      ax0[1].set_title('Scenario 4')
      ax0[2].set_title('Scenario 7')

    y_max = max(y_max_pos)
    y_min = min(y_max_neg)

    y_max += max([abs(y_min), abs(y_max)])*.1
    y_min -= max([abs(y_min), abs(y_max)])*.1

    y_max = 1.2
    y_min = -1.75

    ax0[0].set_xlim(time_min_1, time_max_1)
    ax0[1].set_xlim(time_min_2, time_max_2)
    ax0[2].set_xlim(time_min_3, time_max_3)

    ax0[0].set_ylim(y_min, y_max)
    ax0[1].set_ylim(y_min, y_max)
    ax0[2].set_ylim(y_min, y_max)

    #grid
    l1 = ax1[i].plot(v_min[i], 'r')[0]
    ax1[i].plot(line_v_u[i], '--k', lw=.5)
    l2 = ax1[i].plot(v_max[i], 'y')[0]
    l_limit = ax1[i].plot(line_v_o[i], '--k', lw=.5)[0]
    l3 = ax2[i].plot(tl_max[i]/100, 'g')[0]
    l4 = ax2[i].plot(ll_max[i]/100, 'b')[0]
    l_limit2 = ax2[i].plot(line_lt[i], '--k', lw=.5)[0]
    l5 = ax3[i].plot(power_sum[i], 'k')[0]
    ax3[i].plot(line_lt[i]*trafo_s_n, '--k', lw=.5)[0]
    l6 = ax3[i].plot(-line_lt[i]*trafo_s_n, '--k', lw=.5)[0]
    ax1[i].set_xticks([k for k in power_sum[i].index if ((k.hour == 0) or (k.hour == 6) or (k.hour == 12) or (k.hour == 18)) & (k.minute == 0)])
    ax1[i].set_xticklabels(['00:00', '06:00', '12:00', '18:00']*7 + ['00:00'])
    ax2[i].set_xticks([k for k in power_sum[i].index if ((k.hour == 0) or (k.hour == 6) or (k.hour == 12) or (k.hour == 18)) & (k.minute == 0)])
    ax2[i].set_xticklabels(['00:00', '06:00', '12:00', '18:00']*7 + ['00:00'])
    ax3[i].set_xticks([k for k in power_sum[i].index if ((k.hour == 0) or (k.hour == 6) or (k.hour == 12) or (k.hour == 18)) & (k.minute == 0)])
    ax3[i].set_xticklabels(['00:00', '06:00', '12:00', '18:00']*7 + ['00:00'])

    ax1[i].set(xlim=(time_min[i], time_max[i]), ylim=(.85, 1.15)) # voltage band
    ax2[i].set(xlim=(time_min[i], time_max[i]), ylim=(0, 1.1))    # line and trafo loading
    ax3[i].set(xlim=(time_min[i], time_max[i]), ylim=(-.3, .3))   # Res_load

    if lan == 'DE':
      ax1[2].legend(handles=[l2, l1, l_limit], labels=['Max', 'Min', 'Grenze'] ,loc="lower left", shadow=shadow_legend, prop={'size': font_size_legend}, framealpha=framealpha_legend, bbox_to_anchor=(x_pos_legend, 0.225), bbox_transform=fig.transFigure)
      ax2[2].legend(handles=[l4, l3, l_limit2], labels=['Leitung', 'Trafo', 'Grenze'] ,loc="lower left", shadow=shadow_legend, prop={'size': font_size_legend}, framealpha=framealpha_legend, bbox_to_anchor=(x_pos_legend, 0.111), bbox_transform=fig.transFigure)
      if trafo_s_n == 0:
        ax3[2].legend(handles=[l5], labels=['Residuallast'] ,loc="lower left", shadow=shadow_legend, prop={'size': font_size_legend}, framealpha=framealpha_legend, bbox_to_anchor=(x_pos_legend, 0.45), bbox_transform=fig.transFigure)
      else:
        ax3[2].legend(handles=[l5, l6], labels=['Residuallast', 'Trafogrenze'] ,loc="upper left", shadow=shadow_legend, prop={'size': font_size_legend}, framealpha=framealpha_legend, bbox_to_anchor=(x_pos_legend, 0.45), bbox_transform=fig.transFigure)
      ax2[0].set_xlabel('Uhrzeit')
      ax2[1].set_xlabel('Uhrzeit')
      ax2[2].set_xlabel('Uhrzeit')
      ax1[0].set_ylabel('Spannung\nin p.u.')
      ax2[0].set_ylabel('Leitungs-\nund Trafo-\nbelastung in p.u.')
      ax3[0].set_ylabel('Leistung\nin MW')
    elif lan == 'EN':
      ax1[2].legend(handles=[l2, l1, l_limit], labels=['Max Voltage', 'Min Voltage', 'Voltage Limit'] ,loc="lower left", shadow=shadow_legend, prop={'size': font_size_legend}, framealpha=framealpha_legend, bbox_to_anchor=(x_pos_legend, 0.22), bbox_transform=fig.transFigure) #0.225
      ax2[2].legend(handles=[l4, l3, l_limit2], labels=['Max\nLineloading', 'Trafoloading', 'Limit'] ,loc="lower left", shadow=shadow_legend, prop={'size': font_size_legend}, framealpha=framealpha_legend, bbox_to_anchor=(x_pos_legend, 0.09), bbox_transform=fig.transFigure) #0.111
      if trafo_s_n == 0:
        ax3[2].legend(handles=[l5], labels=['Residual load'] ,loc="lower left", shadow=shadow_legend, prop={'size': font_size_legend}, framealpha=framealpha_legend, bbox_to_anchor=(x_pos_legend, 0.45), bbox_transform=fig.transFigure)
      else:
        ax3[2].legend(handles=[l5, l6], labels=['Residual load', 'Trafo limit'] ,loc="lower left", shadow=shadow_legend, prop={'size': font_size_legend}, framealpha=framealpha_legend, bbox_to_anchor=(x_pos_legend, 0.34), bbox_transform=fig.transFigure)
      ax2[0].set_xlabel('Time')
      ax2[1].set_xlabel('Time')
      ax2[2].set_xlabel('Time')
      ax1[0].set_ylabel('Voltage\nin p.u.')
      #ax2[0].set_ylabel('Line- and Trafo-\nloading in p.u.')
      ax2[0].set_ylabel('Line- and\nTrafoloading\nin p.u.')
      ax3[0].set_ylabel('Power in MW')

  if save_fig_dir is not None:
     plt.savefig(save_fig_dir, bbox_inches='tight', dpi=dpi) 


### with 4 plots ###
def plot_residualload_grid_issues_subplot_overall_eva_4_plots(eva1, eva2, eva3, eva4, save_fig_dir=None):
  prop_cycle = plt.rcParams['axes.prop_cycle']
  c = prop_cycle.by_key()['color']
  font_size_legend = 9
  framealpha_legend = 1
  shadow_legend = True
  x_pos_legend = 1.005#.95 # default .9

  if eva1['net_name_i'] == 7:
    trafo_s_n = 0.16
  elif eva1['net_name_i'] == 8:
    trafo_s_n = 0.25
  elif eva1['net_name_i'] == 9:
    trafo_s_n = 0.4
  elif eva1['net_name_i'] == 10:
    trafo_s_n = 0.4
  elif eva1['net_name_i'] == 11:
    trafo_s_n = 0.63
  else:
    trafo_s_n = 0

  # res load
  power_1 = eva1['power']*1
  power_2 = eva2['power']*1
  power_3 = eva3['power']*1
  power_4 = eva4['power']*1
  power = [power_1, power_2, power_3, power_4]
  storage_1 = -eva1['storage_power']*1
  storage_2 = -eva2['storage_power']*1
  storage_3 = -eva3['storage_power']*1
  storage_4 = -eva4['storage_power']*1
  storage = [storage_1, storage_2, storage_3, storage_4]
  curtailed_power_1 = eva1['curtailed_power']
  curtailed_power_2 = eva2['curtailed_power']
  curtailed_power_3 = eva3['curtailed_power']
  curtailed_power_4 = eva4['curtailed_power']
  curtailed = [curtailed_power_1, curtailed_power_2, curtailed_power_3, curtailed_power_4]

  time1 = power_1.index
  time2 = power_2.index
  time3 = power_3.index
  time4 = power_4.index

  day1 = 3
  day2 = 3
  time_min_1 = time1[(day1-1)*24*60]
  time_max_1 = time1[(day2)*24*60-1]

  time_min_2 = time2[(day1-1)*24*60]
  time_max_2 = time2[(day2)*24*60-1]

  time_min_3 = time3[(day1-1)*24*60]
  time_max_3 = time3[(day2)*24*60-1]

  time_min_4 = time4[(day1-1)*24*60]
  time_max_4 = time4[(day2)*24*60-1]

  time_min = [time_min_1, time_min_2, time_min_3, time_min_4]
  time_max = [time_max_1, time_max_2, time_max_3, time_max_4]

  y_max_pos = [0, 0, 0, 0]
  y_max_neg = [0, 0, 0, 0]

  for i in [0, 1, 2, 3]:
    storage_sum = storage[i].sum(axis=1)
    storage_charge = storage[i].copy()
    storage_charge[storage_charge > 0] = 0
    storage_charge = -storage_charge
    storage_charge = storage_charge.sum(axis=1)

    storage_discharge = storage[i].copy()
    storage_discharge[storage_discharge < 0] = 0
    storage_discharge = storage_discharge.sum(axis=1)
    if i == 0:
      y_max_pos[i] = (power[i].hp + power[i].load + power[i].ev + storage_charge + curtailed[i].load).loc[time_min_1:time_max_1].max()
      y_max_neg[i] = (-storage_discharge - power[i].pv - curtailed[i].pv).loc[time_min_1:time_max_1].min()
    else:
      y_max_pos[i] = (power[i].hp + power[i].load + power[i].ev + storage_charge + curtailed[i].load).loc[time_min_2:time_max_2].max()
      y_max_neg[i] = (-storage_discharge - power[i].pv - curtailed[i].pv).loc[time_min_2:time_max_2].min()

  # grid issues
  power_plot1 = eva1['power']
  storage_power_plot1 = eva1['storage_power']
  power_plot1 = power_plot1.load+power_plot1.hp+power_plot1.ev-power_plot1.pv+storage_power_plot1.sum(axis=1)
  v_plot1 = eva1['v']
  ll_plot1 = eva1['ll']
  tl_plot1 = eva1['tl']

  power_plot2 = eva2['power']
  storage_power_plot2 = eva2['storage_power']
  power_plot2 = power_plot2.load+power_plot2.hp+power_plot2.ev-power_plot2.pv+storage_power_plot2.sum(axis=1)
  v_plot2 = eva2['v']
  ll_plot2 = eva2['ll']
  tl_plot2 = eva2['tl']

  power_plot3 = eva3['power']
  storage_power_plot3 = eva3['storage_power']
  power_plot3 = power_plot3.load+power_plot3.hp+power_plot3.ev-power_plot3.pv+storage_power_plot3.sum(axis=1)
  v_plot3 = eva3['v']
  ll_plot3 = eva3['ll']
  tl_plot3 = eva3['tl']

  power_plot4 = eva4['power']
  storage_power_plot4 = eva4['storage_power']
  power_plot4 = power_plot4.load+power_plot4.hp+power_plot4.ev-power_plot4.pv+storage_power_plot4.sum(axis=1)
  v_plot4 = eva4['v']
  ll_plot4 = eva4['ll']
  tl_plot4 = eva4['tl']

  line_v_o_plot1 = power_plot1*0 + 1.1
  line_v_u_plot1 = power_plot1*0 + .9
  line_lt_plot1 = power_plot1*0 + 1

  line_v_o_plot2 = power_plot2*0 + 1.1
  line_v_u_plot2 = power_plot2*0 + .9
  line_lt_plot2 = power_plot2*0 + 1

  line_v_o_plot3 = power_plot3*0 + 1.1
  line_v_u_plot3 = power_plot3*0 + .9
  line_lt_plot3 = power_plot3*0 + 1

  line_v_o_plot4 = power_plot4*0 + 1.1
  line_v_u_plot4 = power_plot4*0 + .9
  line_lt_plot4 = power_plot4*0 + 1

  line_v_o = [line_v_o_plot1, line_v_o_plot2, line_v_o_plot3, line_v_o_plot4]
  line_v_u = [line_v_u_plot1, line_v_u_plot2, line_v_u_plot3, line_v_u_plot4]
  line_lt = [line_lt_plot1, line_lt_plot2, line_lt_plot3, line_lt_plot4]

  v_min = [v_plot1.T.min().T, v_plot2.T.min().T, v_plot3.T.min().T, v_plot4.T.min().T]
  v_max = [v_plot1.T.max().T, v_plot2.T.max().T, v_plot3.T.max().T, v_plot4.T.max().T]
  ll_max = [ll_plot1.T.max().T, ll_plot2.T.max().T, ll_plot3.T.max().T, ll_plot4.T.max().T]
  tl_max = [tl_plot1.T.max().T, tl_plot2.T.max().T, tl_plot3.T.max().T, tl_plot4.T.max().T]
  power_sum = [power_plot1, power_plot2, power_plot3, power_plot4]

  # figsize=(10,10)
  fig, (ax0, ax3, ax1, ax2) = plt.subplots(4, 4, figsize=(12,6), sharey = 'row', sharex = 'col', gridspec_kw={'wspace': .05, 'hspace': .05, 'height_ratios': [4, 1, 1, 1]})
  for i in [0, 1, 2, 3]:
    #res
    storage_sum = storage[i].sum(axis=1)
    storage_charge = storage[i].copy()
    storage_charge[storage_charge > 0] = 0
    storage_charge = -storage_charge
    storage_charge = storage_charge.sum(axis=1)

    storage_discharge = storage[i].copy()
    storage_discharge[storage_discharge < 0] = 0
    storage_discharge = storage_discharge.sum(axis=1)

    ax0[i].fill_between(power[i].index,                     -storage_discharge,                     -storage_discharge - power[i].pv, alpha=0.7, color=c[0])
    ax0[i].fill_between(power[i].index,                         storage_charge,                         power[i].ev + storage_charge, alpha=0.7, color=c[1])
    ax0[i].fill_between(power[i].index,              power[i].ev + storage_charge,            power[i].load + power[i].ev + storage_charge, alpha=0.7, color=c[2])
    ax0[i].fill_between(power[i].index, power[i].load + power[i].ev + storage_charge, power[i].hp + power[i].load + power[i].ev + storage_charge, alpha=0.7, color=c[3])
    ax0[i].fill_between(power[i].index, 0 , storage_charge     , alpha=0.7, color=c[4])
    ax0[i].fill_between(power[i].index, 0 , -storage_discharge , alpha=0.7, color=c[4])
    # curtailed power
    ax0[i].fill_between(power[i].index, power[i].hp + power[i].load + power[i].ev + storage_charge, power[i].hp + power[i].load + power[i].ev + storage_charge + curtailed[i].load, alpha=0.2, color=c[7])
    ax0[i].fill_between(power[i].index,                     -storage_discharge - power[i].pv,                       -storage_discharge - power[i].pv - curtailed[i].pv, alpha=0.2, color=c[7])

    ax0[i].plot(power[i].index, -storage_discharge-power[i].pv, lw=.6)
    ax0[i].plot(power[i].index, storage_charge+power[i].ev, lw=.6)
    ax0[i].plot(power[i].index, storage_charge+power[i].load+power[i].ev, lw=.6)
    ax0[i].plot(power[i].index, storage_charge+power[i].hp+power[i].load+power[i].ev, lw=.6)
    ax0[i].plot(storage[i].index, storage_charge    , lw=.6)
    ax0[i].plot(storage[i].index, -storage_discharge, lw=.6)

    res_line, = ax0[i].plot(power[i].index, -(power[i].pv-power[i].hp-power[i].load-power[i].ev+storage_sum), color='black', lw=1, label='Residual load')

    ax0[i].set_xticks([k for k in power[i].index if ((k.hour == 0) or (k.hour == 6) or (k.hour == 12) or (k.hour == 18)) & (k.minute == 0)])
    ax0[i].set_xticklabels(['00:00', '06:00', '12:00', '18:00']*7 + ['00:00'])
    ax0[i].set(xlim=(power[i].index[0], power[i].index[-1]))
    if lan == 'DE':
      patch_list = [
         mpatches.Patch(color=c[0], alpha=0.7, label='Photovoltaik'),
         mpatches.Patch(color=c[1], alpha=0.7, label='E-Auto'),
         mpatches.Patch(color=c[2], alpha=0.7, label='Haushalt'),
         mpatches.Patch(color=c[3], alpha=0.7, label='Wärmepumpe'),
         mpatches.Patch(color=c[4], alpha=0.7, label='Speicher'),
         mpatches.Patch(color=c[7], alpha=0.2, label='Abregelung')
                 ]

    elif lan == 'EN':
      patch_list = [
         mpatches.Patch(color=c[0], alpha=0.7, label='Photovoltaic'),
         mpatches.Patch(color=c[1], alpha=0.7, label='E-vehicle'),
         mpatches.Patch(color=c[2], alpha=0.7, label='Household'),
         mpatches.Patch(color=c[3], alpha=0.7, label='Heatpump'),
         mpatches.Patch(color=c[4], alpha=0.7, label='Storage'),
         mpatches.Patch(color=c[7], alpha=0.2, label='Curtailment'),
         res_line
                 ]

    ax0[3].legend(handles=patch_list, loc='lower right', shadow=shadow_legend, prop={'size': font_size_legend}, framealpha=framealpha_legend, bbox_to_anchor=(x_pos_legend, 0.455), bbox_transform=fig.transFigure)

    if lan == 'DE':
      ax0[0].set_ylabel('Leistung in MW')
    elif lan == 'EN':
      ax0[0].set_ylabel('Power in MW')

    y_max = max(y_max_pos)
    y_min = min(y_max_neg)

    y_max += max([abs(y_min), abs(y_max)])*.1
    y_min -= max([abs(y_min), abs(y_max)])*.1

    ax0[0].set_xlim(time_min_1, time_max_1)
    ax0[1].set_xlim(time_min_2, time_max_2)
    ax0[2].set_xlim(time_min_3, time_max_3)
    ax0[3].set_xlim(time_min_4, time_max_4)

    ax0[0].set_ylim(y_min, y_max)
    ax0[1].set_ylim(y_min, y_max)
    ax0[2].set_ylim(y_min, y_max)
    ax0[3].set_ylim(y_min, y_max)

    #grid
    l1 = ax1[i].plot(v_min[i], 'r')[0]
    ax1[i].plot(line_v_u[i], '--k', lw=.5)
    l2 = ax1[i].plot(v_max[i], 'y')[0]
    l_limit = ax1[i].plot(line_v_o[i], '--k', lw=.5)[0]
    l3 = ax2[i].plot(tl_max[i]/100, 'g')[0]
    l4 = ax2[i].plot(ll_max[i]/100, 'b')[0]
    l_limit2 = ax2[i].plot(line_lt[i], '--k', lw=.5)[0]
    l5 = ax3[i].plot(power_sum[i], 'k')[0]
    ax3[i].plot(line_lt[i]*trafo_s_n, '--k', lw=.5)[0]
    l6 = ax3[i].plot(-line_lt[i]*trafo_s_n, '--k', lw=.5)[0]
    ax1[i].set_xticks([k for k in power_sum[i].index if ((k.hour == 0) or (k.hour == 6) or (k.hour == 12) or (k.hour == 18)) & (k.minute == 0)])
    ax1[i].set_xticklabels(['00:00', '06:00', '12:00', '18:00']*7 + ['00:00'])
    ax2[i].set_xticks([k for k in power_sum[i].index if ((k.hour == 0) or (k.hour == 6) or (k.hour == 12) or (k.hour == 18)) & (k.minute == 0)])
    ax2[i].set_xticklabels(['00:00', '06:00', '12:00', '18:00']*7 + ['00:00'])
    ax3[i].set_xticks([k for k in power_sum[i].index if ((k.hour == 0) or (k.hour == 6) or (k.hour == 12) or (k.hour == 18)) & (k.minute == 0)])
    ax3[i].set_xticklabels(['00:00', '06:00', '12:00', '18:00']*7 + ['00:00'])

    ax1[i].set(xlim=(time_min[i], time_max[i]), ylim=(.85, 1.15)) # voltage band
    ax2[i].set(xlim=(time_min[i], time_max[i]), ylim=(0, 1.1))    # line and trafo loading
    ax3[i].set(xlim=(time_min[i], time_max[i]), ylim=(-.3, .3))   # Res_load

    if lan == 'DE':
      ax1[3].legend(handles=[l2, l1, l_limit], labels=['Max', 'Min', 'Grenze'] ,loc="lower right", shadow=shadow_legend, prop={'size': font_size_legend}, framealpha=framealpha_legend, bbox_to_anchor=(x_pos_legend, 0.225), bbox_transform=fig.transFigure)
      ax2[3].legend(handles=[l4, l3, l_limit2], labels=['Leitung', 'Trafo', 'Grenze'] ,loc="lower right", shadow=shadow_legend, prop={'size': font_size_legend}, framealpha=framealpha_legend, bbox_to_anchor=(x_pos_legend, 0.111), bbox_transform=fig.transFigure)
      if trafo_s_n == 0:
        ax3[3].legend(handles=[l5], labels=['Residuallast'] ,loc="lower right", shadow=shadow_legend, prop={'size': font_size_legend}, framealpha=framealpha_legend, bbox_to_anchor=(x_pos_legend, 0.45), bbox_transform=fig.transFigure)
      else:
        ax3[3].legend(handles=[l5, l6], labels=['Residuallast', 'Trafogrenze'] ,loc="upper right", shadow=shadow_legend, prop={'size': font_size_legend}, framealpha=framealpha_legend, bbox_to_anchor=(x_pos_legend, 0.45), bbox_transform=fig.transFigure)
      ax2[0].set_xlabel('Uhrzeit')
      ax2[1].set_xlabel('Uhrzeit')
      ax2[2].set_xlabel('Uhrzeit')
      ax2[3].set_xlabel('Uhrzeit')
      ax1[0].set_ylabel('Spannung\nin p.u.')
      ax2[0].set_ylabel('Leitungs-\nund Trafo-\nbelastung in p.u.')
      ax3[0].set_ylabel('Leistung\nin MW')
    elif lan == 'EN':
      ax1[3].legend(handles=[l2, l1, l_limit], labels=['Max Voltage', 'Min Voltage', 'Voltage Limit'] ,loc="lower right", shadow=shadow_legend, prop={'size': font_size_legend}, framealpha=framealpha_legend, bbox_to_anchor=(x_pos_legend, 0.22), bbox_transform=fig.transFigure) #0.225
      ax2[3].legend(handles=[l4, l3, l_limit2], labels=['Max\nLineloading', 'Trafoloading', 'Limit'] ,loc="lower right", shadow=shadow_legend, prop={'size': font_size_legend}, framealpha=framealpha_legend, bbox_to_anchor=(x_pos_legend, 0.09), bbox_transform=fig.transFigure) #0.111
      if trafo_s_n == 0:
        ax3[3].legend(handles=[l5], labels=['Residual load'] ,loc="lower right", shadow=shadow_legend, prop={'size': font_size_legend}, framealpha=framealpha_legend, bbox_to_anchor=(x_pos_legend, 0.45), bbox_transform=fig.transFigure)
      else:
        ax3[3].legend(handles=[l5, l6], labels=['Residual load', 'Trafo limit'] ,loc="lower right", shadow=shadow_legend, prop={'size': font_size_legend}, framealpha=framealpha_legend, bbox_to_anchor=(x_pos_legend, 0.34), bbox_transform=fig.transFigure)
      ax2[0].set_xlabel('Time')
      ax2[1].set_xlabel('Time')
      ax2[2].set_xlabel('Time')
      ax2[3].set_xlabel('Time')
      ax1[0].set_ylabel('Voltage\nin p.u.')
      #ax2[0].set_ylabel('Line- and Trafo-\nloading in p.u.')
      ax2[0].set_ylabel('Line- and\nTrafoloading\nin p.u.')
      ax3[0].set_ylabel('Power in MW')

  if save_fig_dir is not None:
     plt.savefig(save_fig_dir, bbox_inches='tight', dpi=dpi) 




def plot_violin_overall_eva(df_eva_v, df_eva_l, save_fig_dir=None):
  print('Create Violin plots')
  plt.figure()
  ax = sns.violinplot(x="gridID", y="voltage", hue='timescope', data=df_eva_v, palette="muted", split=True, inner="quartile", cut=0)

  if save_fig_dir is not None:
     plt.savefig(save_fig_dir + 'violin_voltage.png', bbox_inches='tight', dpi=dpi)

  plt.figure()
  ax = sns.violinplot(x="gridID", y="lineloading", hue='timescope', data=df_eva_l, palette="muted", split=True, inner="quartile", cut=0)

  if save_fig_dir is not None:
     plt.savefig(save_fig_dir + 'violin_lineloading.png', bbox_inches='tight', dpi=dpi)

def plot_barplots_overall_eva(eva, n, save_fig_dir=None):
  print('Create Bar plots')
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
  #df_bar_1.drop(index='tl_over', level=1, inplace=True)
  df_bar_1 = df_bar_1.reset_index()

  df_bar_2 = df_bar.groupby(['gridID', 'type'])['value'].sum()/n
  #df_bar_2.drop(index='tl_over', level=1, inplace=True)
  df_bar_2 = df_bar_2.reset_index()


  plt.figure()
  ax = sns.barplot(x = 'scenario', y = 'value', hue = 'type', data = df_bar_1)
  ax.set(xlabel='Scenario', ylabel='Overload in min per unit')

  if save_fig_dir is not None:
     plt.savefig(save_fig_dir + 'bar_scenario.png', bbox_inches='tight', dpi=dpi)

  plt.figure()
  ax = sns.barplot(x = 'gridID', y = 'value', hue = 'type', data = df_bar_2)
  ax.set(xlabel='GridID', ylabel='Overload in min per unit')

  if save_fig_dir is not None:
     plt.savefig(save_fig_dir + 'bar_gridID.png', bbox_inches='tight', dpi=dpi)

  plt.figure()
  ax = sns.barplot(x = 'type', y = 'value', hue = 'scenario', data = df_bar_1)
  ax.set(xlabel='Overload type', ylabel='Overload in min per unit')

  if save_fig_dir is not None:
     plt.savefig(save_fig_dir + 'bar_issus.png', bbox_inches='tight', dpi=dpi)


def plot_heatmap_grid_issus(eva, net_name, columns_scenarios, x_ticklabels, n, save_fig_dir=None):
  #print('Create Heatmap plots grid issus')

  minutes_per_week = 7*24*60

  df_v_heatmap = pd.DataFrame(index=[net_name[7:12]], columns=columns_scenarios).fillna(0)
  df_l_heatmap = pd.DataFrame(index=[net_name[7:12]], columns=columns_scenarios).fillna(0)
  df_t_heatmap = pd.DataFrame(index=[net_name[7:12]], columns=columns_scenarios).fillna(0)
  v_events = pd.DataFrame(index=[net_name[7:12]], columns=columns_scenarios).fillna(0)
  l_events = pd.DataFrame(index=[net_name[7:12]], columns=columns_scenarios).fillna(0)
  t_events = pd.DataFrame(index=[net_name[7:12]], columns=columns_scenarios).fillna(0)

  for index in eva:
   if eva[index]['scenario'] in columns_scenarios:
    df_v_heatmap[eva[index]['scenario']].loc[eva[index]['net_name']] += (eva[index]['v_under'] + eva[index]['v_over'])/n
    df_l_heatmap[eva[index]['scenario']].loc[eva[index]['net_name']] += eva[index]['ll_over']/n
    df_t_heatmap[eva[index]['scenario']].loc[eva[index]['net_name']] += eva[index]['tl_over']/n
    v_events[eva[index]['scenario']].loc[eva[index]['net_name']] += len(eva[index]['v'].columns)/n
    l_events[eva[index]['scenario']].loc[eva[index]['net_name']] += len(eva[index]['ll'].columns)/n
    t_events[eva[index]['scenario']].loc[eva[index]['net_name']] += len(eva[index]['tl'].columns)/n

  #x_ticklabels = ['Conv', 'EV+HP', 'PV', 'PV+EV+HP']
  #y_ticklabels = ['Grid  \nRural 1', 'Grid  \nRural 2', 'Grid  \nRural 3', 'Grid    \nSuburb 1', 'Grid    \nSuburb 2']

  vmax_v = (df_v_heatmap/v_events/minutes_per_week*100).max().max()
  vmax_l = (df_l_heatmap/l_events/minutes_per_week*100).max().max()
  vmax_t = (df_t_heatmap/t_events/minutes_per_week*100).max().max()
  vmax = max([vmax_v, vmax_l, vmax_t])
  #if vmax_v < vmax_l:
  #  vmax = vmax_l
  #else:
  #  vmax = vmax_v
  vmin = 0
  
  plt.figure()
  ax = sns.heatmap(df_v_heatmap/v_events/minutes_per_week*100, vmax = vmax, vmin = vmin, cmap="rocket_r", annot=True, square=True)#, fmt=".0f")
  ax.set_xticklabels(x_ticklabels)
  ax.set_yticklabels(y_ticklabels)
  if lan == 'EN':
    ax.set(xlabel='Scenario', ylabel='Grid')
    ax.set_title('Voltage Violation in %')
  elif lan == 'DE':
    ax.set(xlabel='Szenario', ylabel='Netz')
    ax.set_title('Spannungsbandverletzung in %')

  #ax.set_title('Voltage Violation in Minutes per Week and Bus')

  if save_fig_dir is not None:
     plt.savefig(save_fig_dir + 'heatmap_voltage.png', bbox_inches='tight', dpi=dpi)

  #"YlOrBr"

  plt.figure()
  ax = sns.heatmap(df_l_heatmap/l_events/minutes_per_week*100, vmax = vmax, vmin = vmin, cmap="rocket_r", annot=True, square=True)#, fmt=".0f")
  ax.set_xticklabels(x_ticklabels)
  ax.set_yticklabels(y_ticklabels)
  if lan == 'EN':
    ax.set(xlabel='Scenario', ylabel='Grid')
    ax.set_title('Line Overloading in %')
  elif lan == 'DE':
    ax.set(xlabel='Szenario', ylabel='Netz')
    ax.set_title('Leitungsüberlastung in %')

  #ax.set_title('Line Overloading in Minutes per Week and Line')

  if save_fig_dir is not None:
     plt.savefig(save_fig_dir + 'heatmap_lineloading.png', bbox_inches='tight', dpi=dpi)

  plt.figure()
  ax = sns.heatmap(df_t_heatmap/t_events/minutes_per_week*100, vmax = vmax, vmin = vmin, cmap="rocket_r", annot=True, square=True)#, fmt=".0f")
  ax.set_xticklabels(x_ticklabels)
  ax.set_yticklabels(y_ticklabels)
  if lan == 'EN':
    ax.set(xlabel='Scenario', ylabel='Grid')
    ax.set_title('Transformer Overloading in %')
  elif lan == 'DE':
    ax.set(xlabel='Szenario', ylabel='Netz')
    ax.set_title('Trafoüberlastung in %')

  #ax.set_title('Line Overloading in Minutes per Week and Line')

  if save_fig_dir is not None:
     plt.savefig(save_fig_dir + 'heatmap_trafoloading.png', bbox_inches='tight', dpi=dpi)


##########################################################################################
##########################################################################################
##########################################################################################
##########################################################################################



def plot_heatmap_componentloading_mean_peak(eva, net_name, columns_scenarios, x_ticklabels, save_fig_dir=None):
  minutes_per_hour = 60
  without_v = True

  seasons = pd.DataFrame(index=[net_name[7:12]], columns=columns_scenarios).fillna(0)

  vu_mean = pd.DataFrame(index=[net_name[7:12]], columns=columns_scenarios).fillna(0)
  vo_mean = pd.DataFrame(index=[net_name[7:12]], columns=columns_scenarios).fillna(0)
  ll_mean = pd.DataFrame(index=[net_name[7:12]], columns=columns_scenarios).fillna(0)
  tl_mean = pd.DataFrame(index=[net_name[7:12]], columns=columns_scenarios).fillna(0)

  vu_peak = pd.DataFrame(index=[net_name[7:12]], columns=columns_scenarios).fillna(1)
  vo_peak = pd.DataFrame(index=[net_name[7:12]], columns=columns_scenarios).fillna(0)
  ll_peak = pd.DataFrame(index=[net_name[7:12]], columns=columns_scenarios).fillna(0)
  tl_peak = pd.DataFrame(index=[net_name[7:12]], columns=columns_scenarios).fillna(0)

  for index in eva:
    if eva[index]['scenario'] in columns_scenarios:

      seasons[eva[index]['scenario']].loc[eva[index]['net_name']] += 1 

      vu_mean[eva[index]['scenario']].loc[eva[index]['net_name']] += eva[index]['v'][eva[index]['v'] < 1.0].min(axis=1).mean()
      vo_mean[eva[index]['scenario']].loc[eva[index]['net_name']] += eva[index]['v'][eva[index]['v'] > 1.0].max(axis=1).mean()
      ll_mean[eva[index]['scenario']].loc[eva[index]['net_name']] += eva[index]['ll'].max(axis=1).mean()
      tl_mean[eva[index]['scenario']].loc[eva[index]['net_name']] += eva[index]['tl'].max(axis=1).mean()

      vu_peak[eva[index]['scenario']].loc[eva[index]['net_name']] = min([eva[index]['v'][eva[index]['v'] < 1.0].min(axis=1).min(), vu_peak[eva[index]['scenario']].loc[eva[index]['net_name']][0]])
      vo_peak[eva[index]['scenario']].loc[eva[index]['net_name']] = max([eva[index]['v'][eva[index]['v'] > 1.0].max(axis=1).max(), vo_peak[eva[index]['scenario']].loc[eva[index]['net_name']][0]])
      ll_peak[eva[index]['scenario']].loc[eva[index]['net_name']] = max([eva[index]['ll'].max(axis=1).max(), ll_peak[eva[index]['scenario']].loc[eva[index]['net_name']][0]])
      tl_peak[eva[index]['scenario']].loc[eva[index]['net_name']] = max([eva[index]['tl'].max(axis=1).max(), tl_peak[eva[index]['scenario']].loc[eva[index]['net_name']][0]])

  vu_mean = vu_mean/seasons
  vo_mean = vo_mean/seasons
  ll_mean = ll_mean/seasons
  tl_mean = tl_mean/seasons

  #'''
  print(vu_mean)
  print(vo_mean)
  print(ll_mean)
  print(tl_mean)
  print(vu_peak)
  print(vo_peak)
  print(ll_peak)
  print(tl_peak)
  #'''

  vmax = 1.04
  vmin = .97
  tlmax = 100.

  cmap = "rocket_r"
  cmap_dual = "twilight_shifted"#"seismic"

  # mean
  if without_v != True:
    fig, ax = plt.subplots(2, 2, figsize=(6,6), sharey = 'row', sharex = 'col', gridspec_kw={'wspace': .05, 'hspace': .2})
    sns.heatmap(ax=ax[0][0], data=vu_mean, vmax = vmax, vmin = vmin, cmap=cmap_dual, annot=True, square=False, cbar=False, fmt=".3f")
    sns.heatmap(ax=ax[0][1], data=vo_mean, vmax = vmax, vmin = vmin, cmap=cmap_dual, annot=True, square=False, cbar=False, fmt=".3f")
    sns.heatmap(ax=ax[0][0], data=ll_mean, vmax = tlmax, vmin = -100., cmap=cmap_dual, annot=True, square=False, cbar=False)#, fmt=".0f")
    sns.heatmap(ax=ax[1][1], data=tl_mean, vmax = tlmax, vmin = -100., cmap=cmap_dual, annot=True, square=False, cbar=False)#, fmt=".0f")
  elif without_v == True:
    fig, ax = plt.subplots(1, 2, figsize=(6,3), sharey = 'row', sharex = 'col', gridspec_kw={'wspace': .05, 'hspace': .2})
    sns.heatmap(ax=ax[0], data=ll_mean, vmax = tlmax, vmin = -100., cmap=cmap_dual, annot=True, square=False, cbar=False)#, fmt=".0f")
    sns.heatmap(ax=ax[1], data=tl_mean, vmax = tlmax, vmin = -100., cmap=cmap_dual, annot=True, square=False, cbar=False)#, fmt=".0f")

  if without_v != True:
   for x in [0, 1]:
    for y in [0, 1]:
      ax[x][y].set_xticklabels(x_ticklabels)
      ax[x][y].set_yticklabels(y_ticklabels)
  else:
   for x in [0, 1]:
      ax[x].set_xticklabels(x_ticklabels)
      ax[x].set_yticklabels(y_ticklabels)

  if without_v != True:
   if lan == 'EN':
    ax[0][0].set(xlabel='', ylabel='Grid')
    ax[0][0].set_title('Mean Undervoltage in p.u.')
    ax[0][1].set(xlabel='', ylabel='')
    ax[0][1].set_title('Mean Overvoltage in p.u.')
    ax[1][0].set(xlabel='Scenario', ylabel='Grid')
    ax[1][0].set_title('Mean Lineloading in %')
    ax[1][1].set(xlabel='Scenario', ylabel='')
    ax[1][1].set_title('Mean Trafoloading in %')
  else:
   if lan == 'EN':
    ax[0].set(xlabel='Scenario', ylabel='Grid')
    ax[0].set_title('Mean Lineloading in %')
    ax[1].set(xlabel='Scenario', ylabel='')
    ax[1].set_title('Mean Trafoloading in %')


  if lan == 'DE':
    print('German x- and y-label not implemented')

  if save_fig_dir is not None:
     plt.savefig(save_fig_dir + 'heatmap_subplot_component_loading_mean.png', bbox_inches='tight', dpi=dpi)

  # peak
  fig, ax = plt.subplots(2, 2, figsize=(6,6), sharey = 'row', sharex = 'col', gridspec_kw={'wspace': .05, 'hspace': .2})
  sns.heatmap(ax=ax[0][0], data=vu_peak, vmax = vmax, vmin = vmin, cmap=cmap_dual, annot=True, square=False, cbar=False, fmt=".3f")
  sns.heatmap(ax=ax[0][1], data=vo_peak, vmax = vmax, vmin = vmin, cmap=cmap_dual, annot=True, square=False, cbar=False, fmt=".3f")
  sns.heatmap(ax=ax[1][0], data=ll_peak, vmax = tlmax, vmin = -100., cmap=cmap_dual, annot=True, square=False, cbar=False)#, fmt=".0f")
  sns.heatmap(ax=ax[1][1], data=tl_peak, vmax = tlmax, vmin = -100., cmap=cmap_dual, annot=True, square=False, cbar=False)#, fmt=".0f")

  for x in [0, 1]:
    for y in [0, 1]:
      ax[x][y].set_xticklabels(x_ticklabels)
      ax[x][y].set_yticklabels(y_ticklabels)

  if lan == 'EN':
    ax[0][0].set(xlabel='', ylabel='Grid')
    ax[0][0].set_title('Peak Undervoltage in p.u.')
    ax[0][1].set(xlabel='', ylabel='')
    ax[0][1].set_title('Peak Overvoltage in p.u.')
    ax[1][0].set(xlabel='Scenario', ylabel='Grid')
    ax[1][0].set_title('Peak Lineloading in %')
    ax[1][1].set(xlabel='Scenario', ylabel='')
    ax[1][1].set_title('Peak Trafoloading in %')

  elif lan == 'DE':
    print('German x- and y-label not implemented')

  if save_fig_dir is not None:
     plt.savefig(save_fig_dir + 'heatmap_subplot_component_loading_peak.png', bbox_inches='tight', dpi=dpi)

  import matplotlib
  from scipy.stats import norm

  matplotlib.use("pgf")
  matplotlib.rcParams.update({
    "pgf.texsystem": "pdflatex",
    'font.family': 'serif',
    'text.usetex': True,
    'pgf.rcfonts': False,
  })

  plt.savefig('testheatmap.pgf', format='pgf')


def plot_heatmap_curtailed_power_per_season(eva, scenario, net_name, save_fig_dir=None):
  print('Create Heatmap plots curtailed power')
  #minutes_per_week = 7*24*60

  seasons = ['spring', 'summer', 'autumn', 'winter']

  pv_power = pd.DataFrame(index=[net_name[7:12]], columns=seasons).fillna(0)
  load_power = pd.DataFrame(index=[net_name[7:12]], columns=seasons).fillna(0)

  curtailed_power_pv = pd.DataFrame(index=[net_name[7:12]], columns=seasons).fillna(0) 
  curtailed_power_load = pd.DataFrame(index=[net_name[7:12]], columns=seasons).fillna(0)

  for index in eva:
    if str(eva[index]['scenario']) in str(scenario):
      curtailed_power_pv[eva[index]['time_scope_name']].loc[eva[index]['net_name']] += eva[index]['curtailed_power'].pv.sum()
      curtailed_power_load[eva[index]['time_scope_name']].loc[eva[index]['net_name']] += eva[index]['curtailed_power'].load.sum()
      pv_power[eva[index]['time_scope_name']].loc[eva[index]['net_name']] += eva[index]['power'].pv.sum()
      load_power[eva[index]['time_scope_name']].loc[eva[index]['net_name']] += eva[index]['power'].load.sum() + eva[index]['power'].hp.sum() + eva[index]['power'].ev.sum()

  curtailed_power_pv_per_cent = curtailed_power_pv/(pv_power+curtailed_power_pv)*100
  curtailed_power_load_per_cent = curtailed_power_load/(load_power+curtailed_power_load)*100

  # round
  curtailed_power_pv = (curtailed_power_pv/1000).round(3)
  curtailed_power_load = (curtailed_power_load/1000).round(3)
  curtailed_power_pv_per_cent = curtailed_power_pv_per_cent.round(2)
  curtailed_power_load_per_cent = curtailed_power_load_per_cent.round(2)

  vmax_pv = curtailed_power_pv.max().max()
  vmax_load = curtailed_power_load.max().max()
  vmax_season = np.array([vmax_pv, vmax_load]).max()

  vmax_pv_per_cent = curtailed_power_pv_per_cent.max().max()
  vmax_load_per_cent = curtailed_power_load_per_cent.max().max()
  vmax_pv_load_per_cent = np.array([vmax_pv_per_cent, vmax_load_per_cent]).max()

  vmin = 0

  #y_ticklabels = ['Land- \nnetz 1', 'Land- \nnetz 2', 'Land- \nnetz 3', 'Vorstadt-\nnetz 1  ', 'Vorstadt-\nnetz 2  ']
  if lan == 'EN':
    x_ticklabels = seasons
  elif lan == 'DE':
      x_ticklabels = ['Frühling', 'Sommer', 'Herbst', 'Winter']

  plt.figure(figsize=(5.5,4))
  ax = sns.heatmap(curtailed_power_pv_per_cent, vmax = vmax_pv_load_per_cent, vmin = vmin, cmap="rocket_r", annot=True, square=False)#, fmt=".0f")
  ax.set_xticklabels(x_ticklabels)
  ax.set_yticklabels(y_ticklabels)
  if lan == 'EN':
    ax.set(xlabel='Scenario', ylabel='Grid')
    ax.set_title('Curtailed pv energy in %')
  elif lan == 'DE':
    ax.set(xlabel='Szenario', ylabel='Netz')
    ax.set_title('Abgeregelte PV Energie in %')

  if save_fig_dir is not None:
     plt.savefig(save_fig_dir + '00b_' + str(scenario[0]) + '_heatmap_curtailed_power_pv_per_cent_season.png', bbox_inches='tight', dpi=dpi)
     #plt.savefig(save_fig_dir + '00b_heatmap_curtailed_power_pv_per_cent_' + str(eva[index]['time_scope_name']) + '.png', bbox_inches='tight')
  
  #"YlOrBr"

  plt.figure(figsize=(5.5,4))
  ax = sns.heatmap(curtailed_power_load_per_cent, vmax = vmax_pv_load_per_cent, vmin = vmin, cmap="rocket_r", annot=True, square=False)#, fmt=".0f")
  ax.set_xticklabels(x_ticklabels)
  ax.set_yticklabels(y_ticklabels)
  if lan == 'EN':
    ax.set(xlabel='Scenario', ylabel='Grid')
    ax.set_title('Curtailed load energy in %')
  elif lan == 'DE':
    ax.set(xlabel='Szenario', ylabel='Netz')
    ax.set_title('Abgeregelte Last in %')

  if save_fig_dir is not None:
     plt.savefig(save_fig_dir + '00b_' + str(scenario[0]) + '_heatmap_curtailed_power_load_per_cent_season.png', bbox_inches='tight', dpi=dpi)
     #plt.savefig(save_fig_dir + '00b_heatmap_curtailed_power_load_per_cent_' + str(eva[index]['time_scope_name']) + '.png', bbox_inches='tight')

  plt.figure()
  ax = sns.heatmap(curtailed_power_pv, vmax = vmax_season, vmin = vmin, cmap="rocket_r", annot=True, square=True)#, fmt=".0f")
  ax.set_xticklabels(x_ticklabels)
  ax.set_yticklabels(y_ticklabels)
  if lan == 'EN':
    ax.set(xlabel='Scenario', ylabel='Grid')
    ax.set_title('Curtailed pv energy in MWh')
  elif lan == 'DE':
    ax.set(xlabel='Szenario', ylabel='Netz')
    ax.set_title('Abgeregelte PV Energie in MWh')

  if save_fig_dir is not None:
     plt.savefig(save_fig_dir + '00c_' + str(scenario[0]) + '_heatmap_curtailed_power_pv_season.png', bbox_inches='tight', dpi=dpi)
     #plt.savefig(save_fig_dir + '00c_heatmap_curtailed_power_pv_' + str(eva[index]['time_scope_name']) + '.png', bbox_inches='tight')
  
  #"YlOrBr"

  plt.figure()
  ax = sns.heatmap(curtailed_power_load, vmax = vmax_season, vmin = vmin, cmap="rocket_r", annot=True, square=True)#, fmt=".0f")
  ax.set_xticklabels(x_ticklabels)
  ax.set_yticklabels(y_ticklabels)
  if lan == 'EN':
    ax.set(xlabel='Scenario', ylabel='Grid')
    ax.set_title('Curtailed load energy in MWh')
  elif lan == 'DE':
    ax.set(xlabel='Szenario', ylabel='Netz')
    ax.set_title('Abgeregelte Last in MWh')

  if save_fig_dir is not None:
     plt.savefig(save_fig_dir + '00c_' + str(scenario[0]) + '_heatmap_curtailed_power_load_season.png', bbox_inches='tight', dpi=dpi)
     #plt.savefig(save_fig_dir + '00c_heatmap_curtailed_power_load_' + str(eva[index]['time_scope_name']) + '.png', bbox_inches='tight')

  #plt.show()


def plot_heatmap_curtailed_power(eva, net_name, columns_scenarios, x_ticklabels, save_fig_dir=None):
  print('Create Heatmap plots curtailed power')
  #minutes_per_week = 7*24*60
  minutes_per_hour = 60

  pv_power = pd.DataFrame(index=[net_name[7:12]], columns=columns_scenarios).fillna(0)
  load_power = pd.DataFrame(index=[net_name[7:12]], columns=columns_scenarios).fillna(0)

  # Curtailed pv power
  curtailed_power_summer = pd.DataFrame(index=[net_name[7:12]], columns=columns_scenarios).fillna(0)
  curtailed_power_winter = pd.DataFrame(index=[net_name[7:12]], columns=columns_scenarios).fillna(0)

  curtailed_power_pv = pd.DataFrame(index=[net_name[7:12]], columns=columns_scenarios).fillna(0) 
  curtailed_power_load = pd.DataFrame(index=[net_name[7:12]], columns=columns_scenarios).fillna(0)

  for index in eva:
    if eva[index]['scenario'] in columns_scenarios:
      curtailed_power_pv[eva[index]['scenario']].loc[eva[index]['net_name']] += eva[index]['curtailed_power'].pv.sum() / minutes_per_hour
      curtailed_power_load[eva[index]['scenario']].loc[eva[index]['net_name']] += eva[index]['curtailed_power'].load.sum() / minutes_per_hour
      pv_power[eva[index]['scenario']].loc[eva[index]['net_name']] += eva[index]['power'].pv.sum() / minutes_per_hour
      load_power[eva[index]['scenario']].loc[eva[index]['net_name']] += (eva[index]['power'].load.sum() + eva[index]['power'].hp.sum() + eva[index]['power'].ev.sum()) / minutes_per_hour

  curtailed_power_pv_per_cent = curtailed_power_pv/(pv_power+curtailed_power_pv)*100
  curtailed_power_load_per_cent = curtailed_power_load/(load_power+curtailed_power_load)*100

  curtailed_power_pv_per_cent = curtailed_power_pv_per_cent.fillna(0)

  # round
  curtailed_power_pv = (curtailed_power_pv).round(3)
  curtailed_power_load = (curtailed_power_load).round(3)
  curtailed_power_pv_per_cent = curtailed_power_pv_per_cent.round(0)
  curtailed_power_load_per_cent = curtailed_power_load_per_cent.round(2)

  vmax_summer = curtailed_power_summer.max().max()
  vmax_winter = curtailed_power_winter.max().max()
  vmax_season = np.array([vmax_summer, vmax_winter]).max()

  vmax_pv = curtailed_power_pv.max().max()
  vmax_load = curtailed_power_load.max().max()
  vmax_pv_load = np.array([vmax_pv, vmax_load]).max()

  vmax_pv_per_cent = curtailed_power_pv_per_cent.max().max()
  vmax_load_per_cent = curtailed_power_load_per_cent.max().max()
  vmax_pv_load_per_cent = np.array([vmax_pv_per_cent, vmax_load_per_cent]).max()

  vmin = 0

  '''
  plt.figure(figsize=(fig_x, fig_y))
  ax = sns.heatmap(curtailed_power_pv_per_cent, vmax = vmax_pv_load_per_cent, vmin = vmin, cmap="rocket_r", annot=True, square=False)#, fmt=".0f")
  ax.set_xticklabels(x_ticklabels)
  ax.set_yticklabels(y_ticklabels)
  if lan == 'EN':
    ax.set(xlabel='Scenario', ylabel='Grid')
    ax.set_title('Curtailed pv energy in %')
  elif lan == 'DE':
    ax.set(xlabel='Szenario', ylabel='Netz')
    ax.set_title('Abgeregelte PV Energie in %')

  if save_fig_dir is not None:
     plt.savefig(save_fig_dir + '00b_heatmap_curtailed_power_pv_per_cent.png', bbox_inches='tight', dpi=dpi)
     #plt.savefig(save_fig_dir + '00b_heatmap_curtailed_power_pv_per_cent_' + str(eva[index]['time_scope_name']) + '.png', bbox_inches='tight')
  
  #"YlOrBr"

  plt.figure(figsize=(fig_x, fig_y))
  ax = sns.heatmap(curtailed_power_load_per_cent, vmax = vmax_pv_load_per_cent, vmin = vmin, cmap="rocket_r", annot=True, square=False)#, fmt=".0f")
  ax.set_xticklabels(x_ticklabels)
  ax.set_yticklabels(y_ticklabels)
  if lan == 'EN':
    ax.set(xlabel='Scenario', ylabel='Grid')
    ax.set_title('Curtailed load energy in %')
  elif lan == 'DE':
    ax.set(xlabel='Szenario', ylabel='Netz')
    ax.set_title('Abgeregelte Last in %')

  if save_fig_dir is not None:
     plt.savefig(save_fig_dir + '00b_heatmap_curtailed_power_load_per_cent.png', bbox_inches='tight', dpi=dpi)
     #plt.savefig(save_fig_dir + '00b_heatmap_curtailed_power_load_per_cent_' + str(eva[index]['time_scope_name']) + '.png', bbox_inches='tight')

  plt.figure(figsize=(fig_x, fig_y))
  ax = sns.heatmap(curtailed_power_pv, vmax = vmax_pv_load, vmin = vmin, cmap="rocket_r", annot=True, square=False)#, fmt=".0f")
  ax.set_xticklabels(x_ticklabels)
  ax.set_yticklabels(y_ticklabels)
  if lan == 'EN':
    ax.set(xlabel='Scenario', ylabel='Grid')
    ax.set_title('Curtailed pv energy in MWh')
  elif lan == 'DE':
    ax.set(xlabel='Szenario', ylabel='Netz')
    ax.set_title('Abgeregelte PV Energie in MWh')

  if save_fig_dir is not None:
     plt.savefig(save_fig_dir + '00c_heatmap_curtailed_power_pv.png', bbox_inches='tight', dpi=dpi)
     #plt.savefig(save_fig_dir + '00c_heatmap_curtailed_power_pv_' + str(eva[index]['time_scope_name']) + '.png', bbox_inches='tight')

  plt.figure(figsize=(fig_x, fig_y))
  ax = sns.heatmap(curtailed_power_load, vmax = vmax_pv_load, vmin = vmin, cmap="rocket_r", annot=True, square=False)#, fmt=".0f")
  ax.set_xticklabels(x_ticklabels)
  ax.set_yticklabels(y_ticklabels)
  if lan == 'EN':
    ax.set(xlabel='Scenario', ylabel='Grid')
    ax.set_title('Curtailed load energy in MWh')
  elif lan == 'DE':
    ax.set(xlabel='Szenario', ylabel='Netz')
    ax.set_title('Abgeregelte Last in MWh')

  if save_fig_dir is not None:
     plt.savefig(save_fig_dir + '00c_heatmap_curtailed_power_load.png', bbox_inches='tight', dpi=dpi)
     #plt.savefig(save_fig_dir + '00c_heatmap_curtailed_power_load_' + str(eva[index]['time_scope_name']) + '.png', bbox_inches='tight')
  '''

  fig, ax = plt.subplots(1, 2, figsize=(6,3), sharey = 'row', sharex = 'col', gridspec_kw={'wspace': .05})
  sns.heatmap(ax=ax[0], data=curtailed_power_load_per_cent, vmax = vmax_pv_load_per_cent, vmin = vmin, cmap="rocket_r", annot=True, square=False, cbar=False)#, fmt=".0f")
  sns.heatmap(ax=ax[1], data=curtailed_power_pv_per_cent, vmax = vmax_pv_load_per_cent, vmin = vmin, cmap="rocket_r", annot=True, square=False, cbar=False)#, fmt=".0f")
  ax[0].set_xticklabels(x_ticklabels)
  ax[0].set_yticklabels(y_ticklabels)
  ax[1].set_xticklabels(x_ticklabels)
  ax[1].set_yticklabels(y_ticklabels)
  if lan == 'EN':
    ax[0].set(xlabel='Scenario', ylabel='Grid')
    ax[1].set(xlabel='Scenario', ylabel='')
    ax[0].set_title('Curtailed load energy in %')
    ax[1].set_title('Curtailed PV energy in %')
  elif lan == 'DE':
    ax[0].set(xlabel='Szenario', ylabel='Netz')
    ax[1].set(xlabel='Szenario', ylabel='')
    ax[0].set_title('Abgeregelte Last in %')
    ax[1].set_title('Abgeregelte PV Energie in %')
    ax[0].set_xticklabels(ax[0].get_xticklabels(), rotation=90) 
    ax[1].set_xticklabels(ax[1].get_xticklabels(), rotation=90) 

  if save_fig_dir is not None:
     plt.savefig(save_fig_dir + '00d_subplot_heatmap_curtailed_power_load.png', bbox_inches='tight', dpi=dpi)
     #plt.savefig(save_fig_dir + '00c_heatmap_curtailed_power_load_' + str(eva[index]['time_scope_name']) + '.png', bbox_inches='tight')


def plot_heatmap_self_sufficiency(eva, net_name, columns_scenarios, x_ticklabels, n, save_fig_dir=None):
  print('Create Heatmap plots self sufficiency')
  df_pv_self = pd.DataFrame(index=[net_name[7:12]], columns=columns_scenarios).fillna(0)
  df_pv_total = pd.DataFrame(index=[net_name[7:12]], columns=columns_scenarios).fillna(0)
  df_load_self = pd.DataFrame(index=[net_name[7:12]], columns=columns_scenarios).fillna(0)
  df_load_total = pd.DataFrame(index=[net_name[7:12]], columns=columns_scenarios).fillna(0) 


  df_self_sufficiency = pd.DataFrame(index=[net_name[7:12]], columns=columns_scenarios).fillna(0)
  df_pv_consumption = pd.DataFrame(index=[net_name[7:12]], columns=columns_scenarios).fillna(0)

  for index in eva:
   if eva[index]['scenario'] in columns_scenarios:
     df_pv_total[eva[index]['scenario']].loc[eva[index]['net_name']]   += eva[index]['power'].pv.sum() + eva[index]['curtailed_power'].pv.sum()
     df_pv_self[eva[index]['scenario']].loc[eva[index]['net_name']]    += (eva[index]['power'].pv.sum() + eva[index]['curtailed_power'].pv.sum())*eva[index]['PVConsumption']
     df_load_total[eva[index]['scenario']].loc[eva[index]['net_name']] += eva[index]['power'].load.sum() + eva[index]['power'].hp.sum() + eva[index]['power'].ev.sum()
     df_load_self[eva[index]['scenario']].loc[eva[index]['net_name']]  += (eva[index]['power'].load.sum() + eva[index]['power'].hp.sum() + eva[index]['power'].ev.sum())*eva[index]['SelfSufficiancy']

  df_self_sufficiency = df_load_self/df_load_total
  df_pv_consumption = df_pv_self/df_pv_total

  df_self_sufficiency[df_self_sufficiency < .01] = 0
  df_pv_consumption = df_pv_consumption.fillna(0)

  # round
  df_self_sufficiency = (df_self_sufficiency).round(3)
  df_pv_consumption = (df_pv_consumption).round(3)

  vmax = 100
  vmin = 0
  
  cmap = sns.cubehelix_palette(start=2, rot=0, dark=.4, light=1, reverse=False, as_cmap=True)#"rocket_r"

  plt.figure(figsize=(fig_x, fig_y))
  ax = sns.heatmap(df_self_sufficiency, vmax = vmax, vmin = vmin, cmap=cmap, annot=True, square=False)#, fmt=".0f")
  ax.set_xticklabels(x_ticklabels)
  ax.set_yticklabels(y_ticklabels)
  if lan == 'EN':
    ax.set(xlabel='Scenario', ylabel='Grid')
    ax.set_title('Degree of self sufficiency in %')
  elif lan == 'DE':
    ax.set(xlabel='Szenario', ylabel='Netz')
    ax.set_title('Autarkiegrad in %')
  #ax.set_title('Voltage Violation in Minutes per Week and Bus')

  if save_fig_dir is not None:
     plt.savefig(save_fig_dir + 'heatmap_self_sufficiency.png', bbox_inches='tight', dpi=dpi)
     
  plt.figure(figsize=(fig_x, fig_y))
  ax = sns.heatmap(df_pv_consumption, vmax = vmax, vmin = vmin, cmap=cmap, annot=True, square=False)#, fmt=".0f")
  ax.set_xticklabels(x_ticklabels)
  ax.set_yticklabels(y_ticklabels)
  if lan == 'EN':
    ax.set(xlabel='Scenario', ylabel='Grid')
    ax.set_title('Self consumption rate in %')
  elif lan == 'DE':
    ax.set(xlabel='Szenario', ylabel='Netz')
    ax.set_title('Eigenverbrauch in %')

  if save_fig_dir is not None:
     plt.savefig(save_fig_dir + 'heatmap_pv_consumption.png', bbox_inches='tight', dpi=dpi)

  fig, ax = plt.subplots(1, 2, figsize=(6,3), sharey = 'row', sharex = 'col', gridspec_kw={'wspace': .05})
  sns.heatmap(ax=ax[0], data=df_self_sufficiency, vmax = vmax, vmin = vmin, cmap=cmap, annot=True, square=False, cbar=False)#, fmt=".0f")
  sns.heatmap(ax=ax[1], data=df_pv_consumption, vmax = vmax, vmin = vmin, cmap=cmap, annot=True, square=False, cbar=False)#, fmt=".0f")
  ax[0].set_xticklabels(x_ticklabels)
  ax[0].set_yticklabels(y_ticklabels)
  ax[1].set_xticklabels(x_ticklabels)
  ax[1].set_yticklabels(y_ticklabels)
  ax[0].set_xticklabels(ax[0].get_xticklabels(), rotation=90) 
  ax[1].set_xticklabels(ax[1].get_xticklabels(), rotation=90) 

  if lan == 'EN':
    ax[0].set(xlabel='Scenario', ylabel='Grid')
    ax[1].set(xlabel='Scenario', ylabel='')
    #ax[1].set_title('PV consumption in %')
    #ax[0].set_title('Self sufficiency in %')
    ax[1].set_title('Self-consumption rate in %')
    ax[0].set_title('Degree of self-sufficiency in %')
  elif lan == 'DE':
    ax[0].set(xlabel='Szenario', ylabel='Netz')
    ax[1].set(xlabel='Szenario', ylabel='')
    ax[1].set_title('Eigenverbrauch in %')
    ax[0].set_title('Autarkiegrad in %')

  if save_fig_dir is not None:
     plt.savefig(save_fig_dir + 'heatmap_subplot_pv_consumption_self_sufficiancy.png', bbox_inches='tight', dpi=dpi)
     #plt.savefig(save_fig_dir + '00c_heatmap_curtailed_power_load_' + str(eva[index]['time_scope_name']) + '.png', bbox_inches='tight')
  

def plot_heatmap_self_sufficiency_per_season(eva, scenario, net_name, save_fig_dir=None):
  seasons = ['spring', 'summer', 'autumn', 'winter']

  df_self_sufficiency = pd.DataFrame(index=[net_name[7:12]], columns=seasons).fillna(0)
  df_pv_consumption = pd.DataFrame(index=[net_name[7:12]], columns=seasons).fillna(0)

  for index in eva:
    if str(eva[index]['scenario']) in str(scenario):
      if eva[index]['time_scope_name'] in seasons:
        df_self_sufficiency[eva[index]['time_scope_name']].loc[eva[index]['net_name']] = eva[index]['SelfSufficiancy']
        df_pv_consumption[eva[index]['time_scope_name']].loc[eva[index]['net_name']] = eva[index]['PVConsumption']

  # round
  df_self_sufficiency = (df_self_sufficiency).round(3)
  df_pv_consumption = (df_pv_consumption).round(3)

  vmax = 100
 
  vmin = 0
  
  if lan == 'EN':
    x_ticklabels = seasons
  elif lan == 'DE':
      x_ticklabels = ['Frühling', 'Sommer', 'Herbst', 'Winter']

  plt.figure(figsize=(fig_x, fig_y))
  ax = sns.heatmap(df_self_sufficiency, vmax = vmax, vmin = vmin, cmap="rocket_r", annot=True, square=False, fmt=".0f")
  ax.set_xticklabels(x_ticklabels)
  ax.set_yticklabels(y_ticklabels)
  if lan == 'EN':
    ax.set(ylabel='Grid', xlabel='Season')
    ax.set_title('Self sufficiency in %')
  elif lan == 'DE':
    ax.set(xlabel='Jahreszeit', ylabel='Netz')
    ax.set_title('Autarkiegrad in %')

  if save_fig_dir is not None:
     plt.savefig(save_fig_dir + 'heatmap_self_sufficiency_per_season.png', bbox_inches='tight', dpi=dpi)
     
  plt.figure(figsize=(fig_x, fig_y))
  ax = sns.heatmap(df_pv_consumption, vmax = vmax, vmin = vmin, cmap="rocket_r", annot=True, square=False, fmt=".0f")
  ax.set(ylabel='Grid', xlabel='Season')
  ax.set_xticklabels(x_ticklabels)
  ax.set_yticklabels(y_ticklabels)
  if lan == 'EN':
    ax.set(ylabel='Grid', xlabel='Season')
    ax.set_title('PV consumption in %')
  elif lan == 'DE':
    ax.set(xlabel='Jahreszeit', ylabel='Netz')
    ax.set_title('Eigenverbrauch in %')

  if save_fig_dir is not None:
     plt.savefig(save_fig_dir + 'heatmap_pv_consumption_per_season.png', bbox_inches='tight', dpi=dpi)

def plot_grid_issus_over_power(eva, save_fig_dir=None):

  v_limit_over = 1.1
  v_limit_under = .9

  power = eva['power']
  power = power.load+power.hp+power.ev-power.pv
  v = eva['v']
  ll = eva['ll']
  tl = eva['tl']

  v_over = v[v>v_limit_over]
  v_under = v[v<v_limit_under]
  ll_over = ll[ll>100]
  tl_over = tl[tl>100]

  fig, ax = plt.subplots()
  line3 = ax.plot(power, ll_over/100, 'bo', label="ll")[0]
  line4 = ax.plot(power, tl_over/100, 'go', label="tl")[0]
  line1 = ax.plot(power, v_over, 'yo')[0]
  line2 = ax.plot(power, v_under, 'ro', label="vunder")[0]
  plt.legend(handles=[line1, line2, line3, line4], labels=['overvoltage', 'undervoltage', 'line overload', 'trafo overload'])
  plt.xlabel('Residual load in MW')
  plt.ylabel('voltage in pu / line overloading and trafo overloading')
  plt.grid(True)

  if save_fig_dir is not None:
     plt.savefig(save_fig_dir, bbox_inches='tight', dpi=dpi)

def plot_grid_issus_over_time(eva, save_fig_dir=None):
  power = eva['power']
  power = power.load+power.hp+power.ev-power.pv
  v = eva['v']
  ll = eva['ll']
  tl = eva['tl']

  power = shorted_data(power, 'H')
  v = shorted_data(v, 'H')
  ll = shorted_data(ll, 'H')
  tl = shorted_data(tl, 'H')

  line_v_o = power*0 + 1.1
  line_v_u = power*0 + .9
  line_lt = power*0 + 1

  v_min = v.T.min().T
  v_max = v.T.max().T
  ll_max = ll.T.max().T
  tl_max = tl.T.max().T

  fig, (ax3, ax1, ax2) = plt.subplots(3)
  fig.suptitle(' ')
  l1 = ax1.plot(v_min, 'r')[0]
  ax1.plot(line_v_u, '--k', lw=.5)
  l2 = ax1.plot(v_max, 'y')[0]
  l_limit =ax1.plot(line_v_o, '--k', lw=.5)[0]
  l3 = ax2.plot(tl_max/100, 'g')[0]
  l4 = ax2.plot(ll_max/100, 'b')[0]
  l_limit2 = ax2.plot(line_lt, '--k', lw=.5)[0]
  l5 = ax3.plot(power, 'k')[0]
  ax1.legend(handles=[l2, l1, l_limit], labels=['Max Voltage', 'Min Voltage', 'Voltage Limit'] ,loc="upper right")
  ax2.legend(handles=[l4, l3, l_limit2], labels=['Lineloading', 'Trafoloading', 'Overload Limit'] ,loc="upper right")
  ax3.legend(handles=[l5], labels=['Residual load'] ,loc="lower right")
  ax1.set_xlabel('Time')
  ax1.set_ylabel('Voltage\nin p.u.')
  ax2.set_ylabel('Line and Trafo\nLoading in p.u.')
  ax3.set_ylabel('Power\nin p.u.')
  ax1.set_xticks([i for i in power.index if (i.hour == 12) & (i.minute == 0)])
  ax1.set_xticklabels(['  Day 1', '  Day 2', '  Day 3', '  Day 4', '  Day 5', '  Day 6', '  Day 7'])
  ax2.set_xticks([i for i in power.index if (i.hour == 12) & (i.minute == 0)])
  ax2.set_xticklabels(['  Day 1', '  Day 2', '  Day 3', '  Day 4', '  Day 5', '  Day 6', '  Day 7'])
  ax3.set_xticks([i for i in power.index if (i.hour == 12) & (i.minute == 0)])
  ax3.set_xticklabels(['  Day 1', '  Day 2', '  Day 3', '  Day 4', '  Day 5', '  Day 6', '  Day 7'])
  ax1.set(xlim=(power.index[0], power.index[-1]), ylim=(.87, 1.13))
  ax2.set(xlim=(power.index[0], power.index[-1]), ylim=(0, 4.70))
  ax3.set(xlim=(power.index[0], power.index[-1]), ylim=(-2.1, 1))

  if save_fig_dir is not None:
     plt.savefig(save_fig_dir, bbox_inches='tight', dpi=dpi)

def plot_grid_issus_over_time_subplot(eva1, eva2, detailed=None, save_fig_dir=None):
  power_summer = eva1['power']
  storage_power_summer = eva1['storage_power']
  power_summer = power_summer.load+power_summer.hp+power_summer.ev-power_summer.pv+storage_power_summer.sum(axis=1)
  v_summer = eva1['v']
  ll_summer = eva1['ll']
  tl_summer = eva1['tl']

  power_winter = eva2['power']
  storage_power_winter = eva2['storage_power']
  power_winter = power_winter.load+power_winter.hp+power_winter.ev-power_winter.pv+storage_power_winter.sum(axis=1)
  v_winter = eva2['v']
  ll_winter = eva2['ll']
  tl_winter = eva2['tl']

  time1 = power_summer.index
  time2 = power_winter.index

  if detailed!=None:
    t_freq_new = '10T'
  else:
    t_freq_new = '30T'

  t_freq_new = '1T'

  power_summer = shorted_data(power_summer, t_freq_new)
  v_summer = shorted_data(v_summer, t_freq_new)
  ll_summer = shorted_data(ll_summer, t_freq_new)
  tl_summer = shorted_data(tl_summer, t_freq_new)

  power_winter = shorted_data(power_winter, t_freq_new)
  v_winter = shorted_data(v_winter, t_freq_new)
  ll_winter = shorted_data(ll_winter, t_freq_new)
  tl_winter = shorted_data(tl_winter, t_freq_new)

  line_v_o_winter = power_winter*0 + 1.1
  line_v_u_winter = power_winter*0 + .9
  line_lt_winter = power_winter*0 + 1

  line_v_o_summer = power_summer*0 + 1.1
  line_v_u_summer = power_summer*0 + .9
  line_lt_summer = power_summer*0 + 1

  line_v_o = [line_v_o_summer, line_v_o_winter]
  line_v_u = [line_v_u_summer, line_v_u_winter]
  line_lt = [line_lt_summer, line_lt_winter]

  v_min = [v_summer.T.min().T, v_winter.T.min().T]
  v_max = [v_summer.T.max().T, v_winter.T.max().T]
  ll_max = [ll_summer.T.max().T, ll_winter.T.max().T]
  tl_max = [tl_summer.T.max().T, tl_winter.T.max().T]
  power = [power_summer, power_winter]

  fig, ax = plt.subplots(3, 2, figsize=(8,4), sharey = 'row', sharex = 'col', gridspec_kw={'wspace': .05})
  ax1 = ax[1] # Voltage
  ax2 = ax[2] # Line and Trafo
  ax3 = ax[0] # Residual load
  for i in [0, 1]:
    l1 = ax1[i].plot(v_min[i], 'r')[0]
    ax1[i].plot(line_v_u[i], '--k', lw=.5)
    l2 = ax1[i].plot(v_max[i], 'y')[0]
    l_limit = ax1[i].plot(line_v_o[i], '--k', lw=.5)[0]
    l3 = ax2[i].plot(tl_max[i]/100, 'g')[0]
    l4 = ax2[i].plot(ll_max[i]/100, 'b')[0]
    l_limit2 = ax2[i].plot(line_lt[i], '--k', lw=.5)[0]
    l5 = ax3[i].plot(power[i], 'k')[0]
    #ax1[i].legend(handles=[l2, l1, l_limit], labels=['Max Voltage', 'Min Voltage', 'Voltage Limit'] ,loc="upper right")
    #ax2[i].legend(handles=[l4, l3, l_limit2], labels=['Line Overload', 'Trafo Overload', 'Overload Limit'] ,loc="upper right")
    #ax3[i].legend(handles=[l5], labels=['Residual load'] ,loc="lower right")
    #ax1[i].set_xticks([k for k in power[i].index if (k.hour == 12) & (k.minute == 0)])
    #ax1[i].set_xticklabels(['  Day 1', '  Day 2', '  Day 3', '  Day 4', '  Day 5', '  Day 6', '  Day 7'])
    #ax2[i].set_xticks([k for k in power[i].index if (k.hour == 12) & (k.minute == 0)])
    #ax2[i].set_xticklabels(['  Day 1', '  Day 2', '  Day 3', '  Day 4', '  Day 5', '  Day 6', '  Day 7'])
    #ax3[i].set_xticks([k for k in power[i].index if (k.hour == 12) & (k.minute == 0)])
    #ax3[i].set_xticklabels(['  Day 1', '  Day 2', '  Day 3', '  Day 4', '  Day 5', '  Day 6', '  Day 7'])
    ax1[i].set_xticks([k for k in power[i].index if ((k.hour == 0) or (k.hour == 6) or (k.hour == 12) or (k.hour == 18)) & (k.minute == 0)])
    ax1[i].set_xticklabels(['00:00', '06:00', '12:00', '18:00']*7 + ['00:00'])
    ax2[i].set_xticks([k for k in power[i].index if ((k.hour == 0) or (k.hour == 6) or (k.hour == 12) or (k.hour == 18)) & (k.minute == 0)])
    ax2[i].set_xticklabels(['00:00', '06:00', '12:00', '18:00']*7 + ['00:00'])
    ax3[i].set_xticks([k for k in power[i].index if ((k.hour == 0) or (k.hour == 6) or (k.hour == 12) or (k.hour == 18)) & (k.minute == 0)])
    ax3[i].set_xticklabels(['00:00', '06:00', '12:00', '18:00']*7 + ['00:00'])

    if detailed == None:
      ax1[i].set(xlim=(power[i].index[0], power[i].index[-1]), ylim=(.85, 1.15))
      ax2[i].set(xlim=(power[i].index[0], power[i].index[-1]), ylim=(0, 1.1))
      ax3[i].set(xlim=(power[i].index[0], power[i].index[-1]), ylim=(-.3, .3))

      ax1[1].legend(handles=[l2, l1, l_limit], labels=['Max Voltage', 'Min Voltage', 'Voltage Limit'] ,loc="upper right", shadow=True)
      ax2[1].legend(handles=[l4, l3, l_limit2], labels=['Lineloading', 'Trafoloading', 'Overload Limit'] ,loc="upper right", shadow=True)
      ax3[1].legend(handles=[l5], labels=['Residual load'] ,loc="lower right", shadow=True)

    else:
      day = 3
      time_min_winter = time2[(day-1)*24*60]
      time_max_winter = time2[(day)*24*60-1]

      time_min_summer = time1[(day-1)*24*60]
      time_max_summer = time1[(day)*24*60-1]

      time_min = [time_min_summer, time_min_winter]
      time_max = [time_max_summer, time_max_winter]

      ax1[i].set(xlim=(time_min[i], time_max[i]), ylim=(.85, 1.15)) # voltage band
      ax2[i].set(xlim=(time_min[i], time_max[i]), ylim=(0, 1.1))    # line and trafo loading
      ax3[i].set(xlim=(time_min[i], time_max[i]), ylim=(-.3, .3))   # Res_load

      if save_fig_dir is not None:
        save_fig_dir = save_fig_dir[:-4]+'_detailed'+save_fig_dir[-4:]

    if lan == 'DE':
      ax1[1].legend(handles=[l2, l1, l_limit], labels=['Max', 'Min', 'Grenze'] ,loc="lower left", shadow=True, prop={'size': 7.5})
      ax2[1].legend(handles=[l4, l3, l_limit2], labels=['Leitung', 'Trafo', 'Grenze'] ,loc="lower left", shadow=True, prop={'size': 7.5})
      ax3[1].legend(handles=[l5], labels=['Residuallast'] ,loc="lower left", shadow=True, prop={'size': 7.5})
      ax2[0].set_xlabel('Uhrzeit')
      ax2[1].set_xlabel('Uhrzeit')
      ax1[0].set_ylabel('Spannung\nin p.u.')
      ax2[0].set_ylabel('Leitungs-\nund Trafo-\nbelastung in p.u.')
      ax3[0].set_ylabel('Leistung\nin MW')
    elif lan == 'EN':
      ax1[1].legend(handles=[l2, l1, l_limit], labels=['Max Voltage', 'Min Voltage', 'Voltage Limit'] ,loc="lower right", shadow=True, prop={'size': 7.5})
      ax2[1].legend(handles=[l4, l3, l_limit2], labels=['Max Lineloading', 'Trafoloading', 'Overload Limit'] ,loc="lower right", shadow=True, prop={'size': 7.5})
      ax3[1].legend(handles=[l5], labels=['Residual load'] ,loc="lower right", shadow=True, prop={'size': 7.5})
      ax2[0].set_xlabel('Time')
      ax2[1].set_xlabel('Time')
      ax1[0].set_ylabel('Voltage\nin p.u.')
      ax2[0].set_ylabel('Line-\nand Trafo-\nloading in p.u.')
      ax3[0].set_ylabel('Power\nin MW')


  '''
  ax1[1].legend(handles=[l2, l1, l_limit], labels=['Max Voltage', 'Min Voltage', 'Voltage Limit'] ,loc="upper right", shadow=True)
  ax2[1].legend(handles=[l4, l3, l_limit2], labels=['Lineloading', 'Trafoloading', 'Overload Limit'] ,loc="upper right", shadow=True)
  ax3[1].legend(handles=[l5], labels=['Residual load'] ,loc="lower right", shadow=True)
  '''

  if save_fig_dir is not None:
     plt.savefig(save_fig_dir, bbox_inches='tight', dpi=dpi)

def plot_hist_grid_issus(eva, save_fig_dir=None):
  power = eva['power']
  power = power.load+power.hp+power.ev-power.pv
  v = eva['v']
  ll = eva['ll']
  tl = eva['tl']

  fig, (ax1, ax2, ax3) = plt.subplots(3)
  fig.suptitle('Vertically stacked subplots')
  h1 = ax1.hist(v.stack().values, bins=100, density=True,
         stacked=True,
         cumulative=False
         )[0]
  h4 = ax2.hist(ll.stack().values, bins=100, density=True,
         stacked=True,
         cumulative=False
         )[0]
  h3 = ax3.hist(tl, bins=100, density=True,
         stacked=True,
         cumulative=False
         )[0]
  #ax1.legend(handles=[h1], labels=['Voltage'])
  #ax2.legend(handles=[h4, h3], labels=['Line Overload', 'Trafo Overload'])
  plt.show()

def plot_hist_grid_issus_voltage(eva1, eva2, save_fig_dir=None):
  v1 = eva1['v']
  v2 = eva2['v']

  fig, (ax1) = plt.subplots(1)
  fig.suptitle(' ')
  h1 = ax1.hist(v1.stack().values, bins=100, density=True,
         stacked=True,
         cumulative=False,
         alpha=0.5,
         label=str(eva1['time_scope_name'])
         )[0]
  h2 = ax1.hist(v2.stack().values, bins=100, density=True,
         stacked=True,
         cumulative=False,
         alpha=0.5,
         label=str(eva2['time_scope_name'])
         )[0]
  plt.xlabel('Voltage in p.u.')
  plt.ylabel('Rate in Minutes per Bus')
  legend = ax1.legend(shadow=True)

  if save_fig_dir is not None:
     plt.savefig(save_fig_dir, bbox_inches='tight', dpi=dpi)




# together with plot_curtail_power()
# together with plot_curtail_power()
def plot_clustered_stacked(dfall, labels1=None, labels2=None, title=" ", ylabel= ' ', H=".", **kwargs):
    """Given a list of dataframes, with identical columns and index, create a clustered stacked bar plot. 
labels is a list of the names of the dataframe, used for the legend
title is a string for the title of the plot
H is the hatch used for identification of the different dataframe"""

    n_df = len(dfall)
    n_col = len(dfall[0].columns) 
    n_ind = len(dfall[0].index)
    plt.figure(figsize=(14, 6)) 
    axe = plt.subplot(111)
    #color_map = plt.cm.Spectral_r

    for df in dfall : # for each data frame
        axe = df.plot(kind="bar",
                      linewidth=0,
                      stacked=True,
                      ax=axe,
                      legend=False,
                      grid=False,
                      cmap='summer',
                      **kwargs)  # make bar plots
    
    h,l = axe.get_legend_handles_labels() # get the handles we want to modify
    for i in range(0, n_df * n_col, n_col): # len(h) = n_col * n_df
        for j, pa in enumerate(h[i:i+n_col]):
            for rect in pa.patches: # for each index
                if n_df == 4:
                  rect.set_x(rect.get_x() + 1 / float(n_df + 1) * i / float(n_col) - .5 / float(n_df + 1))
                else:
                  rect.set_x(rect.get_x() + 1 / float(n_df + 1) * i / float(n_col))
                rect.set_hatch(H* int(2*i / n_col))    
                rect.set_width(1 / float(n_df + 1))
                rect.set_alpha(.9)
                rect.set_aa(True)
                #axe.set_xticks([0, 1, 2, 3, 4])
                axe.set_xticks((np.arange(0, 2 * n_ind, 2) + .5 / float(n_df + 1)) / 2.)
    axe.set_xticklabels(df.index, rotation = 0)
    axe.set_title(title)

    # Add invisible data to add another legend
    n=[]        
    for i in range(n_df):
        n.append(axe.bar(0, 0, color="lightgrey", hatch=H * 2*i))
    
    if labels1 is not None:
        l1 = axe.legend(h[:n_col], labels1, loc=[.01, .82])#(h[:n_col], l[:n_col], loc=[1.01, 0.5])
    if labels2 is not None:
        l2 = plt.legend(n, labels2, loc=[.01, .8-n_df/20]) 
    axe.add_artist(l1)
    axe.set_xlabel('Grid')
    axe.set_ylabel(ylabel)
    axe.set_xticklabels(df.index)#['rural 1', 'rural 2', 'rural 3', 'suburban 1', 'suburban 2'])
    axe.set_ylim([0, 130])
   # axe.bar_label(dfall[0].columns, label_type = 'center') # Tabea
    return axe

def calculate_power_df(eva, scenario, seasons):
  df = pd.DataFrame(columns=['gridID', 'time_scope', 'curtailed_power_pv', 'feed-in_power_pv', 'self-consumed_power_pv', 'curtailed_power_load', 'grid_obtained_power_load', 'self-consumed_power_load'], index=range(5*len(seasons)))
  
  scale_factor_energy = 1/60 # kWmin -> kWh

  i = 0
  for index in eva:
    if eva[index]['scenario'] == scenario:
      df['gridID'].iloc[i] = eva[index]['net_name']
      df['time_scope'].iloc[i] = eva[index]['time_scope_name']
      curtailed_power = eva[index]['curtailed_power'].sum()
      df['feed-in_power_pv'].iloc[i] = eva[index]['power']['pv'].sum()*(100-eva[index]['PVConsumption'])/100*scale_factor_energy
      df['self-consumed_power_pv'].iloc[i] = eva[index]['power']['pv'].sum()*(eva[index]['PVConsumption'])/100*scale_factor_energy
      df['curtailed_power_pv'].iloc[i] = curtailed_power['pv']*scale_factor_energy
      df['grid_obtained_power_load'].iloc[i] = (eva[index]['power']['load'].sum() 
                                              +eva[index]['power']['hp'].sum() 
                                              +eva[index]['power']['ev'].sum()
                                              )*(100-eva[index]['SelfSufficiancy'])/100*scale_factor_energy
      df['self-consumed_power_load'].iloc[i] = (eva[index]['power']['load'].sum() 
                                              +eva[index]['power']['hp'].sum() 
                                              +eva[index]['power']['ev'].sum()
                                              )*(eva[index]['SelfSufficiancy'])/100*scale_factor_energy
      df['curtailed_power_load'].iloc[i] = curtailed_power['load']*scale_factor_energy  
      i += 1
      
  df_summer = df[df['time_scope'] == 'summer']
  df_winter = df[df['time_scope'] == 'winter']
  df_spring = df[df['time_scope'] == 'spring']
  df_autumn = df[df['time_scope'] == 'autumn']

  df_summer = df_summer.set_index('gridID')
  df_winter = df_winter.set_index('gridID')
  df_spring = df_spring.set_index('gridID')
  df_autumn = df_autumn.set_index('gridID')


  df_summer = df_summer.drop('time_scope', axis=1)
  df_winter = df_winter.drop('time_scope', axis=1)
  df_spring = df_spring.drop('time_scope', axis=1)
  df_autumn = df_autumn.drop('time_scope', axis=1)

  df_summer_pv = df_summer
  df_winter_pv = df_winter
  df_summer_load = df_summer
  df_winter_load = df_winter
  df_spring_pv = df_spring
  df_autumn_pv = df_autumn
  df_spring_load = df_spring
  df_autumn_load = df_autumn


  df_summer_pv = df_summer_pv.drop('curtailed_power_load', axis=1)
  df_summer_pv = df_summer_pv.drop('grid_obtained_power_load', axis=1)
  df_summer_pv = df_summer_pv.drop('self-consumed_power_load', axis=1)

  df_winter_pv = df_winter_pv.drop('curtailed_power_load', axis=1)
  df_winter_pv = df_winter_pv.drop('grid_obtained_power_load', axis=1)
  df_winter_pv = df_winter_pv.drop('self-consumed_power_load', axis=1)

  df_spring_pv = df_spring_pv.drop('curtailed_power_load', axis=1)
  df_spring_pv = df_spring_pv.drop('grid_obtained_power_load', axis=1)
  df_spring_pv = df_spring_pv.drop('self-consumed_power_load', axis=1)

  df_autumn_pv = df_autumn_pv.drop('curtailed_power_load', axis=1)
  df_autumn_pv = df_autumn_pv.drop('grid_obtained_power_load', axis=1)
  df_autumn_pv = df_autumn_pv.drop('self-consumed_power_load', axis=1)

  df_summer_load = df_summer_load.drop('curtailed_power_pv', axis=1)
  df_summer_load = df_summer_load.drop('feed-in_power_pv', axis=1)
  df_summer_load = df_summer_load.drop('self-consumed_power_pv', axis=1)

  df_winter_load = df_winter_load.drop('curtailed_power_pv', axis=1)
  df_winter_load = df_winter_load.drop('feed-in_power_pv', axis=1)
  df_winter_load = df_winter_load.drop('self-consumed_power_pv', axis=1)

  df_spring_load = df_spring_load.drop('curtailed_power_pv', axis=1)
  df_spring_load = df_spring_load.drop('feed-in_power_pv', axis=1)
  df_spring_load = df_spring_load.drop('self-consumed_power_pv', axis=1)

  df_autumn_load = df_autumn_load.drop('curtailed_power_pv', axis=1)
  df_autumn_load = df_autumn_load.drop('feed-in_power_pv', axis=1)
  df_autumn_load = df_autumn_load.drop('self-consumed_power_pv', axis=1)

  df_summer_pv = df_summer_pv.sort_index()
  df_winter_pv = df_winter_pv.sort_index()
  df_summer_load = df_summer_load.sort_index()
  df_winter_load = df_winter_load.sort_index()
  df_spring_pv = df_spring_pv.sort_index()
  df_autumn_pv = df_autumn_pv.sort_index()
  df_spring_load = df_spring_load.sort_index()
  df_autumn_load = df_autumn_load.sort_index()

  return df_summer_pv, df_winter_pv, df_spring_pv, df_autumn_pv, df_summer_load, df_winter_load, df_spring_load, df_autumn_load


def plot_bar_curtailed_power(eva, scenario, seasons, save_fig_dir=None):

  df_summer_pv, df_winter_pv, df_spring_pv, df_autumn_pv, df_summer_load, df_winter_load, df_spring_load, df_autumn_load = calculate_power_df(eva, scenario, seasons)
  
  plot_clustered_stacked([df_winter_pv, df_summer_pv], ['curtailed','feed-in','self-consumed'], ['winter', 'summer'], title=' ', ylabel='Energy in MWh')

  if save_fig_dir is not None:
     plt.savefig(save_fig_dir+'curtailed_PV_power_'+str(scenario)+'.png', bbox_inches='tight', dpi=dpi)
  else:
     plt.show()

  plot_clustered_stacked([df_winter_load, df_summer_load], ['curtailed','grid-obtained','self-consumed'], ['winter', 'summer'], title=' ', ylabel='Energy in MWh')

  if save_fig_dir is not None:
     plt.savefig(save_fig_dir+'curtailed_Load_power_'+str(scenario)+'.png', bbox_inches='tight', dpi=dpi)

  plot_clustered_stacked([ df_spring_pv, df_summer_pv, df_autumn_pv, df_winter_pv], ['curtailed','feed-in','self-consumed'], ['spring', 'summer', 'autumn', 'winter'], title=' ', ylabel='Energy in MWh')

  if save_fig_dir is not None:
     plt.savefig(save_fig_dir+'curtailed_PV_power_allseasons'+str(scenario)+'.png', bbox_inches='tight', dpi=dpi)

  plot_clustered_stacked([ df_spring_load, df_summer_load, df_autumn_load, df_winter_load], ['curtailed','grid-obtained','self-consumed'], ['spring', 'summer', 'autumn', 'winter'], title=' ', ylabel='Energy in MWh')

  if save_fig_dir is not None:
     plt.savefig(save_fig_dir+'curtailed_Load_power_allseasons'+str(scenario)+'.png', bbox_inches='tight', dpi=dpi)



def plot_bar_chart_percent(eva, scenarios, seasons, save_fig_dir=None):

  d_pv = {}
  d_load = {}
  d_grid_pv = {}
  d_grid_load = {}

  for sc in scenarios:
    df_summer_pv, df_winter_pv, df_spring_pv, df_autumn_pv, df_summer_load, df_winter_load, df_spring_load, df_autumn_load = calculate_power_df(eva, sc, seasons)
    df_pv = df_summer_pv + df_winter_pv + df_spring_pv + df_autumn_pv
    df_load = df_summer_load + df_winter_load + df_spring_load + df_autumn_load
    for index in df_pv.index:
      df_pv.loc[index] = df_pv.loc[index]/df_pv.loc[index].sum()*100
      df_load.loc[index] = df_load.loc[index]/df_load.loc[index].sum()*100
    d_pv[sc] = df_pv
    d_load[sc] = df_load

  for index in df_pv.index:
    d_grid_pv[index] = pd.DataFrame(index=scenarios, columns = df_pv.columns).fillna(0)
    d_grid_load[index] = pd.DataFrame(index=scenarios, columns = df_load.columns).fillna(0)

  for sc in scenarios:
    for grid in df_pv.index:
      d_grid_pv[grid].loc[sc] = d_pv[sc].loc[grid]
      d_grid_load[grid].loc[sc] = d_load[sc].loc[grid]

  # x=grid, Bars=sceanrios
  plot_clustered_stacked([d_pv[sc] for sc in d_pv.keys()], ['curtailed','feed-in','self-consumed'], [sc for sc in d_pv.keys()], title=' ', ylabel='in %')

  if save_fig_dir is not None:
      plt.savefig(save_fig_dir+'bar_chart_pv_power_'+str(1)+'.png', bbox_inches='tight', dpi=dpi)

  # x=grid, Bars=sceanrios
  plot_clustered_stacked([d_load[sc] for sc in d_load.keys()], ['curtailed','grid-obtained','self-consumed'], [sc for sc in d_load.keys()], title=' ', ylabel='in %')

  if save_fig_dir is not None:
      plt.savefig(save_fig_dir+'bar_chart_load_power_'+str(1)+'.png', bbox_inches='tight', dpi=dpi)

  # x=sceanrios, Bars=grid
  plot_clustered_stacked([d_grid_pv[sc] for sc in d_grid_pv.keys()], ['curtailed','feed-in','self-consumed'], [sc for sc in d_grid_pv.keys()], title=' ', ylabel='in %')

  if save_fig_dir is not None:
      plt.savefig(save_fig_dir+'bar_chart_pv_power_'+str(2)+'.png', bbox_inches='tight', dpi=dpi)

  # x=sceanrios, Bars=grid
  plot_clustered_stacked([d_grid_load[sc] for sc in d_grid_load.keys()], ['curtailed','grid-obtained','self-consumed'], [sc for sc in d_grid_load.keys()], title=' ', ylabel='in %')

  if save_fig_dir is not None:
      plt.savefig(save_fig_dir+'bar_chart_load_power_'+str(2)+'.png', bbox_inches='tight', dpi=dpi)

def state_of_charge(eva, net_name, n, save_fig_dir=None):
  df_soc_curtailed = pd.DataFrame(index=[net_name[7:12]], columns=[401,601,611,621,631,641]).fillna(0)
  df_soc = pd.DataFrame(index=[net_name[7:12]], columns=[400,600,610,620,630,640]).fillna(0)

  for index in eva:
   if eva[index]['scenario'] in [401,601,611,621,631,641]:
    df_soc_curtailed[eva[index]['scenario']].loc[eva[index]['net_name']] += eva[index]['soc_bss']#/n
    #df_soc[eva[index]['scenario']].loc[eva[index]['net_name']] += eva[index]['soc_bss']/n
    #print(df_soc_curtailed)
   '''
   for scenario_x in scenario:
    #soc = self.storage_soc
    fig, ax = plt.subplots()
    ax.plot(soc.index, soc)
    ax.set_xlabel('Time')
    ax.set_ylabel('State of charge in %')
    #plt.legend(grid.component_buses.index)
    plt.show()
   '''





















