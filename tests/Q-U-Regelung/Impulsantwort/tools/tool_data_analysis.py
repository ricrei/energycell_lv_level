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

### Output plots ###

def plot_colorbar(output_dir, start_time, end_time):

  vpu = read_data(output_dir + '/res_bus_vm_pu.csv')
  fig, ax = plt.subplots(1, 1)
  c = ax.pcolormesh(vpu.index, vpu.columns, vpu.transpose(), vmin=.9, vmax=1.1, alpha=1)
  #ax.set_title('Spannungsband v_pu im Testnetz')
  #ax.set_xlabel('Uhrzeit')
  #start_time = pd.to_datetime(start_time, utc=True)
  #end_time = pd.to_datetime(end_time, utc=True)
  #ax.set_xticks([start_time, end_time])
  #ax.set_xticklabels([start_time, end_time])

  ax.set_xticklabels(['00:00', '06:00', '12:00', '18:00', '00:00'])
  ax.set_ylabel('Household')
  ax.set_xticks(['2017-05-17 00:00:00+02:00', '2017-05-17 06:00:00+02:00', '2017-05-17 12:00:00+02:00', '2017-05-17 18:00:00+02:00','2017-05-18 00:00:00+02:00'])
  fig.colorbar(c, ax=ax)
  fig.tight_layout()
  plt.show()
  #print(vpu['14'].min())

def plot_colorbar_seaborn(output_dir, start_time, end_time):
  vpu = read_data(output_dir + '/res_bus_vm_pu.csv') 
  plt.figure(figsize=(10,8))
  ax = sns.heatmap(vpu.T, vmin=.9, vmax=1.1, center=1.025, cmap='Spectral', cbar_kws=dict(ticks=[.9, .95, 1, 1.05, 1.1]))
  nr_x_ticks = 5
  x_ticks = [vpu.T.columns[int(round(len(vpu.T)*(i/nr_x_ticks), 0))] for i in range(1, nr_x_ticks + 1)]
  #print(x_ticks)
  #ax.set_xticks(x_ticks)
  '''
  ax.set_xticks([
        pd.to_datetime('2017-05-17 00:00:00+02:00', utc=True),
        pd.to_datetime('2017-05-17 06:00:00+02:00', utc=True),
        pd.to_datetime('2017-05-17 12:00:00+02:00', utc=True),
        pd.to_datetime('2017-05-17 18:00:00+02:00', utc=True),
        pd.to_datetime('2017-05-18 00:00:00+02:00', utc=True)
                ])
  '''
  ax.set_xticklabels(['00:00', '', '', '', '', '', '', '', '', '', '', '06:00', '', '', '', '', '', '', '', '', '', '', '12:00', '', '', '', '', '', '', '', '', '', '', '18:00', '', '', '', '', '', '', '', '', '', '00:00'])
  ax.set_xlabel('Time').set_size(10)
  ax.set_ylabel('Household').set_size(10)
  plt.show()

def plot_input_data():#load_p_data_file, load_q_data_file, pv_data_file):
  
  load_p_data_file = 'input-files/p0_ac_power_test.csv'
  load_q_data_file = 'input-files/q0_ac_power_test.csv'
  pv_data_file = 'input-files/pv_ac_power_test.csv'
  hp_data_file = 'input-files/hp_ac_power_test.csv'
  '''
  load_p_data_file = 'input-files/load_p_sorted.csv'
  load_q_data_file = 'input-files/load_q_sorted.csv'
  pv_data_file = 'input-files/pv_ac_power.csv'
  '''
  
  p0 = read_data(load_p_data_file)
  q0 = read_data(load_q_data_file)
  pv = read_data(pv_data_file)
  hp = read_data(hp_data_file)
  s0 = pd.DataFrame(columns=['total'])
  p0 = p0.reset_index()
  q0 = q0.reset_index()
  hp = hp.reset_index()
  pv = pv.reset_index()
  for i in range(0,74):
      if i == 0:
        s0['total'] =  (p0[str(i)]**2 + q0[str(i)]**2)**1/2 + hp['Demand_el']
      else:
        s0['total'] = s0['total'] + (p0[str(i)]**2 + q0[str(i)]**2)**1/2 + hp['Demand_el']
  plt.plot(range(len(s0['total'])),s0['total']/s0['total'].sum())
  plt.show()

def plot_generation_consumption_as_heat_map(output_dir):

  power = read_data(output_dir+'power_total_MW.csv')
  power_pivot = power.pivot_table(columns=power.index.dayofyear, index=power.index.hour + power.index.minute/60)

  plt.figure(figsize=(10,8))
  ax = sns.heatmap(power_pivot.pv - power_pivot.load - power_pivot.hp - power_pivot.ev, center=0)
  ax.set_xlabel('Day').set_size(20)
  ax.set_ylabel('Hour').set_size(20)
  plt.show()

def plot_residualload(output_dir):
  
  power = read_data(output_dir+'power_total_MW.csv')
  power = power*1000

  '''
  # Calculates the floating sum of consumption, generation and residual load for 7 days
  print('Timeindex' + '        ' + 'summed up loads' + '  ' + 'summed up generation' + '  ' + 'summed up res')
  for i in range(len(power.index)-7):
    power_loads_sum = 0
    power_gen_sum = 0
    power_res_sum = 0
    for l in range(7):
      power_loads_sum += power.hp[i+l] + power.load[i+l] + power.ev[i+l]
      power_gen_sum += power.pv[i+l]
      power_res_sum += power.hp[i+l] + power.load[i+l] + power.ev[i+l] - power.pv[i+l]
    print(str(power.index[i]) + '  ' + str(power_loads_sum.round(1)) + '  ' + str(power_gen_sum.round(1)) + '  ' + str(power_res_sum.round(1)))
  '''

  fig, ax = plt.subplots()
  ax.fill_between(power.index, 0, power.pv, alpha=0.7)
  ax.plot(power.index, power.pv, lw=.6)
  ax.fill_between(power.index, 0, -power.ev, alpha=0.7)
  ax.plot(power.index, -power.ev, lw=.6)
  ax.fill_between(power.index, -power.ev, -power.load-power.ev, alpha=0.7)
  ax.plot(power.index, -power.load-power.ev, lw=.6)
  ax.fill_between(power.index, -power.load-power.ev, -power.hp-power.load-power.ev, alpha=0.7)
  ax.plot(power.index, -power.hp-power.load-power.ev, lw=.6)
  power = shorted_data(power, 'W')
  ax.plot(power.index, power.pv-power.hp-power.load-power.ev, color='black', lw=.5)
  ax.set_xlabel('Time')
  ax.set_ylabel('Power in kW')
  #ax.set_xticklabels(['', '00:00', '03:00', '06:00', '09:00', '12:00', '15:00', '18:00', '21:00', '00:00'])
  plt.legend(['Photovoltaic generation','E-vehicle load','Household load','Heat pump load'])
  plt.show()

def calculate_relevant_outputdata(output_dir, t_freq):

  power = read_data(output_dir+'power_total_MW.csv')
  if t_freq != 'D':
    power = shorted_data(power, 'H')
    f = 1
  else:
    f = 24

  sum_pv = power.pv.sum()*f
  sum_hp = power.hp.sum()*f
  sum_ev = power.ev.sum()*f
  sum_load = power.load.sum()*f
  sum_total_load = sum_hp + sum_load + sum_ev

  Res = power.pv - power.hp - power.ev - power.load
  Res_pos = Res[Res > 0]
  Res_neg = Res[Res < 0]

  SelfSufficiancy = (sum_total_load + Res_neg.sum())*100/sum_total_load
  PVConsumption = (sum_pv - Res_pos.sum())*100/sum_pv
  print(' ')
  print('PV-Generation: %s MWh' % sum_pv.round(2))
  print('HP-Consumption: %s MWh' % sum_hp.round(2))
  print('EV-Consumption: %s MWh' % sum_ev.round(2))
  print('Load-Consumption: %s MWh' % sum_load.round(2))
  print('Total Consumption: %s MWh' % sum_total_load.round(2))
  print(' ')
  print('Self-sufficiancy (balanced): %s ' % ((sum_pv/sum_total_load*100).round(1)))
  print('Self-sufficiancy: %s ' % ((SelfSufficiancy).round(1)))
  print('PV consumption rate: %s ' % ((PVConsumption).round(1)))

def calculate_net_problems(output_dir):

  v = read_data(output_dir+'res_bus_vm_pu.csv')

  v_over = v[v>1.1].fillna(0)
  v_over[v_over > 0] = 1 
  sum_v_over = v_over[v_over.columns].sum(axis=1)
  print('Anzahl der Überspannungsereignisse im gesamten Netz: %s' % sum_v_over.sum())
  sum_v_over[sum_v_over > 0] = 1
  print('Minuten in denen es zu einer Überspannung kam: %s' % sum_v_over.sum())

  v_under = v[v<.9].fillna(0)
  v_under[v_under > 0] = 1 
  sum_v_under = v_under[v_under.columns].sum(axis=1)
  print('Anzahl der Unterspannungsereignisse im gesamten Netz: %s' % sum_v_under.sum())
  sum_v_under[sum_v_under > 0] = 1
  print('Minuten in denen es zu einer Unterspannung kam: %s' % sum_v_under.sum())

  ll = read_data(output_dir+'res_line_load_percent.csv')
  ll = ll[ll>100].fillna(0)
  ll[ll > 0] = 1 
  ll = ll[ll.columns].sum(axis=1)
  print('Anzahl der Leitungsüberlastungen im gesamten Netz: %s' % ll.sum())
  ll[ll > 0] = 1
  print('Minuten in denen es zu einer Leitungsüberlastung kam: %s' % ll.sum())

  tl = read_data(output_dir+'res_trafo_load_percent.csv')

  tl = tl[tl>100].fillna(0)
  tl[tl > 0] = 1 
  tl = tl[tl.columns].sum(axis=1)
  print('Anzahl der Trafoüberlastungen im gesamten Netz: %s' % tl.sum())
  tl[tl > 0] = 1
  print('Minuten in denen es zu einer Trafoüberlastung kam: %s' % tl.sum())

  #plt.plot(sum_v_over)
  #ax = sns.violinplot(y=v_over, cut=0)
  plt.show()

def plot_grid_issus_over_time(output_dir):
  v = read_data(output_dir+'res_bus_vm_pu.csv')
  ll = read_data(output_dir+'res_line_load_percent.csv')
  tl = read_data(output_dir+'res_trafo_load_percent.csv')

  v_min = v.T.min().T
  v_max = v.T.max().T
  ll_max = ll.T.max().T
  tl_max = tl.T.max().T

  fig, (ax1, ax2) = plt.subplots(2)
  fig.suptitle('Vertically stacked subplots')
  l1 = ax1.plot(v_min, 'r')[0]
  l2 = ax1.plot(v_max, 'y')[0]
  l3 = ax2.plot(tl_max, 'g')[0]
  l4 = ax2.plot(ll_max, 'b')[0]
  ax1.legend(handles=[l2, l1], labels=['overvoltage', 'undervoltage'])
  ax2.legend(handles=[l4, l3], labels=['line overload', 'trafo overload'])
  plt.show()

def plot_grid_issus_over_power(output_dir):
  power = read_data(output_dir+'power_total_MW.csv')
  power = power.load+power.hp+power.ev-power.pv
  v = read_data(output_dir+'res_bus_vm_pu.csv')
  ll = read_data(output_dir+'res_line_load_percent.csv')
  tl = read_data(output_dir+'res_trafo_load_percent.csv')

  v_over = v[v>1.1]
  v_under = v[v<.9]
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
  plt.show()

def plot_reactive_power(output_dir):
  p = read_data(output_dir+'active_power_MW.csv')
  q = read_data(output_dir+'reactive_power_MW.csv')
  v = read_data(output_dir+'res_bus_vm_pu.csv')
  cos_phi = p/(p**2 + q**2)**(1/2)

  plt.figure()
  plt.plot(v['42'],q['42'], 'o')
  plt.figure()
  plt.plot(v['42']-1)
  plt.plot(q['42'])
  plt.plot(cos_phi['42'])
  plt.show()

def plot_hist_grid_issus(output_dir):
  power = read_data(output_dir+'power_total_MW.csv')
  power = power.load+power.hp+power.ev-power.pv
  v = read_data(output_dir+'res_bus_vm_pu.csv')
  ll = read_data(output_dir+'res_line_load_percent.csv')
  tl = read_data(output_dir+'res_trafo_load_percent.csv')

  fig, (ax1, ax2, ax3) = plt.subplots(3)
  fig.suptitle('Vertically stacked subplots')
  h1 = ax1.hist(v.stack().values, bins=100, density=True,
         stacked=True,
         cumulative=True)[0]
  h4 = ax2.hist(ll.stack().values, bins=100, density=True,
         stacked=True,
         cumulative=True)[0]
  h3 = ax3.hist(tl, bins=100, density=True,
         stacked=True,
         cumulative=True)[0]
  #ax1.legend(handles=[h1], labels=['Voltage'])
  #ax2.legend(handles=[h4, h3], labels=['Line Overload', 'Trafo Overload'])
  plt.show()

def plot_net_res(net):
  # delete the geocoordinates
  #net.bus_geodata.drop(net.bus_geodata.index, inplace=True)
  #net.line_geodata.drop(net.line_geodata.index, inplace=True)
  #ppply.simple_plotly(net)
  ppply.pf_res_plotly(net, aspectratio=(1.3,1))

def compare_results_of_different_timesteps():
  vpu_1min = read_data('output-files/2017-09-07/1min/res_bus_vm_pu.csv')
  lilo_1min = read_data('output-files/2017-09-07/1min/res_line_load_percent.csv')
  vpu_5min = read_data('output-files/2017-09-07/5min/res_bus_vm_pu.csv')
  lilo_5min = read_data('output-files/2017-09-07/5min/res_line_load_percent.csv')
  vpu_10min = read_data('output-files/2017-09-07/10min/res_bus_vm_pu.csv')
  lilo_10min = read_data('output-files/2017-09-07/10min/res_line_load_percent.csv')
  vpu_15min = read_data('output-files/2017-09-07/15min/res_bus_vm_pu.csv')
  lilo_15min = read_data('output-files/2017-09-07/15min/res_line_load_percent.csv')
  vpu_30min = read_data('output-files/2017-09-07/30min/res_bus_vm_pu.csv')
  lilo_30min = read_data('output-files/2017-09-07/30min/res_line_load_percent.csv')
  vpu_60min = read_data('output-files/2017-09-07/60min/res_bus_vm_pu.csv')
  lilo_60min = read_data('output-files/2017-09-07/60min/res_line_load_percent.csv')
  
  ax = plt.subplot()
  plt.plot(vpu_1min['14'])
  plt.plot(vpu_5min['14'])
  plt.plot(vpu_10min['14'])
  plt.plot(vpu_15min['14'])
  plt.plot(vpu_30min['14'])
  plt.plot(vpu_60min['14'])
  plt.legend(['1min','5min','10min','15min','30min','60min'])
  ax.set_title('Spannungsband v_pu im Testnetz')
  ax.set_xlabel('Uhrzeit am 27.05.')
  ax.set_xticks(['2017-09-07 00:00:00+02:00', '2017-09-07 06:00:00+02:00', '2017-09-07 12:00:00+02:00', '2017-09-07 18:00:00+02:00','2017-09-07 23:55:00+02:00'])
  ax.set_xticklabels(['00:00', '06:00', '12:00', '18:00', '00:00'])
  ax.set_ylabel('bus')
  plt.show()


def impulse_response(output_dir):
  p = read_data(output_dir+'active_power_MW.csv')
  q = read_data(output_dir+'reactive_power_MW.csv')
  v = read_data(output_dir+'res_bus_vm_pu.csv')
  cos_phi = p/(p**2 + q**2)**(1/2)

  fig, (ax1, ax2, ax3, ax4) = plt.subplots(4, sharex='col')
  ax1.plot(p)
  ax1.set_ylabel('P in MW')
  ax2.plot(q)
  ax2.set_ylabel('Q in MW')
  ax3.plot(cos_phi)
  ax3.set_ylabel('cos(phi)')
  ax4.plot(v)
  ax4.set_ylabel('V in p.u.')
  plt.show()





