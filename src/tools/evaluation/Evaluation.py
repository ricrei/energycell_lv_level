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

### Calculate Output Data ###
def calculate_relevant_outputdata_overall_eva(power):

  sum_pv = power.pv.sum()
  sum_hp = power.hp.sum()
  sum_ev = power.ev.sum()
  sum_load = power.load.sum()
  sum_total_load = sum_hp + sum_load + sum_ev

  Res = power.pv - power.hp - power.ev - power.load
  Res_pos = Res[Res > 0]
  Res_neg = Res[Res < 0]

  SelfSufficiancy = (sum_total_load + Res_neg.sum())*100/sum_total_load
  if sum_pv != 0:
    PVConsumption = (sum_pv - Res_pos.sum())*100/sum_pv
  else:
    PVConsumption = 0

  return SelfSufficiancy, PVConsumption


def calculate_net_problems_overall_eva(v, ll, tl):

  v_limit_over = 1.1
  v_limit_under = .9

  v_events = len(v.index)*len(v.columns)
  ll_events = len(ll.index)*len(ll.columns)
  tl_events = len(tl.index)*len(tl.columns)

  v_over = v[v>v_limit_over].fillna(0)
  v_over[v_over > 0] = 1 
  sum_v_over = v_over[v_over.columns].sum(axis=1).sum()
  #print('Anzahl der Überspannungsereignisse im gesamten Netz: %s' % sum_v_over.sum())
  #sum_v_over[sum_v_over > 0] = 1
  #print('Minuten in denen es zu einer Überspannung kam: %s' % sum_v_over.sum())

  v_under = v[v<v_limit_under].fillna(0)
  v_under[v_under > 0] = 1 
  sum_v_under = v_under[v_under.columns].sum(axis=1).sum()
  #print('Anzahl der Unterspannungsereignisse im gesamten Netz: %s' % sum_v_under.sum())
  #sum_v_under[sum_v_under > 0] = 1
  #print('Minuten in denen es zu einer Unterspannung kam: %s' % sum_v_under.sum())

  ll = ll[ll>100].fillna(0)
  ll[ll > 0] = 1 
  sum_ll = ll[ll.columns].sum(axis=1).sum()
  #print('Anzahl der Leitungsüberlastungen im gesamten Netz: %s' % ll.sum())
  #ll[ll > 0] = 1
  #print('Minuten in denen es zu einer Leitungsüberlastung kam: %s' % ll.sum())

  tl = tl[tl>100].fillna(0)
  tl[tl > 0] = 1 
  sum_tl = tl[tl.columns].sum(axis=1).sum()
  #print('Anzahl der Trafoüberlastungen im gesamten Netz: %s' % tl.sum())
  #tl[tl > 0] = 1
  #print('Minuten in denen es zu einer Trafoüberlastung kam: %s' % tl.sum())

  return sum_v_under, sum_v_over, v_events, sum_ll, ll_events, sum_tl, tl_events

def calculate_max_trafo_load():
  pass


### Output plots ###
def plot_generation_consumption_as_heat_map_overall_eva(power, save_fig_dir=None):

  power_pivot = power.pivot_table(columns=power.index.dayofyear, index=power.index.hour + power.index.minute/60)

  plt.figure(figsize=(10,8))
  ax = sns.heatmap(power_pivot.pv - power_pivot.load - power_pivot.hp - power_pivot.ev, center=0)
  ax.set_xlabel('Day').set_size(20)
  ax.set_ylabel('Hour').set_size(20)
  if save_fig_dir is not None:
     plt.savefig(save_fig_dir, bbox_inches='tight')

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
     plt.savefig(save_fig_dir, bbox_inches='tight')

def plot_residualload_subplot_overall_eva(power_summer, power_winter, save_fig_dir=None):

  power_summer = -power_summer*1
  power_winter = -power_winter*1
  power = [power_summer, power_winter]

  fig, ax = plt.subplots(1, 2, figsize=(10,5), sharey=True,  gridspec_kw={'wspace': .05})
  for i in [0,1]:
    ax[i].fill_between(power[i].index, 0, power[i].pv, alpha=0.7)
    ax[i].plot(power[i].index, power[i].pv, lw=.6)
    ax[i].fill_between(power[i].index, 0, -power[i].ev, alpha=0.7)
    ax[i].plot(power[i].index, -power[i].ev, lw=.6)
    ax[i].fill_between(power[i].index, -power[i].ev, -power[i].load-power[i].ev, alpha=0.7)
    ax[i].plot(power[i].index, -power[i].load-power[i].ev, lw=.6)
    ax[i].fill_between(power[i].index, -power[i].load-power[i].ev, -power[i].hp-power[i].load-power[i].ev, alpha=0.7)
    ax[i].plot(power[i].index, -power[i].hp-power[i].load-power[i].ev, lw=.6)
    power[i] = shorted_data(power[i], 'H')
    ax[i].plot(power[i].index, power[i].pv-power[i].hp-power[i].load-power[i].ev, color='black', lw=1)
    ax[i].set_xticks([k for k in power[i].index if (k.hour == 12) & (k.minute == 0)])
    ax[i].set_xticklabels(['  Day 1', '  Day 2', '  Day 3', '  Day 4', '  Day 5', '  Day 6', '  Day 7'])
    ax[i].set(xlim=(power[i].index[0], power[i].index[-1]), ylim=(-2.000, .500))
    plt.legend(['PV Generation','EV Load','Household Load','HP Load', 'Residual Load'], loc='lower right', shadow=True, markerscale=1.0)

  ax[0].set_ylabel('Power in MW')
  ax[0].set_xlabel('Summer')
  ax[1].set_xlabel('Winter')

  if save_fig_dir is not None:
     plt.savefig(save_fig_dir, bbox_inches='tight')

def plot_residualload_subplot_overall_eva_timeslot(power_summer, power_winter, save_fig_dir=None):

  power_summer = -power_summer*1
  power_winter = -power_winter*1
  power = [power_summer, power_winter]

  fig, ax = plt.subplots(1, 2, figsize=(10,5), sharey=True,  gridspec_kw={'wspace': .05})
  for i in [0,1]:
    ax[i].fill_between(power[i].index, 0, power[i].pv, alpha=0.7)
    ax[i].plot(power[i].index, power[i].pv, lw=.6)
    ax[i].fill_between(power[i].index, 0, -power[i].ev, alpha=0.7)
    ax[i].plot(power[i].index, -power[i].ev, lw=.6)
    ax[i].fill_between(power[i].index, -power[i].ev, -power[i].load-power[i].ev, alpha=0.7)
    ax[i].plot(power[i].index, -power[i].load-power[i].ev, lw=.6)
    ax[i].fill_between(power[i].index, -power[i].load-power[i].ev, -power[i].hp-power[i].load-power[i].ev, alpha=0.7)
    ax[i].plot(power[i].index, -power[i].hp-power[i].load-power[i].ev, lw=.6)
    power[i] = shorted_data(power[i], '10T')
    ax[i].plot(power[i].index, power[i].pv-power[i].hp-power[i].load-power[i].ev, color='black', lw=1)
    ax[i].set_xticks([k for k in power[i].index if (k.hour == 12) & (k.minute == 0)])
    ax[i].set_xticklabels(['  Day 1', '  Day 2', '  Day 3', '  Day 4', '  Day 5', '  Day 6', '  Day 7'])
    ax[i].set(xlim=(power[i].index[0], power[i].index[-1]), ylim=(-2.000, .500))
    plt.legend(['PV Generation','EV Load','Household Load','HP Load', 'Residual Load'], loc='lower right', shadow=True, markerscale=1.0)

  ax[0].set_ylabel('Power in MW')
  ax[0].set_xlabel('Summer')
  ax[1].set_xlabel('Winter')

  time_min_winter = pd.to_datetime('2017-01-05 00:00:00+01:00', utc=True)
  time_max_winter = pd.to_datetime('2017-01-07 00:00:00+01:00', utc=True)

  time_min_summer = pd.to_datetime('2017-05-27 00:00:00+01:00', utc=True)
  time_max_summer = pd.to_datetime('2017-05-29 00:00:00+01:00', utc=True)

  ax[0].set_xlim(time_min_summer, time_max_summer)
  ax[1].set_xlim(time_min_winter, time_max_winter)

  if save_fig_dir is not None:
     plt.savefig(save_fig_dir, bbox_inches='tight')

def plot_violin_overall_eva(df_eva_v, df_eva_l, save_fig_dir=None):
  print('Create Violin plots')
  plt.figure()
  ax = sns.violinplot(x="gridID", y="voltage", hue='timescope', data=df_eva_v, palette="muted", split=True, inner="quartile", cut=0)

  if save_fig_dir is not None:
     plt.savefig(save_fig_dir + 'violin_voltage.png', bbox_inches='tight')

  plt.figure()
  ax = sns.violinplot(x="gridID", y="lineloading", hue='timescope', data=df_eva_l, palette="muted", split=True, inner="quartile", cut=0)

  if save_fig_dir is not None:
     plt.savefig(save_fig_dir + 'violin_lineloading.png', bbox_inches='tight')

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
     plt.savefig(save_fig_dir + 'bar_scenario.png', bbox_inches='tight')

  plt.figure()
  ax = sns.barplot(x = 'gridID', y = 'value', hue = 'type', data = df_bar_2)
  ax.set(xlabel='GridID', ylabel='Overload in min per unit')

  if save_fig_dir is not None:
     plt.savefig(save_fig_dir + 'bar_gridID.png', bbox_inches='tight')

  plt.figure()
  ax = sns.barplot(x = 'type', y = 'value', hue = 'scenario', data = df_bar_1)
  ax.set(xlabel='Overload type', ylabel='Overload in min per unit')

  if save_fig_dir is not None:
     plt.savefig(save_fig_dir + 'bar_issus.png', bbox_inches='tight')


def plot_heatmap_grid_issus(eva, net_name, n, save_fig_dir=None):
  print('Create Heatmap plots grid issus')

  minutes_per_week = 7*24*60

  df_v_heatmap = pd.DataFrame(index=[net_name[7:12]], columns=[100,200,300,400]).fillna(0)
  df_l_heatmap = pd.DataFrame(index=[net_name[7:12]], columns=[100,200,300,400]).fillna(0)
  df_t_heatmap = pd.DataFrame(index=[net_name[7:12]], columns=[100,200,300,400]).fillna(0)
  v_events = pd.DataFrame(index=[net_name[7:12]], columns=[100,200,300,400]).fillna(0)
  l_events = pd.DataFrame(index=[net_name[7:12]], columns=[100,200,300,400]).fillna(0)
  t_events = pd.DataFrame(index=[net_name[7:12]], columns=[100,200,300,400]).fillna(0)

  for index in eva:
   if eva[index]['scenario'] in [100,200,300,400]:
    df_v_heatmap[eva[index]['scenario']].loc[eva[index]['net_name']] += (eva[index]['v_under'] + eva[index]['v_over'])/n
    df_l_heatmap[eva[index]['scenario']].loc[eva[index]['net_name']] += eva[index]['ll_over']/n
    df_t_heatmap[eva[index]['scenario']].loc[eva[index]['net_name']] += eva[index]['tl_over']/n
    v_events[eva[index]['scenario']].loc[eva[index]['net_name']] += len(eva[index]['v'].columns)/n
    l_events[eva[index]['scenario']].loc[eva[index]['net_name']] += len(eva[index]['ll'].columns)/n
    t_events[eva[index]['scenario']].loc[eva[index]['net_name']] += len(eva[index]['tl'].columns)/n

  x_ticklabels = ['Conv', 'EV+HP', 'PV', 'PV+EV+HP']
  y_ticklabels = ['Grid  \nRural 1', 'Grid  \nRural 2', 'Grid  \nRural 3', 'Grid    \nSuburb 1', 'Grid    \nSuburb 2']

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
  ax.set(xlabel='Scenario', ylabel='Grid')
  ax.set_xticklabels(x_ticklabels)
  ax.set_yticklabels(y_ticklabels)
  ax.set_title('Voltage Violation in %')
  #ax.set_title('Voltage Violation in Minutes per Week and Bus')

  if save_fig_dir is not None:
     plt.savefig(save_fig_dir + 'heatmap_voltage.png', bbox_inches='tight')

  #"YlOrBr"

  plt.figure()
  ax = sns.heatmap(df_l_heatmap/l_events/minutes_per_week*100, vmax = vmax, vmin = vmin, cmap="rocket_r", annot=True, square=True)#, fmt=".0f")
  ax.set(xlabel='Scenario', ylabel='Grid')
  ax.set_xticklabels(x_ticklabels)
  ax.set_yticklabels(y_ticklabels)
  ax.set_title('Line Overloading in %')
  #ax.set_title('Line Overloading in Minutes per Week and Line')

  if save_fig_dir is not None:
     plt.savefig(save_fig_dir + 'heatmap_lineloading.png', bbox_inches='tight')

  plt.figure()
  ax = sns.heatmap(df_t_heatmap/t_events/minutes_per_week*100, vmax = vmax, vmin = vmin, cmap="rocket_r", annot=True, square=True)#, fmt=".0f")
  ax.set(xlabel='Scenario', ylabel='Grid')
  ax.set_xticklabels(x_ticklabels)
  ax.set_yticklabels(y_ticklabels)
  ax.set_title('Trafo Overloading in %')
  #ax.set_title('Line Overloading in Minutes per Week and Line')

  if save_fig_dir is not None:
     plt.savefig(save_fig_dir + 'heatmap_trafoloading.png', bbox_inches='tight')


def plot_heatmap_curtailed_power(eva, net_name, n, save_fig_dir=None):
  print('Create Heatmap plots curtailed power')

  #minutes_per_week = 7*24*60

  pv_power = pd.DataFrame(index=[net_name[7:12]], columns=[401,601,611,621]).fillna(0)
  load_power = pd.DataFrame(index=[net_name[7:12]], columns=[401,601,611,621]).fillna(0)

  # Curtailed pv power
  curtailed_power_summer = pd.DataFrame(index=[net_name[7:12]], columns=[401,601,611,621]).fillna(0)
  curtailed_power_winter = pd.DataFrame(index=[net_name[7:12]], columns=[401,601,611,621]).fillna(0)

  curtailed_power_pv = pd.DataFrame(index=[net_name[7:12]], columns=[401,601,611,621]).fillna(0)
  curtailed_power_load = pd.DataFrame(index=[net_name[7:12]], columns=[401,601,611,621]).fillna(0)

  for index in eva:
    #if eva[index]['scenario'] in [401]: # 400
    if eva[index]['scenario'] in [401,601,611,621]:
      curtailed_power_pv[eva[index]['scenario']].loc[eva[index]['net_name']] += eva[index]['curtailed_power'].curtail_pv.sum()
      curtailed_power_load[eva[index]['scenario']].loc[eva[index]['net_name']] += eva[index]['curtailed_power'].curtail_load.sum()
      pv_power[eva[index]['scenario']].loc[eva[index]['net_name']] = eva[index]['power'].pv.sum()
      load_power[eva[index]['scenario']].loc[eva[index]['net_name']] = eva[index]['power'].load.sum() + eva[index]['power'].hp.sum() + eva[index]['power'].ev.sum()
      if eva[index]['time_scope_name'] == 'summer':
        curtailed_power_summer[eva[index]['scenario']].loc[eva[index]['net_name']] += eva[index]['curtailed_power'].curtail_pv.sum()
      elif eva[index]['time_scope_name'] == 'winter':
        curtailed_power_winter[eva[index]['scenario']].loc[eva[index]['net_name']] += eva[index]['curtailed_power'].curtail_pv.sum()

  curtailed_power_pv_per_cent = curtailed_power_pv/(pv_power+curtailed_power_pv)*100
  curtailed_power_load_per_cent = curtailed_power_load/(load_power+curtailed_power_load)*100

  print(pv_power+curtailed_power_pv)

  x_ticklabels = ['401', '601', '611', '621']
  y_ticklabels = ['Grid  \nRural 1', 'Grid  \nRural 2', 'Grid  \nRural 3', 'Grid    \nSuburb 1', 'Grid    \nSuburb 2']

  vmax_summer = curtailed_power_summer.max().max()/1000
  vmax_winter = curtailed_power_winter.max().max()/1000
  vmax_season = np.array([vmax_summer, vmax_winter]).max()

  vmax_pv_per_cent = curtailed_power_pv_per_cent.max().max()
  vmax_load_per_cent = curtailed_power_load_per_cent.max().max()
  vmax_pv_load_per_cent = np.array([vmax_pv_per_cent, vmax_load_per_cent]).max()

  vmin = 0
  
  plt.figure()
  ax = sns.heatmap(curtailed_power_summer/1000, vmax = vmax_season, vmin = vmin, cmap="rocket_r", annot=True, square=True)#, fmt=".0f")
  ax.set(xlabel='Scenario', ylabel='Grid')
  ax.set_xticklabels(x_ticklabels)
  ax.set_yticklabels(y_ticklabels)
  ax.set_title('Curtailed energy in summer in MWh')
  #ax.set_title('Voltage Violation in Minutes per Week and Bus')

  if save_fig_dir is not None:
     plt.savefig(save_fig_dir + 'heatmap_curtailed_power_summer.png', bbox_inches='tight')

  #"YlOrBr"

  plt.figure()
  ax = sns.heatmap(curtailed_power_winter/1000, vmax = vmax_season, vmin = vmin, cmap="rocket_r", annot=True, square=True)#, fmt=".0f")
  ax.set(xlabel='Scenario', ylabel='Grid')
  ax.set_xticklabels(x_ticklabels)
  ax.set_yticklabels(y_ticklabels)
  ax.set_title('Curtailed energy in winter in MWh')
  #ax.set_title('Line Overloading in Minutes per Week and Line')

  if save_fig_dir is not None:
     plt.savefig(save_fig_dir + 'heatmap_curtailed_power_winter.png', bbox_inches='tight')

  plt.figure()
  ax = sns.heatmap(curtailed_power_pv_per_cent, vmax = vmax_pv_load_per_cent, vmin = vmin, cmap="rocket_r", annot=True, square=True)#, fmt=".0f")
  ax.set(xlabel='Scenario', ylabel='Grid')
  ax.set_xticklabels(x_ticklabels)
  ax.set_yticklabels(y_ticklabels)
  ax.set_title('Curtailed pv energy in %')
  #ax.set_title('Voltage Violation in Minutes per Week and Bus')

  if save_fig_dir is not None:
     plt.savefig(save_fig_dir + 'heatmap_curtailed_power_pv.png', bbox_inches='tight')

  #"YlOrBr"

  plt.figure()
  ax = sns.heatmap(curtailed_power_load_per_cent, vmax = vmax_pv_load_per_cent, vmin = vmin, cmap="rocket_r", annot=True, square=True)#, fmt=".0f")
  ax.set(xlabel='Scenario', ylabel='Grid')
  ax.set_xticklabels(x_ticklabels)
  ax.set_yticklabels(y_ticklabels)
  ax.set_title('Curtailed load energy in %')
  #ax.set_title('Line Overloading in Minutes per Week and Line')

  if save_fig_dir is not None:
     plt.savefig(save_fig_dir + 'heatmap_curtailed_power_load.png', bbox_inches='tight')



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
     plt.savefig(save_fig_dir, bbox_inches='tight')

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
  ax3.legend(handles=[l5], labels=['Residualload'] ,loc="lower right")
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
     plt.savefig(save_fig_dir, bbox_inches='tight')

def plot_grid_issus_over_time_subplot(eva_summer, eva_winter, detailed=None, save_fig_dir=None):
  power_summer = eva_summer['power']
  power_summer = power_summer.load+power_summer.hp+power_summer.ev-power_summer.pv
  v_summer = eva_summer['v']
  ll_summer = eva_summer['ll']
  tl_summer = eva_summer['tl']

  power_winter = eva_winter['power']
  power_winter = power_winter.load+power_winter.hp+power_winter.ev-power_winter.pv
  v_winter = eva_winter['v']
  ll_winter = eva_winter['ll']
  tl_winter = eva_winter['tl']

  if detailed!=None:
    t_freq_new = '10T'
  else:
    t_freq_new = '30T'

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

  fig, ax = plt.subplots(3, 2, figsize=(10,5), sharey = 'row', sharex = 'col', gridspec_kw={'wspace': .05})
  ax1 = ax[1] # Voltage
  ax2 = ax[2] # Line and Trafo
  ax3 = ax[0] # Residualload
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
    #ax3[i].legend(handles=[l5], labels=['Residualload'] ,loc="lower right")
    ax1[i].set_xticks([k for k in power[i].index if (k.hour == 12) & (k.minute == 0)])
    ax1[i].set_xticklabels(['  Day 1', '  Day 2', '  Day 3', '  Day 4', '  Day 5', '  Day 6', '  Day 7'])
    ax2[i].set_xticks([k for k in power[i].index if (k.hour == 12) & (k.minute == 0)])
    ax2[i].set_xticklabels(['  Day 1', '  Day 2', '  Day 3', '  Day 4', '  Day 5', '  Day 6', '  Day 7'])
    ax3[i].set_xticks([k for k in power[i].index if (k.hour == 12) & (k.minute == 0)])
    ax3[i].set_xticklabels(['  Day 1', '  Day 2', '  Day 3', '  Day 4', '  Day 5', '  Day 6', '  Day 7'])
    if detailed == None:
      ax1[i].set(xlim=(power[i].index[0], power[i].index[-1]), ylim=(.85, 1.15))
      ax2[i].set(xlim=(power[i].index[0], power[i].index[-1]), ylim=(0, 7.0))
      ax3[i].set(xlim=(power[i].index[0], power[i].index[-1]), ylim=(-2.2, 1))

      ax1[1].legend(handles=[l2, l1, l_limit], labels=['Max Voltage', 'Min Voltage', 'Voltage Limit'] ,loc="upper right", shadow=True)
      ax2[1].legend(handles=[l4, l3, l_limit2], labels=['Lineloading', 'Trafoloading', 'Overload Limit'] ,loc="upper right", shadow=True)
      ax3[1].legend(handles=[l5], labels=['Residualload'] ,loc="lower right", shadow=True)

    else:
      time_min_winter = pd.to_datetime('2017-01-05 00:00:00+01:00', utc=True)
      time_max_winter = pd.to_datetime('2017-01-07 00:00:00+01:00', utc=True)

      time_min_summer = pd.to_datetime('2017-05-27 00:00:00+01:00', utc=True)
      time_max_summer = pd.to_datetime('2017-05-29 00:00:00+01:00', utc=True)

      time_min = [time_min_summer, time_min_winter]
      time_max = [time_max_summer, time_max_winter]

      ax1[i].set(xlim=(time_min[i], time_max[i]), ylim=(.85, 1.15))
      ax2[i].set(xlim=(time_min[i], time_max[i]), ylim=(0, 7.0))
      ax3[i].set(xlim=(time_min[i], time_max[i]), ylim=(-2.2, 1))

      ax1[1].legend(handles=[l2, l1, l_limit], labels=['Max Voltage', 'Min Voltage', 'Voltage Limit'] ,loc="upper left", shadow=True)
      ax2[1].legend(handles=[l4, l3, l_limit2], labels=['Lineloading', 'Trafoloading', 'Overload Limit'] ,loc="upper left", shadow=True)
      ax3[1].legend(handles=[l5], labels=['Residualload'] ,loc="lower left", shadow=True)

      if save_fig_dir is not None:
        save_fig_dir = save_fig_dir[:-4]+'_detailed'+save_fig_dir[-4:]

  ax2[0].set_xlabel('Summer')
  ax2[1].set_xlabel('Winter')
  ax1[0].set_ylabel('Voltage\nin p.u.')
  ax2[0].set_ylabel('Line and Trafo\nLoading in p.u.')
  ax3[0].set_ylabel('Power\nin MW')

  '''
  ax1[1].legend(handles=[l2, l1, l_limit], labels=['Max Voltage', 'Min Voltage', 'Voltage Limit'] ,loc="upper right", shadow=True)
  ax2[1].legend(handles=[l4, l3, l_limit2], labels=['Lineloading', 'Trafoloading', 'Overload Limit'] ,loc="upper right", shadow=True)
  ax3[1].legend(handles=[l5], labels=['Residualload'] ,loc="lower right", shadow=True)
  '''

  if save_fig_dir is not None:
     plt.savefig(save_fig_dir, bbox_inches='tight')

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
     plt.savefig(save_fig_dir, bbox_inches='tight')




# together with plot_curtail_power()
# together with plot_curtail_power()
def plot_clustered_stacked(dfall, labels1=None, labels2=None, title=" ",  H=".", **kwargs):
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
                rect.set_x(rect.get_x() + 1 / float(n_df + 1) * i / float(n_col))
                rect.set_hatch(H* int(3*i / n_col))#(H * int(2*i / n_col)) #edited part     
                rect.set_width(1 / float(n_df + 1))
                rect.set_alpha(.9)
                rect.set_aa(True)

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
        l2 = plt.legend(n, labels2, loc=[.01, .7]) 
    axe.add_artist(l1)
    axe.set_xlabel('Grid')
    axe.set_ylabel('Energy in MWh')
    axe.set_xticklabels(df.index)#['rural 1', 'rural 2', 'rural 3', 'suburban 1', 'suburban 2'])
    axe.set_ylim([0, 120])
    return axe


def plot_curtailed_power(eva, scenario, save_fig_dir=None):

  df = pd.DataFrame(columns=['gridID', 'time_scope', 'curtailed_power_pv', 'feed-in_power_pv', 'self-consumed_power_pv', 'curtailed_power_load', 'grid_obtained_power_load', 'self-consumed_power_load'], index=range(10))
  
  scale_factor_energy = 1/60 # kWmin -> kWh

  i = 0
  for index in eva:
    if eva[index]['scenario'] == scenario:
      df['gridID'].iloc[i] = eva[index]['net_name']
      df['time_scope'].iloc[i] = eva[index]['time_scope_name']
      curtailed_power = eva[index]['curtailed_power'].sum()
      df['feed-in_power_pv'].iloc[i] = eva[index]['power']['pv'].sum()*(100-eva[index]['PVConsumption'])/100*scale_factor_energy
      df['self-consumed_power_pv'].iloc[i] = eva[index]['power']['pv'].sum()*(eva[index]['PVConsumption'])/100*scale_factor_energy
      df['curtailed_power_pv'].iloc[i] = curtailed_power['curtail_pv']*scale_factor_energy
      df['grid_obtained_power_load'].iloc[i] = (eva[index]['power']['load'].sum() 
                                              +eva[index]['power']['hp'].sum() 
                                              +eva[index]['power']['ev'].sum()
                                              )*(100-eva[index]['SelfSufficiancy'])/100*scale_factor_energy
      df['self-consumed_power_load'].iloc[i] = (eva[index]['power']['load'].sum() 
                                              +eva[index]['power']['hp'].sum() 
                                              +eva[index]['power']['ev'].sum()
                                              )*(eva[index]['SelfSufficiancy'])/100*scale_factor_energy
      df['curtailed_power_load'].iloc[i] = curtailed_power['curtail_load']*scale_factor_energy  
      i += 1
      
  df_summer = df[df['time_scope'] == 'summer']
  df_winter = df[df['time_scope'] == 'winter']

  df_summer = df_summer.set_index('gridID')
  df_winter = df_winter.set_index('gridID')

  df_summer = df_summer.drop('time_scope', axis=1)
  df_winter = df_winter.drop('time_scope', axis=1)

  df_summer_pv = df_summer
  df_winter_pv = df_winter
  df_summer_load = df_summer
  df_winter_load = df_winter

  df_summer_pv = df_summer_pv.drop('curtailed_power_load', axis=1)
  df_summer_pv = df_summer_pv.drop('grid_obtained_power_load', axis=1)
  df_summer_pv = df_summer_pv.drop('self-consumed_power_load', axis=1)

  df_winter_pv = df_winter_pv.drop('curtailed_power_load', axis=1)
  df_winter_pv = df_winter_pv.drop('grid_obtained_power_load', axis=1)
  df_winter_pv = df_winter_pv.drop('self-consumed_power_load', axis=1)

  df_summer_load = df_summer_load.drop('curtailed_power_pv', axis=1)
  df_summer_load = df_summer_load.drop('feed-in_power_pv', axis=1)
  df_summer_load = df_summer_load.drop('self-consumed_power_pv', axis=1)

  df_winter_load = df_winter_load.drop('curtailed_power_pv', axis=1)
  df_winter_load = df_winter_load.drop('feed-in_power_pv', axis=1)
  df_winter_load = df_winter_load.drop('self-consumed_power_pv', axis=1)

  df_summer_pv = df_summer_pv.sort_index()
  df_winter_pv = df_winter_pv.sort_index()
  df_summer_load = df_summer_load.sort_index()
  df_winter_load = df_winter_load.sort_index()
  
  plot_clustered_stacked([df_winter_pv, df_summer_pv], ['curtailed','feed-in','self-consumed'], ['winter', 'summer'], title=' ')

  if save_fig_dir is not None:
     plt.savefig(save_fig_dir+'curtailed_PV_power_'+str(scenario)+'.png', bbox_inches='tight')
  else:
     plt.show()

  plot_clustered_stacked([df_winter_load, df_summer_load], ['curtailed','grid-obtained','self-consumed'], ['winter', 'summer'], title=' ')

  if save_fig_dir is not None:
     plt.savefig(save_fig_dir+'curtailed_Load_power_'+str(scenario)+'.png', bbox_inches='tight')

























