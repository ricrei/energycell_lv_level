import pandapower as pp
import pandapower.networks as pn
import simbench as sb

import pandas as pd
import numpy as np
import datetime

import sys

import tools.tools as tt

class Grid:

  def __init__(self, net_name, scenario, time_scope, control_parameter, grid_analysis):
    '''
    Init method to initialize and modify a pandapower network. 

    :param net_name: string
                Name of the network (see config-file)
    :param scenario: array of int 
                Scenario definition (see config-file)
    :param time_scope: dict of strings
                Containing the simulation start time, end time, and time resolution (see config-file)
    '''

    self.time_scope = time_scope
    self.scenario = scenario
    self.grid_analysis = grid_analysis
    if grid_analysis == False:
        self.ec_size = control_parameter['EC_size']

    #self.is_community_storage = True if self.scenario[2] in [3, 4] else False
    self.net_name = net_name
    if grid_analysis == True:
        #self.net_name = net_name
        self.create_net()
        pp.runpp(self.net, algorithm='nr')  # Has to be executed to get initial net.res_bus for Q(U)-control
    else:
        self.category = control_parameter['EC_demografic_category']
        if self.category not in ['rural','suburban','urban']:
            raise NameError('Hint: Selected category not valid. Please check EC_demografic_category')
        self.create_energycell_structure()

    self.curtailed_pv_power = 0
    self.curtailed_load_power = 0

    self.df_solar = tt.get_time_sun(self.time_scope)
    self.df_t_amb = tt.get_amb_temp(self.time_scope)

  ######################
  ### create network ###
  ######################
  def create_net(self):
        '''
        Load predefined grid with pandapower or simbench. Grid contains not generation units or sector coupled consumers. 

        '''
        # create net: load  only, without pv
        if self.net_name == "kerber_rural_1":
            self.net = pn.create_kerber_landnetz_freileitung_1()
            self.category = 'rural'
        elif self.net_name == "kerber_rural_2":
            self.net = pn.create_kerber_landnetz_freileitung_2()
            self.category = 'rural'
        elif self.net_name == "kerber_rural_3":
            self.net = pn.create_kerber_landnetz_kabel_1()
            self.category = 'rural'
        elif self.net_name == "kerber_rural_4":
            self.net = pn.create_kerber_landnetz_kabel_2()
            self.category = 'rural'
        elif self.net_name == "kerber_village":
            self.net = pn.create_kerber_dorfnetz()
            self.category = 'village'
        elif self.net_name == "kerber_suburb_1":
            self.net = pn.create_kerber_vorstadtnetz_kabel_1()
            self.category = 'suburban'
        elif self.net_name == "kerber_suburb_2":
            self.net = pn.create_kerber_vorstadtnetz_kabel_2()
            self.category = 'suburban'
        elif self.net_name == "simbench_rural_1":
            self.net = sb.get_simbench_net('1-LV-rural1--0-sw')
            self.category = 'rural'
            self.rename_all_buses()
        elif self.net_name == "simbench_rural_2":
            self.net = sb.get_simbench_net('1-LV-rural2--0-sw')
            self.category = 'rural'
            self.rename_all_buses()
        elif self.net_name == "simbench_rural_3":
            self.net = sb.get_simbench_net('1-LV-rural3--0-sw')
            self.category = 'rural'
            self.rename_all_buses()
        elif self.net_name == "simbench_suburb_4":
            self.net = sb.get_simbench_net('1-LV-semiurb4--0-sw')
            self.category = 'suburban'
            self.rename_all_buses()
        elif self.net_name == "simbench_suburb_5":
            self.net = sb.get_simbench_net('1-LV-semiurb5--0-sw')
            self.category = 'suburban'
            self.rename_all_buses()
        elif self.net_name == "simbench_urban_6":
            self.net = sb.get_simbench_net('1-LV-urban6--0-sw')
            self.category = 'urban'
            self.rename_all_buses()
        elif self.net_name == "test_net_one_load_branch":
            self.net = self.create_test_net_one_load_branch()
            self.category = 'rural'
        elif self.net_name == "test_net_n_load_branch":
            self.net = self.create_test_net_n_load_branch()
            self.category = 'rural'
        else:
            raise NameError('Hint: No Network found. Please check net_name')

        # Set vm_pu of external grid
        #print(self.net.ext_grid.vm_pu)
        self.net.ext_grid.vm_pu = 1.0

        # if there are any sgen's within the original network -> remove them first
        for index in self.net.sgen.index:
          self.net.sgen.drop(index=index, inplace=True)

        # needed to create HHL, HP, EV and BSS at each bus
        self.component_buses = self.net.load.bus

        self.s_trafo_power = self.net.trafo.sn_mva.sum()

        self.get_buses_per_feeder()

        # Run diagnostic if there are problems regarding powerflow
        #pp.diagnostic(self.net, report_style='detailed', warnings_only=False)

  def create_energycell_structure(self):
      '''
      An empty 'network' is created for simulations without a power grid.
      '''
      self.net = pp.create_empty_network() # Tabea ???

      #pp.create_transformer(self.net, hv_bus=9, lv_bus=10, std_type=['0.25 MVA 20/0.4 kV']) ###NEU!!!
      #self.net['trafo']['lv_bus'].loc[0]=100

      self.net['trafo']['p_mw'] = "" # so richtig und wird das gebraucht??? wird hier dann überhaupt die kummulierte Leistung eingespeichert?
      self.p_trafo_power = self.net.trafo.p_mw.sum() # wird das gebraucht?

      # add new row for each bus/household
      for x in range(self.ec_size):
          self.net.load.loc[x] = ''
          self.net.bus.loc[x] = ''
          self.net.load.bus.loc[x] = x

      # add new row for transformer #NEU
      n_busses = len(self.net.bus)
      self.net.trafo.loc[0] = ''
      self.net.trafo.lv_bus.loc[0] = n_busses
      self.net.bus.loc[n_busses] = ''
      self.net.trafo.hv_bus.loc[0] = n_busses + 1

      #pp.create_transformer(self.net, hv_bus=11, lv_bus=10,std_type=['0.25 MVA 20/0.4 kV'])  ###NEU!!!


      # needed to create HHL, HP, EV and BSS at each bus
      self.component_buses = self.net.load.bus

  def get_component_index(self):
        '''
        Method to store the index of generation and consumption units within class Grid.
        Call after generation and additional consumers are defined.
        '''
        self.pv_index = self.net.sgen.index
        self.load_index = self.net.load.index[self.net.load.type.str.contains('load')]
        self.hp_index = self.net.load.index[self.net.load.type.str.contains('hp')]
        self.ev_index = self.net.load.index[self.net.load.type.str.contains('ev')]
        self.bss_index = self.net.storage.index

  def get_label_of_each_component(self):
        '''
        Set labels for all gens and cons coresponding to the type unit.
        Necessary to allocate a load series to each gen and con unit.
        '''
        self.label_pv = self.net.sgen.type.loc[self.pv_index]
        self.label_pv_p = self.label_pv + '_p'
        self.label_pv_q = self.label_pv + '_q'

        self.label_load_p = [self.net.load.type[i] + '_p' for i in self.load_index]
        self.label_load_q = [self.net.load.type[i] + '_q' for i in self.load_index]

        self.label_hp_p = [self.net.load.type[i] + '_p' for i in self.hp_index]
        self.label_hp_q = [self.net.load.type[i] + '_q' for i in self.hp_index]

        self.label_ev = [self.net.load.type[i] for i in self.ev_index]

  def rename_all_buses(self):
    for i in self.net.bus.index:
      self.net.bus.name[i] = str(self.net.bus.subnet[i]) + ' Bus ' + str(i)
    for i in self.net.line.index:
      self.net.line.name[i] = str(self.net.bus.subnet[i]) + ' Line ' + str(i)

  def reset_all_power_values(self):
    self.net.load.p_mw = 0
    self.net.load.q_mvar = 0
    self.net.sgen.p_mw = 0
    self.net.sgen.q_mvar = 0
    self.net.storage.p_mw = 0
    self.net.storage.q_mvar = 0

    return self

  def get_vm_pu_ext_grid(self, grid):
    '''
    Returns the voltage in pu at the external grid.  
    considering the MV-grid valid voltage deviation of +-4%
    assuming that the voltage magnitute depends on the residual load

    :param grid: class Grid
    '''
    voltage_deviation_in_percent = .04
    nominal_voltage = 1.0
    residual_load = grid.net.load.p_mw.sum() - grid.net.sgen.p_mw.sum()
    voltage_deviation = -residual_load/(grid.total_installed_pv_power/1000)*voltage_deviation_in_percent

    return nominal_voltage + voltage_deviation

  # only use with 'grid-oriented feed-in damping'
  def get_residualload_s_sum(self):
    line_losses_p = self.net.res_line.pl_mw
    line_losses_q = self.net.res_line.ql_mvar
    trafo_losses_p = self.net.res_trafo.pl_mw
    trafo_losses_q = self.net.res_trafo.ql_mvar
    total_load_p = self.net.load.p_mw.sum() + line_losses_p.sum() + trafo_losses_p.sum()
    total_load_q = self.net.load.q_mvar.sum() + line_losses_q.sum() + trafo_losses_q.sum()

    p_res = total_load_p - self.net.sgen.p_mw.sum() + self.net.storage['p_mw'].sum()
    q_res = total_load_q - self.net.sgen.q_mvar.sum() + self.net.storage['q_mvar'].sum()

    s_res = (p_res**2 + q_res**2)**(.5)
    if p_res <= 0:
      s_res = -s_res

    return s_res, p_res

  # only use with 'household-oriented feed-in damping'
  def get_residualload_p_per_household(self):
    p_res = self.net.load.loc[self.load_index, 'p_mw'].values + \
            self.net.load.loc[self.hp_index, 'p_mw'].values + \
            self.net.load.loc[self.ev_index, 'p_mw'].values - \
            self.net.sgen['p_mw'].values + \
            self.net.storage['p_mw'].values
    return p_res

  # only use with 'household-oriented feed-in damping'
  def get_residualload_q_per_household(self):
    q_res = self.net.load.loc[self.load_index, 'q_mvar'].values + \
            self.net.load.loc[self.hp_index, 'q_mvar'].values + \
            self.net.load.loc[self.ev_index, 'q_mvar'].values - \
            self.net.sgen['q_mvar'].values  + \
            self.net.storage['q_mvar'].values
    return q_res

  # only use with 'household-oriented feed-in damping'
  def get_residualload_s_per_household(self):
    p_res = self.get_residualload_p_per_household()
    q_res = self.get_residualload_q_per_household()
    s_res = (p_res**2 + q_res**2)**(.5)
    s_res[p_res < 0] = -s_res[p_res < 0]

    return s_res

  def get_buses_per_feeder(self):
    '''
    Traces along the feeders within the network, allocate each bus to a feeder number, write the result into self.grid.net.bus.feeder.
    Store all lines connected with the trafo in self.monitored_lines.
    '''
    def trace_feeder_path(line, bus, index, feeder):
      if self.net.bus.loc[self.net.bus.index == bus, 'feeder'].values == 0:
        self.net.bus.loc[self.net.bus.index == bus, 'feeder'] = feeder
      else:
        raise ValueError('Network topology appears to have rings. Tracing of net topology aborted')
      new_line = self.net.line.loc[bus == self.net.line.from_bus]
      new_line = new_line.append(self.net.line.loc[bus == self.net.line.to_bus])
      if line.name in new_line.name:        
        new_line = new_line.drop(index=index)

      for i in new_line.index:
        if new_line.loc[i].from_bus != bus:
          trace_feeder_path(new_line.loc[i], new_line.loc[i].from_bus, i, feeder)
        if new_line.loc[i].to_bus != bus:
          trace_feeder_path(new_line.loc[i], new_line.loc[i].to_bus, i, feeder)

    self.monitored_lines = self.net.line.loc[int(self.net.trafo.lv_bus.values) == self.net.line.from_bus]
    self.monitored_lines = self.monitored_lines.append(self.net.line.loc[int(self.net.trafo.lv_bus.values) == self.net.line.to_bus])
    self.net.bus['feeder'] = 0
    self.monitored_lines['feeder'] = 0

    feeder = 0
    for i in self.monitored_lines.index:
      feeder += 1
      self.monitored_lines.feeder.loc[i] = feeder
      if self.monitored_lines.loc[i].from_bus != int(self.net.trafo.lv_bus.values):
        trace_feeder_path(self.monitored_lines.loc[i], self.monitored_lines.loc[i].from_bus, i, feeder)
      if self.monitored_lines.loc[i].to_bus != int(self.net.trafo.lv_bus.values):
        trace_feeder_path(self.monitored_lines.loc[i], self.monitored_lines.loc[i].to_bus, i, feeder)

    self.feeder = {'n_feeder' : feeder,
                   'buses_in_feeder' : pd.DataFrame(columns=['buses'], index=range(1,feeder+1)),
                   'load_index_in_feeder' : pd.DataFrame(columns=['load_index'], index=range(1,feeder+1)),
                   'sgen_index_in_feeder' : pd.DataFrame(columns=['sgen_index'], index=range(1,feeder+1)),
                   'storage_index_in_feeder' : pd.DataFrame(columns=['storage_index'], index=range(1,feeder+1))}

  def get_load_sgen_index_per_feeder(self):
    for i in range(1,self.feeder['n_feeder'] + 1):
       self.feeder['buses_in_feeder'].loc[i]['buses'] = self.net.bus.loc[i == self.net.bus.feeder].index
       self.feeder['load_index_in_feeder'].loc[i]['load_index'] = self.net.load[self.net.load.bus.isin(self.feeder['buses_in_feeder'].loc[i]['buses'])].index
       self.feeder['sgen_index_in_feeder'].loc[i]['sgen_index'] = self.net.sgen[self.net.sgen.bus.isin(self.feeder['buses_in_feeder'].loc[i]['buses'])].index
       self.feeder['storage_index_in_feeder'].loc[i]['storage_index'] = self.net.storage[self.net.storage.bus.isin(self.feeder['buses_in_feeder'].loc[i]['buses'])].index

    self.feeder['buses_in_feeder']['l_sum'] = 0
    self.feeder['buses_in_feeder']['dv_max'] = 0
    self.feeder['buses_in_feeder']['bus_dv_max'] = np.nan
    self.feeder['buses_in_feeder']['p_bss'] = 0

  def get_timedelta(self, t):
      sunrise = datetime.datetime.combine(t.date(), self.df_solar.loc[t.date()].sunrise)
      sunset = datetime.datetime.combine(t.date(), self.df_solar.loc[t.date()].sunset)
      t = t.tz_localize(None)
      timedelta_sunrise_sunset_s = (sunset - sunrise).total_seconds()
      timedelta_day_s = abs((sunset - t).total_seconds())
      #timedelta_night_s = abs((sunrise - t).total_seconds()) ### timedelta next day
      return sunrise, sunset, timedelta_day_s, timedelta_sunrise_sunset_s

  def create_test_net_one_load_branch(self):
    '''
    Create a test grid with one household: ext_grid --- trafo --- line --- generation/consumption
    '''
    net = pp.create_empty_network(name='one_load_branch')
    b1 = pp.create_bus(net=net, vn_kv = 10, name='1')
    b2 = pp.create_bus(net=net, vn_kv =.4, name='2')
    b3 = pp.create_bus(net=net, vn_kv =.4, name='3')
    pp.create_ext_grid(net, b1, name='ext_grid')
    pp.create_line(net, b3, b2, 5, 'NAYY 4x50 SE', name='line')
    pp.create_load(net, b3, 0)
    pp.create_transformer(net, b1, b2, '0.25 MVA 10/0.4 kV', name='trafo')
    return net

  def create_test_net_n_load_branch(self):
    '''
    Create a test grid with n household: ext_grid --- trafo --- line --- generation/consumption ... --- line --- generation/consumption
    '''

    n = 50 # Number of buses
    net = pp.create_empty_network(name='n_load_branch')
    b1 = pp.create_bus(net=net, vn_kv = 10, name='Bus T1', geodata=(1,n))
    b2 = pp.create_bus(net=net, vn_kv =.4, name='Bus T2', geodata=(1,n-1))
    pp.create_transformer(net, b1, b2, '0.25 MVA 10/0.4 kV', name='trafo')
    pp.create_ext_grid(net, b1, name='ext_grid')
    b_k = b2

    for i in range(n):
      b_i = pp.create_bus(net=net, vn_kv =.4, name='Bus '+str(i), geodata=(1,n-2-i))
      pp.create_line(net, b_i, b_k, .015, 'NAYY 4x150 SE', name='line')
      pp.create_load(net, b_i, 0)
      b_k = b_i

    #sys.exit(0)

    return net



















