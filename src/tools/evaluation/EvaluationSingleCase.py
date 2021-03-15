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

# Handle date time conversions between pandas and matplotlib
from pandas.plotting import register_matplotlib_converters
register_matplotlib_converters()

import tools.tools as tt

import bz2
import _pickle as cPickle


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

  def plot_generation_consumption_as_heat_map_overall_eva(self):

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
