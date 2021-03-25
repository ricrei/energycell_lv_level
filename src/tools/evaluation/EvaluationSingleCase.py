import os
import csv
import time
import numpy as np
import pandas as pd

import matplotlib.pyplot as plt
import pandapower.plotting.plotly as ppply
import seaborn as sns

# Handle date time conversions between pandas and matplotlib
from pandas.plotting import register_matplotlib_converters
register_matplotlib_converters()

import tools.tools as tt



class EvaluationSingleCase():
  
  def __init__(self, output_dir, net_name, scenario, time_scope):
    self.output_dir = output_dir
    self.net_name = net_name
    self.scenario = scenario
    self.time_scope = time_scope

    self.p = self.read_data(output_dir+'active_power_MW.csv')
    self.q = self.read_data(output_dir+'reactive_power_MW.csv')
    self.power = self.read_data(self.output_dir+'power_total_MW.csv')
    self.v = self.read_data(self.output_dir+'res_bus_vm_pu.csv')
    self.ll = self.read_data(self.output_dir+'res_line_load_percent.csv')
    self.tl = self.read_data(self.output_dir+'res_trafo_load_percent.csv')


  ### Helper Methods ###
  def read_data(self, filename):
    data = pd.read_csv(filename, delimiter = ',', low_memory=False)
    data['timestamp'] = pd.to_datetime(data['timestamp'], utc=True)
    data = data.set_index('timestamp')

    return data

  def shorted_data(self, data, t_freq):
    data_shorted = data.resample(t_freq).mean()
    data_shorted = data_shorted.round(4)
    data_shorted.index = pd.DatetimeIndex(data_shorted.index, tz=None, ambiguous='infer')

    return data_shorted

  ### Output plots / Inputdata ###
  def plot_residualload(self):
    power = self.power*1000

    fig, ax = plt.subplots()
    ax.fill_between(power.index, 0, power.pv, alpha=0.7)
    ax.plot(power.index, power.pv, lw=.6)
    ax.fill_between(power.index, 0, -power.ev, alpha=0.7)
    ax.plot(power.index, -power.ev, lw=.6)
    ax.fill_between(power.index, -power.ev, -power.load-power.ev, alpha=0.7)
    ax.plot(power.index, -power.load-power.ev, lw=.6)
    ax.fill_between(power.index, -power.load-power.ev, -power.hp-power.load-power.ev, alpha=0.7)
    ax.plot(power.index, -power.hp-power.load-power.ev, lw=.6)
    power = self.shorted_data(power, 'H')
    ax.plot(power.index, power.pv-power.hp-power.load-power.ev, color='black', lw=.5)
    ax.set_xlabel('Time')
    ax.set_ylabel('Power in kW')
    #ax.set_xticklabels(['', '00:00', '03:00', '06:00', '09:00', '12:00', '15:00', '18:00', '21:00', '00:00'])
    plt.legend(['Photovoltaic generation','E-vehicle load','Household load','Heat pump load'])
    plt.show()

  def plot_generation_consumption_as_heat_map(self):

    power_pivot = self.power.pivot_table(columns=self.power.index.dayofyear, index=self.power.index.hour + self.power.index.minute/60)

    plt.figure(figsize=(10,8))
    ax = sns.heatmap(power_pivot.pv - power_pivot.load - power_pivot.hp - power_pivot.ev, center=0)
    ax.set_xlabel('Day').set_size(20)
    ax.set_ylabel('Hour').set_size(20)
    plt.show()

  ### Output plots / Outputdata ###
  def plot_colorbar_seaborn(self):
    plt.figure(figsize=(10,8))
    ax = sns.heatmap(self.v.T, vmin=.9, vmax=1.1, center=1.025, cmap='Spectral', cbar_kws=dict(ticks=[.9, .95, 1, 1.05, 1.1]))
    nr_x_ticks = 5
    x_ticks = [self.v.T.columns[int(round(len(self.v.T.columns)*(i/nr_x_ticks)-.5, 0))] for i in range(1, nr_x_ticks + 1)]
    ax.set_xticklabels(['00:00', '', '', '', '', '', '', '', '', '', '', '06:00', '', '', '', '', '', '', '', '', '', '', '12:00', '', '', '', '', '', '', '', '', '', '', '18:00', '', '', '', '', '', '', '', '', '', '00:00'])
    ax.set_xlabel('Time').set_size(10)
    ax.set_ylabel('Household').set_size(10)
    plt.show()


  ### calculate and print relevant parameters ###
  def calculate_relevant_outputdata(self):

    power = self.power

    if self.time_scope['t_freq'] != 'D':
      power = self.shorted_data(power, 'H')
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
    print('Self-sufficiancy (balanced): %s %%' % ((sum_pv/sum_total_load*100).round(1)))
    print('Self-sufficiancy: %s %%' % ((SelfSufficiancy).round(1)))
    print('PV consumption rate: %s %%' % ((PVConsumption).round(1)))

  def calculate_net_problems(self):

    v = self.v
    ll = self.ll
    tl = self.tl

    print(' ')

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

    ll = ll[ll>100].fillna(0)
    ll[ll > 0] = 1 
    ll = ll[ll.columns].sum(axis=1)
    print('Anzahl der Leitungsüberlastungen im gesamten Netz: %s' % ll.sum())
    ll[ll > 0] = 1
    print('Minuten in denen es zu einer Leitungsüberlastung kam: %s' % ll.sum())

    tl = tl[tl>100].fillna(0)
    tl[tl > 0] = 1 
    tl = tl[tl.columns].sum(axis=1)
    print('Anzahl der Trafoüberlastungen im gesamten Netz: %s' % tl.sum())
    tl[tl > 0] = 1
    print('Minuten in denen es zu einer Trafoüberlastung kam: %s' % tl.sum())


  def plot_grid_issus_over_time(self):
    v = self.v
    ll = self.ll
    tl = self.tl

    v_min = v.T.min().T
    v_max = v.T.max().T
    ll_max = ll.T.max().T
    tl_max = tl.T.max().T

    fig, (ax1, ax2) = plt.subplots(2)
    fig.suptitle(' ')
    l1 = ax1.plot(v_min, 'r')[0]
    l2 = ax1.plot(v_max, 'y')[0]
    l3 = ax2.plot(tl_max, 'g')[0]
    l4 = ax2.plot(ll_max, 'b')[0]
    ax1.legend(handles=[l2, l1], labels=['overvoltage', 'undervoltage'])
    ax2.legend(handles=[l4, l3], labels=['line overload', 'trafo overload'])
    plt.show()

  def plot_grid_issus_over_power(self):
    power = self.power
    power = power.load+power.hp+power.ev-power.pv
    v = self.v
    ll = self.ll
    tl = self.tl

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

  def plot_reactive_power(self):
    p = self.p
    q = self.q
    v = self.v
    cos_phi = p/(p**2 + q**2)**(1/2)

    fig, (ax1, ax2, ax3) = plt.subplots(3)
    fig.suptitle(' ')
    ax1.plot(v)[0]
    ax2.plot(q)[0]
    ax3.plot(cos_phi)[0]
    ax1.set_ylabel('Voltage in p.u.')
    ax2.set_ylabel('Reactive power in Mvar')
    ax3.set_ylabel('cos(phi)')
    ax3.set_xlabel('Time')
    plt.show()
