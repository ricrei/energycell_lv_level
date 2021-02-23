import pandas as pd
import matplotlib.pyplot as plt
import matplotlib as mpl
import numpy as np
import pandapower.plotting.plotly as ppply
import seaborn as sns
from datetime import datetime, timedelta


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

### Output plots ###
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

def plot_generation_consumption_as_heat_map_overall_eva(power, save_fig_dir=None):

  power_pivot = power.pivot_table(columns=power.index.dayofyear, index=power.index.hour + power.index.minute/60)

  plt.figure(figsize=(10,8))
  ax = sns.heatmap(power_pivot.pv - power_pivot.load - power_pivot.hp - power_pivot.ev, center=0)
  ax.set_xlabel('Day').set_size(20)
  ax.set_ylabel('Hour').set_size(20)
  if save_fig_dir is not None:
     plt.savefig(save_fig_dir)

def plot_residualload_overall_eva(power, save_fig_dir=None):

  power = power*1000

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
  #ax.plot(power.index, power.pv-power.hp-power.load-power.ev, color='black', lw=.5)
  ax.set_xlabel('Time')
  ax.set_ylabel('Power in kW')
  ax.set_xticks([i for i in power.index if (i.hour == 12) & (i.minute == 0)])
  ax.set_xticklabels(['  Day 1', '  Day 2', '  Day 3', '  Day 4', '  Day 5', '  Day 6', '  Day 7'])
  ax.set(xlim=(power.index[0], power.index[-1]))
  plt.legend(['Photovoltaic generation','E-vehicle load','Household load','Heat pump load'])
  if save_fig_dir is not None:
     plt.savefig(save_fig_dir)


def plot_violin_overall_eva(df_eva_v, df_eva_l, save_fig_dir=None):
  print('Create Violin plots')
  plt.figure()
  ax = sns.violinplot(x="gridID", y="voltage", hue='timescope', data=df_eva_v, palette="muted", split=True, inner="quartile", cut=0)

  if save_fig_dir is not None:
     plt.savefig(save_fig_dir + 'violin_voltage.png')

  plt.figure()
  ax = sns.violinplot(x="gridID", y="lineloading", hue='timescope', data=df_eva_l, palette="muted", split=True, inner="quartile", cut=0)

  if save_fig_dir is not None:
     plt.savefig(save_fig_dir + 'violin_lineloading.png')

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
     plt.savefig(save_fig_dir + 'bar_scenario.png')

  plt.figure()
  ax = sns.barplot(x = 'gridID', y = 'value', hue = 'type', data = df_bar_2)
  ax.set(xlabel='GridID', ylabel='Overload in min per unit')

  if save_fig_dir is not None:
     plt.savefig(save_fig_dir + 'bar_gridID.png')

  plt.figure()
  ax = sns.barplot(x = 'type', y = 'value', hue = 'scenario', data = df_bar_1)
  ax.set(xlabel='Overload type', ylabel='Overload in min per unit')

  if save_fig_dir is not None:
     plt.savefig(save_fig_dir + 'bar_issus.png')


def plot_heatmap_grid_issus(eva, net_name, n, save_fig_dir=None):
  print('Create Heatmap plots')
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
  ax.set(xlabel='Scenario', ylabel='Grid')

  if save_fig_dir is not None:
     plt.savefig(save_fig_dir + 'heatmap_voltage.png')

  plt.figure()
  ax = sns.heatmap(df_l_heatmap/l_events, annot=True)
  ax.set(xlabel='Scenario', ylabel='Grid')

  if save_fig_dir is not None:
     plt.savefig(save_fig_dir + 'heatmap_lineloading.png')


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
     plt.savefig(save_fig_dir)

def plot_grid_issus_over_time(eva, save_fig_dir=None):
  power = eva['power']
  power = power.load+power.hp+power.ev-power.pv
  v = eva['v']
  ll = eva['ll']
  tl = eva['tl']

  v_min = v.T.min().T
  v_max = v.T.max().T
  ll_max = ll.T.max().T
  tl_max = tl.T.max().T

  fig, (ax1, ax2, ax3) = plt.subplots(3)
  fig.suptitle(' ')
  l1 = ax1.plot(v_min, 'r')[0]
  l2 = ax1.plot(v_max, 'y')[0]
  l3 = ax2.plot(tl_max, 'g')[0]
  l4 = ax2.plot(ll_max, 'b')[0]
  l5 = ax3.plot(power, 'k')[0]
  ax1.legend(handles=[l2, l1], labels=['overvoltage', 'undervoltage'] ,loc="upper right")
  ax2.legend(handles=[l4, l3], labels=['line overload', 'trafo overload'] ,loc="upper right")
  ax3.legend(handles=[l5], labels=['Residualload'] ,loc="lower right")
  ax1.set_xlabel('Time')
  #ax2.set_xlabel('Time')
  #ax3.set_xlabel('Time')
  ax1.set_ylabel('Voltage\nin p.u.')
  ax2.set_ylabel('Line and trafo\nloading I/I_n')
  ax3.set_ylabel('Power\nin MW')
  ax1.set_xticks([i for i in power.index if (i.hour == 12) & (i.minute == 0)])
  ax1.set_xticklabels(['  Day 1', '  Day 2', '  Day 3', '  Day 4', '  Day 5', '  Day 6', '  Day 7'])
  ax2.set_xticks([i for i in power.index if (i.hour == 12) & (i.minute == 0)])
  ax2.set_xticklabels(['  Day 1', '  Day 2', '  Day 3', '  Day 4', '  Day 5', '  Day 6', '  Day 7'])
  ax3.set_xticks([i for i in power.index if (i.hour == 12) & (i.minute == 0)])
  ax3.set_xticklabels(['  Day 1', '  Day 2', '  Day 3', '  Day 4', '  Day 5', '  Day 6', '  Day 7'])
  ax1.set(xlim=(power.index[0], power.index[-1]), ylim=(.9, 1.13))
  ax2.set(xlim=(power.index[0], power.index[-1]), ylim=(0, 450))
  ax3.set(xlim=(power.index[0], power.index[-1]), ylim=(-2.1, 1))


  if save_fig_dir is not None:
     plt.savefig(save_fig_dir)

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
     plt.savefig(save_fig_dir)
