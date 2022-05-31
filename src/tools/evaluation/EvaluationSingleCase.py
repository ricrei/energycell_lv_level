import numpy as np 
import pandas as pd
from scipy.fft import fft, fftfreq

import pandapower as pp
from pandapower.plotting.plotly import simple_plotly
from pandapower.plotting.plotly import pf_res_plotly
import pandapower.plotting as ppplt

import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import seaborn as sns

# Handle date time conversions between pandas and matplotlib
from pandas.plotting import register_matplotlib_converters
register_matplotlib_converters()

import tools.tools as tt

#import BSS_sizing_helper as BSS_sizing

class EvaluationSingleCase():
  
  def __init__(self, grid, output_dir, net_name, scenario, time_scope, save_full_data): 
    self.grid = grid
    self.output_dir = output_dir
    self.net_name = net_name
    self.scenario = scenario
    self.time_scope = time_scope

    self.v = self.read_data(self.output_dir+'res_bus_vm_pu.csv')
    self.ll = self.read_data(self.output_dir+'res_line_load_percent.csv')
    self.tl = self.read_data(self.output_dir+'res_trafo_load_percent.csv')
    self.power = self.read_data(self.output_dir+'power_total_MW.csv')
    self.curtailed_power = self.read_data(self.output_dir+'curtailed_power_MW.csv')
    self.curtailed_power_pv = pd.DataFrame(columns=self.curtailed_power.columns, index=self.curtailed_power.index).fillna(0)
    self.curtailed_power_load = pd.DataFrame(columns=self.curtailed_power.columns, index=self.curtailed_power.index).fillna(0)
    self.curtailed_power_pv[self.curtailed_power >= 0] = self.curtailed_power[self.curtailed_power >= 0]
    self.curtailed_power_load[self.curtailed_power < 0] = -self.curtailed_power[self.curtailed_power < 0]
    self.losses_p = self.read_data(self.output_dir+'losses_active_power_MW.csv')
    self.storage_p = self.read_data(self.output_dir+'storage_active_power_MW.csv')
    self.storage_soc = self.read_data(self.output_dir+'storage_state_of_charge_percent.csv') # in powerflow wird aktuell noch e_mwh an soc übergeben
    self.trafo_p = self.read_data(self.output_dir+'trafo_active_power_MW.csv')
    self.pv_p = self.read_data(self.output_dir+'pv_active_power_MW.csv')
    self.load_p = self.read_data(self.output_dir+'load_active_power_MW.csv')
    self.bss_p_flex = self.read_data(self.output_dir+'bss_active_power_flex_MW.csv')
    self.load_p_flex = self.read_data(self.output_dir+'load_active_power_flex_MW.csv')
    if save_full_data == True:
      self.pv_q = self.read_data(self.output_dir+'pv_reactive_power_MW.csv')
      self.load_q = self.read_data(self.output_dir+'load_reactive_power_MW.csv')
      self.ev_soc = self.read_data(self.output_dir+'ev_soc.csv')
      self.v_pu_ext_grid = self.read_data(self.output_dir+'v_pu_ext_grid.csv')
      self.storage_e_mwh = self.read_data(self.output_dir+'storage_energy_content_MWh.csv')
      self.hp_soc = self.read_data(self.output_dir+'hp_soc.csv')
      self.hp_demand_th = self.read_data(self.output_dir+'hp_demand_th.csv')
      self.hp_cop = self.read_data(self.output_dir+'hp_cop.csv')
      self.hp_hp_th = self.read_data(self.output_dir+'hp_hp_th.csv')
      self.hp_tes_th = self.read_data(self.output_dir+'hp_tes_th.csv')
      self.hp_tes_losses_th = self.read_data(self.output_dir+'hp_tes_losses_th.csv')

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
  def plot_residualload(self, add_curtail, add_losses):
    prop_cycle = plt.rcParams['axes.prop_cycle']
    c = prop_cycle.by_key()['color']

    power = self.power*1000
    curtailed_pv = self.curtailed_power_pv.sum(axis=1)*1000
    curtailed_load = self.curtailed_power_load.sum(axis=1)*1000
    curtailed = pd.DataFrame()
    curtailed['curtail_pv'] = curtailed_pv
    curtailed['curtail_load'] = curtailed_load
    #try:
    losses = self.losses_p.sum(axis=1)*1000
    #except:
    #  losses = curtailed['curtail_pv']*0
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
    if add_losses:
      ax.fill_between(power.index, power.hp + power.load + power.ev + storage_charge, power.hp + power.load + power.ev + storage_charge + losses, alpha=0.7, color=c[8])

    ax.plot(power.index, -storage_discharge-power.pv, lw=.6)
    ax.plot(power.index, storage_charge+power.ev, lw=.6)
    ax.plot(power.index, storage_charge+power.load+power.ev, lw=.6)
    ax.plot(power.index, storage_charge+power.hp+power.load+power.ev, lw=.6)
    ax.plot(storage.index, storage_charge    , lw=.6)
    ax.plot(storage.index, -storage_discharge, lw=.6)
    if add_losses:
      ax.plot(power.index, storage_charge+power.hp+power.load+power.ev + losses, color=c[8], lw=.6)

    #power = self.shorted_data(power, '1H')
    #storage = self.shorted_data(storage, '1H')

    if add_losses:
      ax.plot(power.index, -power.pv+power.hp+power.load+power.ev-storage_sum+losses, color='black', lw=.5)
    else:
      ax.plot(power.index, -power.pv+power.hp+power.load+power.ev-storage_sum, color='black', lw=.5)

    ax.set_xlabel('Time')
    ax.set_ylabel('Power in kW')
    '''
    patch_list = [
         mpatches.Patch(color=c[0], alpha=0.7, label='Photovoltaic generation'),
         mpatches.Patch(color=c[1], alpha=0.7, label='E-vehicle load'),
         mpatches.Patch(color=c[2], alpha=0.7, label='Household load'),
         mpatches.Patch(color=c[3], alpha=0.7, label='Heat pump load'),
         mpatches.Patch(color=c[4], alpha=0.7, label='Storage'),
         mpatches.Patch(color=c[0], alpha=0.7, label='Curtailed energy'),
         mpatches.Patch(color=c[8], alpha=0.7, label='Line and trafo losses')
                 ]
    '''

    if add_curtail and add_losses:
      patch_list = [
         mpatches.Patch(color=c[0], alpha=0.7, label='Photovoltaic generation'),
         mpatches.Patch(color=c[1], alpha=0.7, label='E-vehicle load'),
         mpatches.Patch(color=c[2], alpha=0.7, label='Household load'),
         mpatches.Patch(color=c[3], alpha=0.7, label='Heat pump load'),
         mpatches.Patch(color=c[4], alpha=0.7, label='Storage'),
         mpatches.Patch(color=c[0], alpha=0.2, label='Curtailed energy'),
         mpatches.Patch(color=c[8], alpha=0.7, label='Line and trafo losses')
                 ]
      plt.legend(handles=patch_list)

    if not add_curtail and add_losses:
      patch_list = [
         mpatches.Patch(color=c[0], alpha=0.7, label='Photovoltaic generation'),
         mpatches.Patch(color=c[1], alpha=0.7, label='E-vehicle load'),
         mpatches.Patch(color=c[2], alpha=0.7, label='Household load'),
         mpatches.Patch(color=c[3], alpha=0.7, label='Heat pump load'),
         mpatches.Patch(color=c[4], alpha=0.7, label='Storage'),
         mpatches.Patch(color=c[8], alpha=0.7, label='Line and trafo losses')
                 ]
      plt.legend(handles=patch_list)

    if add_curtail and not add_losses:
      patch_list = [
         mpatches.Patch(color=c[0], alpha=0.7, label='Photovoltaic generation'),
         mpatches.Patch(color=c[1], alpha=0.7, label='E-vehicle load'),
         mpatches.Patch(color=c[2], alpha=0.7, label='Household load'),
         mpatches.Patch(color=c[3], alpha=0.7, label='Heat pump load'),
         mpatches.Patch(color=c[4], alpha=0.7, label='Storage'),
         mpatches.Patch(color=c[0], alpha=0.2, label='Curtailed energy')
                 ]
      plt.legend(handles=patch_list)

    if not add_curtail and not add_losses:
      patch_list = [
         mpatches.Patch(color=c[0], alpha=0.7, label='Photovoltaic generation'),
         mpatches.Patch(color=c[1], alpha=0.7, label='E-vehicle load'),
         mpatches.Patch(color=c[2], alpha=0.7, label='Household load'),
         mpatches.Patch(color=c[3], alpha=0.7, label='Heat pump load'),
         mpatches.Patch(color=c[4], alpha=0.7, label='Storage')
                 ]
      plt.legend(handles=patch_list)

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
    curtail_pv = self.curtailed_power_pv.sum(axis=1)
    curtail_load = self.curtailed_power_load.sum(axis=1)
    curtail_p = pd.DataFrame()
    curtail_p['curtail_pv'] = curtail_pv
    curtail_p['curtail_load'] = curtail_load

    if self.time_scope['t_freq'] != None:#'1D':
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

  ### calculate residualload to determine max, min and balanced residualload week ###
  def calculate_resi_week(self):
    '''
    Only suited for 2017-01-01_2018-01-01_1D
    '''
    self.power['total_load'] = self.power.load + self.power.hp + self.power.ev
    self.power['res_load'] = self.power.total_load - self.power.pv
    self.power['sevenday'] = 0

    j = 0
    for i in self.power.index:
     for k in range(7):
      try:
       self.power['sevenday'].iloc[j] += self.power.res_load.iloc[j+k]
      except:
       self.power['sevenday'].iloc[j] += self.power.res_load.iloc[k]
     j += 1

    #print(self.power['sevenday'].tail(90))
    #print(self.power.iloc[270:320])

    print(self.power.loc[(self.power['sevenday'] > -.05) & (self.power['sevenday'] < .05), 'sevenday'])
    print(self.power['sevenday'].idxmax())
    print(self.power['sevenday'].max())
    print(self.power['sevenday'].idxmin())
    print(self.power['sevenday'].min())

    plt.figure()
    plt.plot(self.power['sevenday'])
    plt.show()

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
    fig, ax = plt.subplots()
    line = ax.plot(self.pv_q)
    plt.xlabel('Time')
    plt.ylabel('PV reactive power in MW')
    plt.grid(True)
    plt.show()


  def plot_pv_reactive_power2(self, grid):
    p = self.pv_p
    q = self.pv_q
    v = self.v
    cos_phi = (p/(p**2 + q**2)**(1/2)).fillna(1.)
    columns = q.columns

    v_new = pd.DataFrame(columns=q.columns)

    for pv in grid.net.sgen.index:
      v_new[str(pv)] = v[str(grid.net.sgen.bus.loc[pv])]

    fig, (ax1, ax2, ax3) = plt.subplots(3)
    fig.suptitle(' ')
    ax1.plot(v_new)[0]
    ax2.plot(q)[0]
    ax3.plot(cos_phi)[0]
    ax1.set_ylabel('Voltage in p.u.')
    ax2.set_ylabel('Reactive power in Mvar')
    ax3.set_ylabel('cos(phi)')
    ax3.set_xlabel('Time')
    #plt.show()

    bus = ['65', '13', '73', '90']

    fig, ax = plt.subplots()

    #for c in bus:    
    for c in columns:
      try:
        ax.plot(v_new[c], q[c], '*')
      except:
        pass
    
    #ax.plot(v[bus], q[bus], '*-')
    ax.set_ylabel('Reactive power in Mvar')
    ax.set_xlabel('Voltage in p.u.')
    ax.legend(bus)
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
    
  def plot_bss_e_mwh(self):
    e_mwh = self.storage_e_mwh
    fig, ax = plt.subplots()
    ax.plot(e_mwh.index, e_mwh)
    ax.set_xlabel('Time')
    ax.set_ylabel('Energy content in MWh')
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
    bss_p = self.storage_p
    fig, ax = plt.subplots()
    ax.plot(bss_p.index, bss_p)
    ax.set_xlabel('Time')
    ax.set_ylabel('Power in MW')
    plt.show()
    
  def plot_hp_soc(self):
    soc = self.hp_soc
    fig, ax = plt.subplots()
    ax.plot(soc.index, soc)
    ax.set_xlabel('Time')
    ax.set_ylabel('State of charge MWh')
    plt.show()

  def plot_hp_cop(self):
    cop = self.hp_cop
    fig, ax = plt.subplots()
    ax.plot(cop.index, cop)
    ax.set_xlabel('Time')
    ax.set_ylabel('coefficent of performance - COP')
    plt.show()
    
  def plot_hp_active_power(self):
    fig, ax = plt.subplots()
    for i in self.grid.hp_index:
      ax.plot(self.load_p[str(i)])
    ax.set_xlabel('Time')
    ax.set_ylabel('hp_el_demand in MW')
    #plt.legend(grid.component_buses.index)
    plt.show()

  def plot_hp_eva_th(self):
    prop_cycle = plt.rcParams['axes.prop_cycle']
    c = prop_cycle.by_key()['color']

    bus = str(self.hp_demand_th.columns[2])
    result = self.hp_hp_th - self.hp_demand_th - self.hp_tes_th - self.hp_tes_losses_th

    fig, ax = plt.subplots()
    ax.plot(result)
    ax.set_xlabel('Time')
    ax.set_ylabel('Thermal Power Deviation in MW\n(should be near zero)')
    #plt.show()

    fig, ax = plt.subplots()
    ax.plot(self.hp_demand_th[bus])
    ax.plot(-self.hp_hp_th[bus])
    ax.plot(self.hp_tes_th[bus])
    ax.plot(self.hp_tes_losses_th[bus])
    ax.set_xlabel('Time')
    ax.set_ylabel('Thermal Power in MW')
    plt.legend(['Demand', 'HP', 'TES', 'TES losses'])
    #plt.show()

    hp_tes_gen = self.hp_tes_th*0
    hp_tes_con = self.hp_tes_th*0
    hp_tes_gen[self.hp_tes_th < 0] = self.hp_tes_th[self.hp_tes_th < 0]
    hp_tes_con[self.hp_tes_th > 0] = self.hp_tes_th[self.hp_tes_th > 0]
    hp_tes_gen = hp_tes_gen.sum(axis=1)
    hp_tes_con = hp_tes_con.sum(axis=1)
    hp_hp_th = self.hp_hp_th.sum(axis=1)
    hp_tes_losses_th = self.hp_tes_losses_th.sum(axis=1)
    hp_demand_th = self.hp_demand_th.sum(axis=1)

    fig, ax = plt.subplots()
    # Consumption
    ax.fill_between(hp_demand_th.index, 0                      , hp_demand_th                            , alpha=0.7, color=c[0])
    ax.fill_between(hp_demand_th.index, hp_demand_th           , hp_demand_th+hp_tes_con                 , alpha=0.7, color=c[1])
    ax.fill_between(hp_demand_th.index, hp_demand_th+hp_tes_con, hp_demand_th+hp_tes_con+hp_tes_losses_th, alpha=0.7, color=c[2])
    # Production
    ax.fill_between(hp_demand_th.index, 0                      , -hp_hp_th                               , alpha=0.7, color=c[3])
    ax.fill_between(hp_demand_th.index, -hp_hp_th              , -hp_hp_th+hp_tes_gen                    , alpha=0.7, color=c[1])
    #ax.plot(self.pv_p.sum(axis=1))
    patch_list = [
         mpatches.Patch(color=c[0], alpha=0.7, label='Demand'),
         mpatches.Patch(color=c[1], alpha=0.7, label='TES'),
         mpatches.Patch(color=c[2], alpha=0.7, label='TES losses'),
         mpatches.Patch(color=c[3], alpha=0.7, label='HP')
                 ]
    plt.legend(handles=patch_list)
    ax.set_xlabel('Time')
    ax.set_ylabel('Thermal Power in MW')
    plt.show()

  def plot_curtailed_power(self):
    fig, ax = plt.subplots()
    ax.plot(self.curtailed_power_load.sum(axis=1))
    ax.set_xlabel('Time')
    ax.set_ylabel('Curtailed power load in MW')

    fig, ax = plt.subplots()
    ax.plot(self.curtailed_power_pv.sum(axis=1))
    ax.set_xlabel('Time')
    ax.set_ylabel('Curtailed power pv in MW')

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


  def plot_flex_power(self):
    fig, ax = plt.subplots()
    ax.plot(self.bss_p_flex.sum(axis=1))
    ax.set_xlabel('Time')
    ax.set_ylabel('Flex bss power in MW')

    fig, ax = plt.subplots()
    ax.plot(self.load_p_flex.sum(axis=1))
    ax.set_xlabel('Time')
    ax.set_ylabel('Flex load power in MW')

    plt.show()

  def energyflow_on_HH_level(self):
    load_index = [str(i) for i in self.grid.load_index]
    hp_index = [str(i) for i in self.grid.hp_index]
    ev_index = [str(i) for i in self.grid.ev_index]

    # HP-load per HH
    hp_load = self.load_p[hp_index]
    hp_load.columns = load_index
    # EV-load per HH
    ev_load = self.load_p[ev_index]
    ev_load.columns = load_index
    # HH-load per HH
    hh_load = self.load_p[load_index]
    # PV per HH
    pv = self.pv_p
    # BSS per HH
    bss = self.storage_p
    bss_neg = pd.DataFrame(index=bss.index, columns=bss.columns).fillna(0)
    bss_pos = pd.DataFrame(index=bss.index, columns=bss.columns).fillna(0)
    bss_neg[bss < 0] = bss[bss < 0]
    bss_pos[bss > 0] = bss[bss > 0]
    # total losses
    losses = self.losses_p.sum(axis=1)

    # flex_pos and flex_neg contains partional self-consumed and locally traded energy
    # provided flexibility by:
    # discharging BSS (flex_neg) in times of trafo overload by consumers
    flex_neg = pd.DataFrame(index=self.bss_p_flex.index, columns=self.bss_p_flex.columns).fillna(0)
    flex_neg[self.bss_p_flex<0] = -self.bss_p_flex[self.bss_p_flex<0] # flex durch erzeugung
    # charging BSS, EV, TES (flex_pos) in times of trafo overload by pv power excess
    flex_pos = pd.DataFrame(index=self.bss_p_flex.index, columns=self.bss_p_flex.columns).fillna(0)
    flex_pos[self.bss_p_flex>0] = self.bss_p_flex[self.bss_p_flex>0] # flex durch last
    flex_pos += -self.load_p_flex

    # residual load per HH
    dE_HH = hh_load + hp_load + ev_load - pv + bss
    # residual load whole grid
    dE_LV = pd.DataFrame(index=dE_HH.index, columns=dE_HH.columns)
    for c in dE_LV.columns:
      dE_LV[c] = dE_HH.sum(axis=1)# + losses

    # Sum of all PV excess
    sum_PV_LV_excess = pd.DataFrame(index=dE_HH.index, columns=dE_HH.columns).fillna(0)
    sum_Con_LV_lack = pd.DataFrame(index=dE_HH.index, columns=dE_HH.columns).fillna(0)
    for c in dE_LV.columns:
      sum_PV_LV_excess[c] = dE_HH[dE_HH < 0].sum(axis=1) # PV Überschuss gesamtes Netz
      sum_Con_LV_lack[c] = dE_HH[dE_HH >= 0].sum(axis=1) # Lastüberschuss gesamtes Netz

    # create
    Ec_MV = pd.DataFrame(index=pv.index, columns=pv.columns).fillna(0)
    Ec_LV = pd.DataFrame(index=pv.index, columns=pv.columns).fillna(0)
    Ec_self = pd.DataFrame(index=pv.index, columns=pv.columns).fillna(0)
    Eg_self = pd.DataFrame(index=pv.index, columns=pv.columns).fillna(0)
    Eg_LV = pd.DataFrame(index=pv.index, columns=pv.columns).fillna(0)
    Eg_MV = pd.DataFrame(index=pv.index, columns=pv.columns).fillna(0)
    Ecur_load = self.curtailed_power_load
    Ecur_pv = self.curtailed_power_pv


    ### Aufteilen in wieviel des Verbrauchs wird aus PV gedeckt und wieviel aus Speicher
    ### Aufteilen in wieviel der Erzegung geht in Last und wieviel in Speicher
    ### Anschließend Flexibilität aufteilen in, wieviel kommt aus dem Speicher und wieviel aus der Last

    # if PV gen greater than con -> calculate self consumption
    Ec_self[dE_HH < 0] = hh_load[dE_HH < 0] + hp_load[dE_HH < 0] + ev_load[dE_HH < 0]
    Eg_self[dE_HH < 0] = hh_load[dE_HH < 0] + hp_load[dE_HH < 0] + ev_load[dE_HH < 0] + bss_pos[dE_HH < 0]
    Ec_MV[dE_HH < 0] = 0
    Ec_LV[dE_HH < 0] = 0
    Eg_MV[(dE_HH < 0) & (dE_LV >= 0)] = 0
    Eg_LV[(dE_HH < 0) & (dE_LV >= 0)] = dE_HH[(dE_HH < 0) & (dE_LV >= 0)]
    Eg_MV[(dE_HH < 0) & (dE_LV < 0)] = dE_HH[(dE_HH < 0) & (dE_LV < 0)] / sum_PV_LV_excess[(dE_HH < 0) & (dE_LV < 0)] * dE_LV[(dE_HH < 0) & (dE_LV < 0)]
    Eg_LV[(dE_HH < 0) & (dE_LV < 0)] = dE_HH[(dE_HH < 0) & (dE_LV < 0)] / sum_PV_LV_excess[(dE_HH < 0) & (dE_LV < 0)] * (sum_PV_LV_excess[(dE_HH < 0) & (dE_LV < 0)] - dE_LV[(dE_HH < 0) & (dE_LV < 0)])

    # if PV gen lower than con -> calculate self consumption
    Ec_self[dE_HH >= 0] = - pv[dE_HH >= 0] + bss_neg[dE_HH >= 0]
    Eg_self[dE_HH >= 0] = - pv[dE_HH >= 0]
    Ec_MV[(dE_HH >= 0) & (dE_LV >= 0)] = dE_HH[(dE_HH >= 0) & (dE_LV >= 0)] / sum_Con_LV_lack[(dE_HH >= 0) & (dE_LV >= 0)] * dE_LV[(dE_HH >= 0) & (dE_LV >= 0)]
    Ec_LV[(dE_HH >= 0) & (dE_LV >= 0)] = dE_HH[(dE_HH >= 0) & (dE_LV >= 0)] / sum_Con_LV_lack[(dE_HH >= 0) & (dE_LV >= 0)] * (sum_Con_LV_lack[(dE_HH >= 0) & (dE_LV >= 0)] - dE_LV[(dE_HH >= 0) & (dE_LV >= 0)])
    Ec_MV[(dE_HH >= 0) & (dE_LV < 0)] = 0
    Ec_LV[(dE_HH >= 0) & (dE_LV < 0)] = dE_HH[(dE_HH >= 0) & (dE_LV < 0)]
    Eg_MV[dE_HH >= 0] = 0
    Eg_LV[dE_HH >= 0] = 0

    Ec_self = abs(Ec_self)
    Eg_self = abs(Eg_self)

    '''
    fig, ax = plt.subplots()
    for i in ['7']:#Ec_LV.columns:
      ax.plot(flex_pos[i])
    ax.set_xlabel('Time')
    ax.set_ylabel('dP of each HH in MW')
    plt.show()
    '''


    #'''    
    ### Calculate how much of the pos and neg flexibility is included in self-sonsumption and locally traded energy
    Eflex_in_Ec_self = pd.DataFrame(index=dE_HH.index, columns=dE_HH.columns).fillna(0)
    Eflex_in_Ec_LV = pd.DataFrame(index=dE_HH.index, columns=dE_HH.columns).fillna(0)
    Eflex_in_Eg_LV = pd.DataFrame(index=dE_HH.index, columns=dE_HH.columns).fillna(0)
    # case: PV excess, if only own pv energy is consumed
    Eflex_in_Ec_self[flex_pos <= Ec_self] = flex_pos[flex_pos <= Ec_self]
    Eflex_in_Ec_LV[flex_pos <= Ec_self] = 0
    # case: PV excess, if own pv energy and pv energy from community is consumed
    Eflex_in_Ec_self[flex_pos > Ec_self] = Ec_self[flex_pos > Ec_self]
    Eflex_in_Ec_LV[flex_pos > Ec_self] = flex_pos[flex_pos > Ec_self] - Ec_self[flex_pos > Ec_self]
    # case: Load excess, if only own load energy is covered
    Eflex_in_Ec_self[flex_neg <= Ec_self] += flex_neg[flex_neg <= Ec_self]
    Eflex_in_Eg_LV[flex_neg <= Ec_self] = 0
    # case: Load excess, if own load energy and load energy from community is covered
    Eflex_in_Ec_self[flex_neg > Ec_self] += Ec_self[flex_neg > Ec_self]
    Eflex_in_Eg_LV[flex_neg > Ec_self] = flex_neg[flex_neg > Ec_self] - Ec_self[flex_neg > Ec_self]
    #'''


    E = pd.DataFrame(index=Ec_self.columns)

    E['Ec_self'] = Ec_self.sum()
    E['Eg_self'] = Eg_self.sum()
    E['Ec_MV'] = Ec_MV.sum()
    E['Ec_LV'] = Ec_LV.sum()
    E['Eg_MV'] = abs(Eg_MV).sum()
    E['Eg_LV'] = abs(Eg_LV).sum()
    E['Ecur_pv'] = Ecur_pv.sum()
    E['Ecur_load'] = Ecur_load.sum()
    #E['Ec_flex'] = Eflex_pos.sum()
    #E['Eg_flex'] = Eflex_neg.sum()

    # Bilanzcheck
    #print((abs(Ec_self) + abs(Ec_MV) + abs(Ec_LV) - (hh_load + hp_load + ev_load + bss_pos)))
    #print((abs(Ec_self) + abs(Ec_MV) + abs(Ec_LV) - (hh_load + hp_load + ev_load + bss_pos)))
    #print((abs(Ec_self) + abs(Eg_MV) + abs(Eg_LV) - (pv - bss_neg)))
    #print('Consumption (incl. BSS): ' + str(((E.sum(axis=0).Ec_self + E.sum(axis=0).Ec_MV + E.sum(axis=0).Ec_LV)/60).round(3)) + ' MWh')
    #print('Generation (incl. BSS) : ' + str(((E.sum(axis=0).Ec_self + E.sum(axis=0).Eg_MV + E.sum(axis=0).Eg_LV)/60).round(3)) + ' MWh')

    #'''
    # Plot PV
    E_barplot1 = E
    E_barplot1['Eg_LV'] +=  E_barplot1['Eg_self']
    E_barplot1['Eg_MV'] +=  E_barplot1['Eg_LV']
    E_barplot1['Ecur_pv'] += E_barplot1['Eg_MV']
    #E_barplot1['Eg_flex'] += E_barplot1['Ecur_pv']
    for i in E_barplot1.index: # plot in percent
      E_barplot1.loc[i] = E_barplot1.loc[i] / E_barplot1['Ecur_pv'].loc[i] * 100
    #s5 = sns.barplot(x = E.index, y = 'Eg_flex', data = E_barplot1, color = 'grey')
    s4 = sns.barplot(x = E.index, y = 'Ecur_pv', data = E_barplot1, color = 'yellow')
    s3 = sns.barplot(x = E.index, y = 'Eg_MV', data = E_barplot1, color = 'green')
    s2 = sns.barplot(x = E.index, y = 'Eg_LV', data = E_barplot1, color = 'blue')
    s1 = sns.barplot(x = E.index, y = 'Eg_self', data = E_barplot1, color = 'red')
    Ecur_pv_bar = mpatches.Patch(color='yellow', label='curtailed')
    Eg_MV_bar = mpatches.Patch(color='green', label='MV feed-in')
    Eg_LV_bar = mpatches.Patch(color='blue', label='LV consumed')
    Ec_self_bar = mpatches.Patch(color='red', label='self consumed')
    plt.legend(handles=[Ecur_pv_bar, Eg_MV_bar, Eg_LV_bar, Ec_self_bar])
    plt.xlabel('Households')
    plt.ylabel('PV power in %')
    plt.show()

    # Plot load
    E_barplot2 = E
    E_barplot2['Ec_LV'] +=  E_barplot2['Ec_self']
    E_barplot2['Ec_MV'] +=  E_barplot2['Ec_LV']
    E_barplot2['Ecur_load'] +=  E_barplot2['Ec_MV']
    #E_barplot1['Ec_flex'] += E_barplot1['Ecur_load']
    for i in E_barplot2.index: # plot in percent
      E_barplot2.loc[i] = E_barplot2.loc[i] / E_barplot1['Ecur_load'].loc[i] * 100
    #s5 = sns.barplot(x = E.index, y = 'Ec_flex', data = E_barplot2, color = 'grey')
    s4 = sns.barplot(x = E.index, y = 'Ecur_load', data = E_barplot2, color = 'yellow')
    s3 = sns.barplot(x = E.index, y = 'Ec_MV', data = E_barplot2, color = 'green')
    s2 = sns.barplot(x = E.index, y = 'Ec_LV', data = E_barplot2, color = 'blue')
    s1 = sns.barplot(x = E.index, y = 'Ec_self', data = E_barplot2, color = 'red')
    Ecur_load_bar = mpatches.Patch(color='yellow', label='curtailed')
    Ec_MV_bar = mpatches.Patch(color='green', label='MV grid obtained')
    Ec_LV_bar = mpatches.Patch(color='blue', label='LV grid obtained')
    Ec_self_bar = mpatches.Patch(color='red', label='self consumed')
    plt.legend(handles=[Ecur_load_bar, Ec_MV_bar, Ec_LV_bar, Ec_self_bar])
    plt.xlabel('Households')
    plt.ylabel('Load power in %')
    plt.show()
    #'''

    # To-DO
    ## flexibility power tracken und aus verbrauch rausrechnen

    '''
    fig, ax = plt.subplots()
    ax.plot(dE_HH)
    ax.plot(self.tl/100)
    ax.set_xlabel('Time')
    ax.set_ylabel('dP of each HH in MW')
    plt.show()
    '''









