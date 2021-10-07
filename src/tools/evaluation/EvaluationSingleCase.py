import numpy as np 
import pandas as pd
from scipy.fft import fft, fftfreq

import pandapower as pp
from pandapower.plotting.plotly import simple_plotly
from pandapower.plotting.plotly import pf_res_plotly
import pandapower.plotting as ppplt

import matplotlib.pyplot as plt
import seaborn as sns

# Handle date time conversions between pandas and matplotlib
from pandas.plotting import register_matplotlib_converters
register_matplotlib_converters()

import tools.tools as tt

#import BSS_sizing_helper as BSS_sizing

class EvaluationSingleCase():
  
  def __init__(self, grid, output_dir, net_name, scenario, time_scope): 
    self.grid = grid
    self.output_dir = output_dir
    self.net_name = net_name
    self.scenario = scenario
    self.time_scope = time_scope

    self.v = self.read_data(self.output_dir+'res_bus_vm_pu.csv')
    self.ll = self.read_data(self.output_dir+'res_line_load_percent.csv')
    self.tl = self.read_data(self.output_dir+'res_trafo_load_percent.csv')
    self.power = self.read_data(self.output_dir+'power_total_MW.csv')
    self.pv_p = self.read_data(self.output_dir+'pv_active_power_MW.csv')
    self.pv_q = self.read_data(self.output_dir+'pv_reactive_power_MW.csv')
    self.load_p = self.read_data(self.output_dir+'load_active_power_MW.csv')
    self.load_q = self.read_data(self.output_dir+'load_reactive_power_MW.csv')
    self.ev_soc = self.read_data(self.output_dir+'ev_soc.csv')
    self.v_pu_ext_grid = self.read_data(self.output_dir+'v_pu_ext_grid.csv')
    self.storage_p = self.read_data(self.output_dir+'storage_active_power_MW.csv')
    self.trafo_p = self.read_data(self.output_dir+'trafo_active_power_MW.csv')
    self.losses_p = self.read_data(self.output_dir+'losses_active_power_MW.csv')
    self.bss_p = self.read_data(self.output_dir+'storage_active_power_MW.csv') ###
    self.storage_soc = self.read_data(self.output_dir+'storage_state_of_charge_percent.csv') # in powerflow wird aktuell noch e_mwh an soc übergeben
    self.curtailed_power = self.read_data(self.output_dir+'curtailed_power_MW.csv')

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
  def plot_residualload(self, add_curtail):
    prop_cycle = plt.rcParams['axes.prop_cycle']
    c = prop_cycle.by_key()['color']

    power = self.power*1000
    curtailed = self.curtailed_power*1000

    '''
    storage = -self.storage_p.sum(axis=1)*1000
    storage_sum = storage.copy()
    storage_charge = storage.copy()
    storage_charge[storage_charge > 0] = 0
    storage_charge = -storage_charge
    storage_charge = pd.Series(storage_charge[0])
    storage_discharge = storage.copy()
    storage_discharge[storage_discharge < 0] = 0
    storage_discharge = pd.Series(storage_discharge[0])
    '''
    storage = -self.storage_p*1000
    storage_sum = storage.sum(axis=1)
    storage_charge = storage.copy()
    storage_charge[storage_charge > 0] = 0
    storage_charge = -storage_charge
    storage_charge = storage_charge.sum(axis=1)

    storage_discharge = storage.copy()
    storage_discharge[storage_discharge < 0] = 0
    storage_discharge = storage_discharge.sum(axis=1)

    fig, ax = plt.subplots()
    ax.fill_between(power.index,                     -storage_discharge,                     -storage_discharge - power.pv, alpha=0.7, color=c[0])
    ax.fill_between(power.index,                         storage_charge,                         power.ev + storage_charge, alpha=0.7, color=c[1])
    ax.fill_between(power.index,              power.ev + storage_charge,            power.load + power.ev + storage_charge, alpha=0.7, color=c[2])
    ax.fill_between(power.index, power.load + power.ev + storage_charge, power.hp + power.load + power.ev + storage_charge, alpha=0.7, color=c[3])
    ax.fill_between(power.index, 0 , storage_charge     , alpha=0.7, color=c[4])
    ax.fill_between(power.index, 0 , -storage_discharge , alpha=0.7, color=c[4])
    if add_curtail:
      ax.fill_between(power.index, power.hp + power.load + power.ev + storage_charge, power.hp + power.load + power.ev + storage_charge + curtailed.curtail_load, alpha=0.2, color=c[5])
      ax.fill_between(power.index,                     -storage_discharge - power.pv,                       -storage_discharge - power.pv - curtailed.curtail_pv, alpha=0.2, color=c[0])

    ax.plot(power.index, -storage_discharge-power.pv, lw=.6)
    ax.plot(power.index, storage_charge+power.ev, lw=.6)
    ax.plot(power.index, storage_charge+power.load+power.ev, lw=.6)
    ax.plot(power.index, storage_charge+power.hp+power.load+power.ev, lw=.6)
    ax.plot(storage.index, storage_charge    , lw=.6)
    ax.plot(storage.index, -storage_discharge, lw=.6)

    #power = self.shorted_data(power, '1H')
    #storage = self.shorted_data(storage, '1H')
    ax.plot(power.index, -power.pv+power.hp+power.load+power.ev-storage_sum, color='black', lw=.5)
    ax.set_xlabel('Time')
    ax.set_ylabel('Power in kW')
    #ax.set_xticklabels(['', '00:00', '03:00', '06:00', '09:00', '12:00', '15:00', '18:00', '21:00', '00:00'])
    plt.legend(['Photovoltaic generation','E-vehicle load','Household load','Heat pump load', 'Storage'])
    plt.show()

  def plot_generation_consumption_as_heat_map(self):

    power_pivot = self.power.pivot_table(columns=self.power.index.dayofyear, index=self.power.index.hour + self.power.index.minute/60)

    plt.figure(figsize=(10,8))
    ax = sns.heatmap(power_pivot.pv - power_pivot.load - power_pivot.hp - power_pivot.ev, center=0)
    ax.set_xlabel('Day').set_size(20)
    ax.set_ylabel('Hour').set_size(20)

  ### Output plots / Outputdata ###
  def plot_colorbar_seaborn(self):
    plt.figure(figsize=(10,8))
    ax = sns.heatmap(self.v.T, vmin=.9, vmax=1.1, center=1.025, cmap='Spectral', cbar_kws=dict(ticks=[.9, .95, 1, 1.05, 1.1]))
    nr_x_ticks = 5
    x_ticks = [self.v.T.columns[int(round(len(self.v.T.columns)*(i/nr_x_ticks)-.5, 0))] for i in range(1, nr_x_ticks + 1)]
    #ax.set_xticklabels(['00:00', '', '', '', '', '', '', '', '', '', '', '06:00', '', '', '', '', '', '', '', '', '', '', '12:00', '', '', '', '', '', '', '', '', '', '', '18:00', '', '', '', '', '', '', '', '', '', '00:00'])
    ax.set_xlabel('Time').set_size(10)
    ax.set_ylabel('Household').set_size(10)

  ### calculate and print relevant parameters ###
  def calculate_relevant_outputdata(self):

    power = self.power
    losses = self.losses_p
    trafo_p = self.trafo_p
    curtail_p = self.curtailed_power

    if self.time_scope['t_freq'] != '1D':
      power = self.shorted_data(power, '1H')
      losses = self.shorted_data(losses, '1H')
      trafo_p = self.shorted_data(trafo_p, '1H')
      curtail_p = self.shorted_data(curtail_p, '1H')
      f = 1
    else:
      f = 24

    sum_curtailed_pv = curtail_p.curtail_pv.sum()*f
    sum_curtailed_load = curtail_p.curtail_load.sum()*f
    losses = losses.sum().sum()
    sum_pv = power.pv.sum()*f
    sum_hp = power.hp.sum()*f
    sum_ev = power.ev.sum()*f
    sum_load = power.load.sum()*f
    sum_total_load = sum_hp + sum_load + sum_ev

    Res = -1*trafo_p.values
    
    Res_pos = Res[Res > 0]
    Res_neg = Res[Res < 0]

    SelfSufficiancy = (sum_total_load + losses + Res_neg.sum())*100/(sum_total_load + losses)
    if sum_pv > 0:
      PVConsumption = (sum_pv - Res_pos.sum())*100/sum_pv
    else:
      PVConsumption = sum_pv*0.0
      
    print(' ')
    print('PV-Generation: %s MWh' % sum_pv.round(2))
    print('HP-Consumption: %s MWh' % sum_hp.round(2))
    print('EV-Consumption: %s MWh' % sum_ev.round(2))
    print('Load-Consumption: %s MWh' % sum_load.round(2))
    print('Total Consumption: %s MWh' % sum_total_load.round(2))
    print(' ')
    print('Total Losses (lines+trafo): %s MWh' % losses.round(2))
    print('Curtailed PV Energy: %s MWh' % sum_curtailed_pv.round(2))
    print('Curtailed Load Energy: %s MWh' % sum_curtailed_load.round(2))
    print(' ')
    print('Generation/Consumption ratio: %s %%' % ((sum_pv/sum_total_load*100).round(1)))
    print('Self-sufficiancy: %s %%' % ((SelfSufficiancy).round(2)))
    print('PV consumption rate: %s %%' % ((PVConsumption).round(2)))
    print(' ')

  def calculate_net_problems(self):

    v = self.v
    ll = self.ll
    tl = self.tl

    n_buses = len(v.columns)
    n_lines = len(ll.columns)

    n_timesteps = len(v.index)

    v_over = v[v>1.1].fillna(0)
    v_over[v_over > 0] = 1 
    sum_v_over = v_over[v_over.columns].sum(axis=1)
    sum_v_over[sum_v_over > 0] = 1
    v_over = v_over.sum().sum()

    v_under = v[v<.9].fillna(0)
    v_under[v_under > 0] = 1 
    sum_v_under = v_under[v_under.columns].sum(axis=1)
    sum_v_under[sum_v_under > 0] = 1
    v_under = v_under.sum().sum()

    ll = ll[ll>100].fillna(0)
    ll[ll > 0] = 1 
    ll = ll[ll.columns].sum(axis=1)
    ll[ll > 0] = 1
    ll = ll.sum()

    tl = tl[tl>100].fillna(0)
    tl[tl > 0] = 1 
    tl = tl[tl.columns].sum(axis=1)
    tl[tl > 0] = 1
    tl = tl.sum()

    print('Over voltage events     : %s %%' % (v_over/(n_buses*n_timesteps)*100).round(3))
    print('Under voltage events    : %s %%' % (v_under/(n_buses*n_timesteps)*100).round(3))
    print('Line overloading events : %s %%' % (ll/(n_lines*n_timesteps)*100).round(3))
    print('Trafo overloading events: %s %%' % (tl/(n_timesteps)*100).round(3))

  ### plots ###
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

  def plot_bss_active_power(self):
    fig, ax = plt.subplots()
    line = ax.plot(self.storage_p)
    plt.xlabel('Time')
    plt.ylabel('Storage active power in MW')
    plt.grid(True)
    plt.show()

  def plot_pv_active_power(self):
    fig, ax = plt.subplots()
    line = ax.plot(self.pv_p)
    plt.xlabel('Time')
    plt.ylabel('PV active power in MW')
    plt.grid(True)
    plt.show()


  def plot_pv_reactive_power(self):
    p = self.pv_p
    q = self.pv_q
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

  def plot_soc(self):
    #busses_num = len(grid.component_buses.index)
    #array_bus = np.arange(busses_num)
    soc = self.storage_soc
    fig, ax = plt.subplots()
    ax.plot(soc.index, soc)
    ax.set_xlabel('Time')
    ax.set_ylabel('State of charge in %')
    #plt.legend(grid.component_buses.index)
    plt.show()

  def plot_ev_soc(self):
    #busses_num = len(grid.component_buses.index)
    #array_bus = np.arange(busses_num)
    soc = self.ev_soc
    fig, ax = plt.subplots()
    ax.plot(soc.index, soc)
    ax.set_xlabel('Time')
    ax.set_ylabel('State of charge in %')
    #plt.legend(grid.component_buses.index)
    plt.show()

  def plot_bss_p_mw(self):
    bss_p = self.bss_p
    fig, ax = plt.subplots()
    ax.plot(bss_p.index, bss_p)
    ax.set_xlabel('Time')
    ax.set_ylabel('Power in MW')
    #plt.legend(grid.component_buses.index)
    plt.show()
    
  def plot_grid(self, time_sample=None):
    if time_sample==None:
      raise ValueError('plot_grid failed. Please define time_sample.')

    def fill_grid_with_power_values(timestep):
      self.grid.net.sgen['p_mw'] = self.pv_p.loc[timestep].values
      self.grid.net.sgen['q_mvar'] = self.pv_q.loc[timestep].values
      self.grid.net.load['p_mw'] = self.load_p.loc[timestep].values
      self.grid.net.load['q_mvar'] = self.load_q.loc[timestep].values
      self.grid.net.storage['p_mw'] = self.storage_p.loc[timestep].values
      self.grid.net.ext_grid.vm_pu = self.v_pu_ext_grid.loc[timestep].values

    time_sample = pd.to_datetime(time_sample)

    fill_grid_with_power_values(time_sample)

    pp.runpp(self.grid.net, algorithm='nr', init='results', max_iteration=30, tolerance_mva=1e-6)

    pf_res_plotly(self.grid.net, aspectratio=(1,1))


  def plot_grid_2(self):
    time_sample = pd.to_datetime('2017-05-26 14:00:00+02:00')
    colors = sns.color_palette()

    def run_pp(timestep):
      self.grid.net.sgen['p_mw'] = self.pv_p.loc[timestep].values
      self.grid.net.sgen['q_mvar'] = self.pv_q.loc[timestep].values
      self.grid.net.load['p_mw'] = self.load_p.loc[timestep].values
      self.grid.net.load['q_mvar'] = self.load_q.loc[timestep].values
      self.grid.net.storage['p_mw'] = self.storage_p.loc[timestep].values
      self.grid.net.ext_grid.vm_pu = self.v_pu_ext_grid.loc[timestep].values
      pp.runpp(self.grid.net, algorithm='nr', init='results', max_iteration=30, tolerance_mva=1e-6)

    net = self.grid.net
    bc = ppplt.create_bus_collection(net, buses=net.bus.index, patch_type='rect', size=.00005, color=colors[2], zorder=1)
    lc = ppplt.create_line_collection(net, lines=net.line.index, color='grey', zorder=2)
    tc = ppplt.create_trafo_collection(net, trafos=net.trafo.index, size=.0001, color=colors[1], zorder=3)

    run_pp(time_sample)

    buses_over = net.bus[net.res_bus.vm_pu > 1.05]
    bc_over = ppplt.create_bus_collection(net, buses=buses_over.index, patch_type='rect', size=.00005, color=colors[3], zorder=4)

    lines_over = net.line[net.res_line.loading_percent > 50]
    lc_over = ppplt.create_line_collection(net, lines=lines_over.index, color=colors[3], zorder=5)


    ppplt.draw_collections([bc, lc, tc, bc_over, lc_over])
    plt.show()


