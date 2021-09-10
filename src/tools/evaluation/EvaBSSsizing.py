import numpy as np 
import pandas as pd
from scipy.fft import fft, fftfreq

import pandapower as pp
from pandapower.plotting.plotly import simple_plotly
from pandapower.plotting.plotly import pf_res_plotly

import matplotlib.pyplot as plt
import seaborn as sns

# Handle date time conversions between pandas and matplotlib
from pandas.plotting import register_matplotlib_converters
register_matplotlib_converters()

import tools.tools as tt

#import BSS_sizing_helper as BSS_sizing

class EvaBSSsizing():
  
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
    #self.storage_soc = self.read_data(self.output_dir+'storage_state_of_charge_percent.csv') # in powerflow wird aktuell noch e_mwh an soc übergeben
    self.curtailed_power = self.read_data(self.output_dir+'curtailed_power_MW.csv')
    #self.storage_soc = self.read_data(self.output_dir+'storage_state_of_charge_percent.csv') # in powerflow wird aktuell noch e_mwh an soc übergeben

    self.n_HH = len(self.grid.load_index)

  ### Helper Methods ###
  def read_data(self, filename):
    data = pd.read_csv(filename, delimiter = ',', low_memory=False)
    data['timestamp'] = pd.to_datetime(data['timestamp'], utc=True)
    data = data.set_index('timestamp')
    return data


  ### calculate storage parameters ###
  def calculate_storage_sizing(self):
    print(' ')
    print('Hint: No Efficiency considered! No reactive power considered!')
    #print('Total installed PV-power: ' + str(self.grid.total_installed_pv_power) + ' kW')

  def bss_sizing_trafo(self):
    # Sizing according to maximum transformer load
    p_res = self.trafo_p
    p_res_pos = 0*p_res
    p_res_neg = 0*p_res
    p_res_pos[p_res > 0]  = p_res
    p_res_neg[p_res <= 0] = p_res

    e_pos = p_res_pos.resample('1D').sum()*self.grid.time_scope['intervall_in_seconds']/3600 # in MWh
    e_neg   = p_res_neg.resample('1D').sum()*self.grid.time_scope['intervall_in_seconds']/3600 # in MWh

    '''
    fig, ax = plt.subplots()
    ax.stem(e_pos)
    ax.stem(e_neg)
    ax.set_xlabel('Time')
    ax.set_ylabel(' ')
    plt.show()
    '''

    p_res_pos_max = p_res.max()
    p_res_neg_max = p_res.min()

    if abs(p_res_pos_max.values) > abs(p_res_neg_max.values):
      p_max = abs(p_res_pos_max.values) - self.grid.net.trafo.sn_mva.values
    else:
      p_max = abs(p_res_neg_max.values) - self.grid.net.trafo.sn_mva.values

    if p_max < 0:
      p_max[0] = 0

    p_res_pos_overload = p_res - self.grid.net.trafo.sn_mva.values
    p_res_neg_overload = p_res + self.grid.net.trafo.sn_mva.values

    p_res_pos_overload[p_res_pos_overload < 0] = 0
    p_res_neg_overload[p_res_neg_overload > 0] = 0
    '''
    fig, ax = plt.subplots()
    ax.plot(p_res_pos_overload)
    ax.plot(p_res_neg_overload)
    ax.set_xlabel('Time')
    ax.set_ylabel(' ')
    plt.show()
    '''

    e_load = p_res_pos_overload.resample('1D').sum()*self.grid.time_scope['intervall_in_seconds']/3600 # in MWh
    e_pv   = p_res_neg_overload.resample('1D').sum()*self.grid.time_scope['intervall_in_seconds']/3600 # in MWh

    '''
    fig, ax = plt.subplots()
    ax.plot(p_res_pos_overload)
    ax.plot(p_res_neg_overload)
    ax.set_xlabel('Time')
    ax.set_ylabel(' ')
    plt.show()
    '''

    if abs(e_load).max().values > abs(e_pv).max().values:
      e_max = abs(e_load).max().values
    else:
      e_max = abs(e_pv).max().values

    print('')
    print('Sizing according to maximum transformer load:')
    print('P_max total: ' + str((p_max[0]*1000).round(2)) + ' kW')
    print('E_max total: ' + str((e_max[0]*1000).round(2)) + ' kWh')
    print('P_max per HH: ' + str((p_max[0]*1000/self.n_HH).round(2)) + ' kW')
    print('E_max per HH: ' + str((e_max[0]*1000/self.n_HH).round(2)) + ' kWh')

  def bss_sizing_line(self):
    pass

  def bss_sizing_voltage(self):
    # Sizing according to maximum voltage violation
    def calculate_sum_resistence(net, feeder, i_feeder):
       bus_trafo = int(net.trafo.lv_bus.values)
       bus_distances = pp.topology.calc_distance_to_bus(net, bus_trafo)
       feeder['buses_in_feeder'].l_sum.loc[i_feeder] = bus_distances.loc[feeder['buses_in_feeder'].buses.loc[i_feeder]].sum() # km
       return feeder

    def calculate_max_v_deviation(net, feeder, i_feeder):
       feeder['buses_in_feeder'].dv_max.loc[i_feeder] = net.res_bus.vm_pu.loc[feeder['buses_in_feeder'].buses.loc[i_feeder]].max() - 1.1
       feeder['buses_in_feeder'].bus_dv_max.loc[i_feeder] = int(net.res_bus.vm_pu.loc[feeder['buses_in_feeder'].buses.loc[i_feeder]].idxmax())
       if feeder['buses_in_feeder'].dv_max.loc[i_feeder] < 0:
         feeder['buses_in_feeder'].dv_max.loc[i_feeder] = 0
       return feeder

    def calculate_BSS_power(net, feeder, i_feeder):
       v_ref = net.bus.vn_kv[0] # .4 kV
       rho = (net.line.r_ohm_per_km[0]**2 + net.line.x_ohm_per_km[0]**2)**.5 # Ohm/km
       alpha = v_ref/rho # MAm = m/(W*V)
       if BESS_pos == 0:
         feeder['buses_in_feeder'].p_bss.loc[i_feeder] = alpha * feeder['buses_in_feeder'].dv_max.loc[i_feeder]*v_ref / (feeder['buses_in_feeder'].l_sum.loc[i_feeder]) # MAm*kV/km = MW
       elif BESS_pos == 1:
         bus_trafo = int(net.trafo.lv_bus.values)
         bus_distances = pp.topology.calc_distance_to_bus(net, bus_trafo)
         bus_dist = bus_distances.loc[feeder['buses_in_feeder'].bus_dv_max.loc[i_feeder]]
         feeder['buses_in_feeder'].p_bss.loc[i_feeder] = alpha * feeder['buses_in_feeder'].dv_max.loc[i_feeder]*v_ref / bus_dist # MAm*kV/km = MW
       return feeder

    def set_bss_power(net, feeder, i_feeder):
       if BESS_pos == 0:
         net.storage.p_mw[feeder['storage_index_in_feeder'].loc[i_feeder]['storage_index']] += feeder['buses_in_feeder'].p_bss.loc[i_feeder]
       elif BESS_pos == 1:
         index = net.storage[net.storage.bus.isin([int(feeder['buses_in_feeder'].loc[i_feeder]['bus_dv_max'])])].index
         net.storage.p_mw[index] += feeder['buses_in_feeder'].p_bss.loc[i_feeder]
       return net

    def load_scenario_output_data():
      # check if scenario 4 exists and load data
      if self.output_dir:
         try:
           self.v_pu = tt.read_data(self.output_dir + 'res_bus_vm_pu.csv')
           self.ll = tt.read_data(self.output_dir+'res_line_load_percent.csv')
           self.tl = tt.read_data(self.output_dir+'res_trafo_load_percent.csv')
           self.load_p = tt.read_data(self.output_dir+'load_active_power_MW.csv')
           self.load_q = tt.read_data(self.output_dir+'load_reactive_power_MW.csv')
           self.pv_p = tt.read_data(self.output_dir+'pv_active_power_MW.csv')
           self.pv_q = tt.read_data(self.output_dir+'pv_reactive_power_MW.csv')
           self.v_pu_ext_grid = tt.read_data(self.output_dir+'v_pu_ext_grid.csv')
         except:
           raise KeyError('Run first Scenario 4')         
      else:
         raise KeyError('Run first Scenario 4')

    def fill_grid_with_power_values(timestep):
      self.grid.net.sgen['p_mw'] = self.pv_p.loc[timestep].values
      self.grid.net.sgen['q_mvar'] = self.pv_q.loc[timestep].values
      self.grid.net.load['p_mw'] = self.load_p.loc[timestep].values
      self.grid.net.load['q_mvar'] = self.load_q.loc[timestep].values
      self.grid.net.ext_grid.vm_pu = self.v_pu_ext_grid.loc[timestep].values

    load_scenario_output_data()

    for i_feeder in range(1,self.grid.feeder['n_feeder']+1):
      self.grid.feeder = calculate_sum_resistence(self.grid.net, self.grid.feeder, i_feeder)

    BESS_pos = 0 # 0: HH, 1: Community storage

    time = self.v_pu.index

    self.storage_p = pd.DataFrame(index=time, columns=self.grid.net.storage.index).fillna(0)

    for timestep in time:
      v_max = self.v_pu.loc[timestep].max()
      if v_max > 1.1:
        self.grid.net.storage.p_mw = 0.
        bus_v_max = int(self.v_pu.loc[timestep].idxmax())
        fill_grid_with_power_values(timestep)
        pp.runpp(self.grid.net)
        i = 0
        while v_max > 1.1:
          i_feeder = self.grid.net.bus.feeder.loc[bus_v_max]
          self.grid.feeder = calculate_max_v_deviation(self.grid.net, self.grid.feeder, i_feeder)
          self.grid.feeder = calculate_BSS_power(self.grid.net, self.grid.feeder, i_feeder)
          self.grid.net = set_bss_power(self.grid.net, self.grid.feeder, i_feeder)
          pp.runpp(self.grid.net)
          v_max = self.grid.net.res_bus.vm_pu.max()
          bus_v_max = self.grid.net.res_bus.vm_pu.idxmax()
          i += 1
        #print(str(timestep) + ' Durchläufe: ' + str(i) + ' Total BSS Power: ' + str(self.grid.net.storage.p_mw.sum()))
        self.storage_p.loc[timestep] = self.grid.net.storage.p_mw
    
    p_bss = self.storage_p.sum(axis=1).max()*1000
    e_bss = self.storage_p.resample('1D').sum()*self.grid.time_scope['intervall_in_seconds']/3600 # in MWh
    e_bss = e_bss.sum(axis=1).max()*1000
    #pf_res_plotly(self.grid.net, aspectratio=(1,1))

    print('')
    print('Sizing according to maximum voltage violation:')
    print('P_max total: ' + str((p_bss).round(2)) + ' kW')
    print('E_max total: ' + str((e_bss).round(2)) + ' kWh')
    print('P_max per HH (on average): ' + str((p_bss/self.n_HH).round(2)) + ' kW')
    print('E_max per HH (on average): ' + str((e_bss/self.n_HH).round(2)) + ' kWh')

  def bss_sizing_pv(self):
    # Sizing according to installed PV power
    ratio = 1  # kWh_BSS/kW_PV
    c_rate = 1 # kW_BSS/kWh_BSS
    
    e_bss = self.grid.net.sgen['installed_power']*ratio
    p_bss = e_bss*c_rate

    print('')
    print('Sizing according to installed PV power:')
    print('P_max total: ' + str((p_bss.sum()).round(2)) + ' kW')
    print('E_max total: ' + str((e_bss.sum()).round(2)) + ' kWh')
    print('P_max per HH (on average): ' + str((p_bss.sum()/self.n_HH).round(2)) + ' kW')
    print('E_max per HH (on average): ' + str((e_bss.sum()/self.n_HH).round(2)) + ' kWh')

  def bss_sizing_fft(self):
    # Sizing according to FFT-Analysis

    p_res = self.trafo_p
    sample_rate = 1/self.grid.time_scope['intervall_in_seconds'] # in Hz
    duration = len(p_res)*self.grid.time_scope['intervall_in_seconds'] # in seconds

    # Number of sample points
    N = sample_rate*duration

    # sample spacing
    T = 1/sample_rate

    y = p_res['0'].to_numpy()

    yf = fft(y)
    yf = 2/N*np.abs(yf[0:int(N)//2])

    xf = fftfreq(int(N), T)[:int(N)//2]*3600*24

    '''
    fig, ax = plt.subplots()
    plt.semilogx(1/xf[1:], yf[1:]*1000, marker='o')
    ax.set_xlabel('Period T in days')
    ax.set_ylabel('Power in kW')
    plt.grid()
    plt.show()
    '''

    p_res_f = pd.DataFrame(columns=['1/xf', 'yf'])
    p_res_f['1/xf'] = 1/xf[1:]
    p_res_f['yf'] = yf[1:]
    p_res_f = p_res_f.set_index('1/xf')

    p_bss_index = p_res_f.idxmax()
    p_bss = p_res_f.loc[p_bss_index].values
    T_period = 24 # h
    e_bss = p_bss*T_period/np.pi

    print('')
    print('Sizing according to Fourier Analysis:')
    print('P_max total: ' + str(float((p_bss*1000).round(2))) + ' kW')
    print('E_max total: ' + str(float((e_bss*1000).round(2))) + ' kWh')
    print('P_max per HH (on average): ' + str(float((p_bss*1000/self.n_HH).round(2))) + ' kW')
    print('E_max per HH (on average): ' + str(float((e_bss*1000/self.n_HH).round(2))) + ' kWh')
    
    print(' ')
    print('Total installed PV Power: ' + str(self.grid.total_installed_pv_power) + ' kW')

