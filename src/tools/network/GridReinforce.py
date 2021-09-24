import pandapower as pp
import pandapower.networks as pn
import pandapower.topology as top
from pandapower.plotting.plotly import simple_plotly
from pandapower.plotting.plotly import pf_res_plotly
from pandapower.plotting.plotly import create_bus_trace

import simbench as sb

import pandas as pd
import math
import numpy as np

import tools.tools as tt


class GridReinforce:

  def __init__(self, grid, output_dir_worst_case, output_dir, use_data_of_scenario):
    self.grid = grid
    self.net_name = self.grid.net_name
    self.output_dir = output_dir
    self.output_dir_worst_case = output_dir_worst_case

    self.use_data_of_scenario = use_data_of_scenario

    self.load_scenario_output_data()

    self.trafo_overloading = self.tl.max().max()
    self.trafo_overloading_time = pd.to_datetime(self.tl.max(axis=1).idxmax())

    self.line_overloading = self.ll.max().max()
    self.line_overloading_time = pd.to_datetime(self.ll.max(axis=1).idxmax())

    self.overvoltage = self.v_pu.max().max().round(3)
    self.overvoltage_time = pd.to_datetime(self.v_pu.max(axis=1).idxmax())

    self.undervoltage = self.v_pu.min().min().round(3)
    self.undervoltage_time = pd.to_datetime(self.v_pu.min(axis=1).idxmin())

    self.result_lines = pd.DataFrame(columns=['linetype', 'from_bus', 'to_bus', 'length_in_km', 'costs_per_km', 'total_costs'])
    self.result_trafo = pd.DataFrame(columns=['trafotype', 'costs'])

    self.define_std_types()
    self.set_grid_expantion_costs()


  def define_std_types(self):
    #https://shop.faberkabel.de/out/downloads/uploads/DE/dbl_nayy.pdf
    omega = 2*math.pi*50
    pp.create_std_type(self.grid.net, {
                       "r_ohm_per_km": 0.164, "x_ohm_per_km": omega*0.256/1000,
                       "c_nf_per_km": 261, "max_i_ka": 0.313},
                       name="NAYY 4x185SE 0.6/1kV",element = "line")

    pp.create_std_type(self.grid.net, {
                       "r_ohm_per_km": 0.125, "x_ohm_per_km": omega*0.254/1000,
                       "c_nf_per_km": 261, "max_i_ka": 0.364},
                       name="NAYY 4x240SE 0.6/1kV",element = "line")


    pp.create_std_type(self.grid.net, {
                       "r_ohm_per_km": 0.1, "x_ohm_per_km": omega*0.279/1000,
                       "c_nf_per_km": 261, "max_i_ka": 0.419},
                       name="NAYY 4x300SE 0.6/1kV",element = "line")

  def set_grid_expantion_costs(self):
    # according to Verteilnetzstudie Hessen
    self.trafo_costs_dir = {'0.25 MVA 20/0.4 kV' : 
                                {'inv_cost' : 25000.+7000.,
                                 'ope_cost' : (25000.+7000.)*.02,
                                 'ope_time' : 35},
                            '0.4 MVA 20/0.4 kV' : 
                                {'inv_cost' : 25000.+9000.,
                                 'ope_cost' : (25000.+9000.)*.02,
                                 'ope_time' : 35},
                            '0.63 MVA 20/0.4 kV' : 
                                {'inv_cost' : 25000.+12000.,
                                 'ope_cost' : (25000.+12000.)*.02,
                                 'ope_time' : 35}
    }

    # according to Verteilnetzstudie Baden-Württemberg
    self.lines_costs_dir = {'rural' : 80000.,
                            'suburban' : 100000.,
                            'urban' : 120000.
    }

  def load_scenario_output_data(self):
    # check if scenario 4 exists and load data
    if self.output_dir_worst_case:
       try:
         self.v_pu = tt.read_data(self.output_dir_worst_case + 'res_bus_vm_pu.csv')
         self.ll = tt.read_data(self.output_dir_worst_case+'res_line_load_percent.csv')
         self.tl = tt.read_data(self.output_dir_worst_case+'res_trafo_load_percent.csv')
         self.load_p = tt.read_data(self.output_dir_worst_case+'load_active_power_MW.csv')
         self.load_q = tt.read_data(self.output_dir_worst_case+'load_reactive_power_MW.csv')
         self.pv_p = tt.read_data(self.output_dir_worst_case+'pv_active_power_MW.csv')
         self.pv_q = tt.read_data(self.output_dir_worst_case+'pv_reactive_power_MW.csv')
         self.v_pu_ext_grid = tt.read_data(self.output_dir_worst_case+'v_pu_ext_grid.csv')
       except:
         raise KeyError('Run first Scenario 4')         
    else:
       raise KeyError('Run first Scenario 4')

  def fill_grid_with_power_values(self, timestep):
    self.grid.net.sgen['p_mw'] = self.pv_p.loc[timestep].values
    self.grid.net.sgen['q_mvar'] = self.pv_q.loc[timestep].values
    self.grid.net.load['p_mw'] = self.load_p.loc[timestep].values
    self.grid.net.load['q_mvar'] = self.load_q.loc[timestep].values
    self.grid.net.ext_grid.vm_pu = self.v_pu_ext_grid.loc[timestep].values

  ##########################
  ### START: TRANSFORMER ###
  ##########################
  def reinforce_transformer(self, grid):
    self.grid = grid
    print(' ')
    print(tt.text1('Transfromer reinforcement: ')+ str(self.trafo_overloading_time))
    print('Maximum trafo loading within the grid: ' + str(self.trafo_overloading) + ' %')
    if (self.trafo_overloading > 100).any() or self.use_data_of_scenario[0] == 5:
      print(tt.textred('Transformer reinforcement needed.'))
      print('Original transformer:')
      self.print_trafo_loading()
      lv_bus = int(self.grid.net.trafo.lv_bus.values)
      hv_bus = int(self.grid.net.trafo.hv_bus.values)
      transformer_types = self.get_transformer_type()
      if transformer_types != None:
        self.grid.net.trafo.drop(0, inplace=True)
        for trafo_type in transformer_types:
          pp.create_transformer(self.grid.net, hv_bus, lv_bus, trafo_type)
      else:
        print('No transformer changed')
      self.fill_grid_with_power_values(self.trafo_overloading_time)
      pp.runpp(self.grid.net, algorithm='nr', init='results', max_iteration=30, tolerance_mva=1e-6)
      self.trafo_overloading = self.grid.net.res_trafo.loading_percent.values.round(0)
      print('Transformer changed to:')
      self.print_trafo_loading()

      for trafotype in transformer_types:
        result = pd.DataFrame(data=[[trafotype, self.trafo_costs_dir[trafotype]['inv_cost']]], columns=self.result_trafo.columns.values)
        self.result_trafo = self.result_trafo.append(result, ignore_index=True)  
      self.result_trafo.round(3).to_csv(self.output_dir + 'reinforced_trafo.csv',
                                   mode='w', header=True, index=True)
      print(self.result_trafo)
    else:
      print(tt.textgreen('No transformer reinforcement needed.'))
    print(' ')

    return self.grid

  def get_transformer_type(self):
    if self.net_name == "kerber_rural_1":
      return ['0.25 MVA 10/0.4 kV']
      #return self.grid.net.trafo.std_type.loc[0]
    elif self.net_name == "kerber_rural_2":
      return self.grid.net.trafo.std_type.loc[0]
    elif self.net_name == "kerber_rural_3":
      return self.grid.net.trafo.std_type.loc[0]
    elif self.net_name == "kerber_rural_4":
      return self.grid.net.trafo.std_type.loc[0]
    elif self.net_name == "kerber_village":
      return self.grid.net.trafo.std_type.loc[0]
    elif self.net_name == "kerber_suburb_1":
      return self.grid.net.trafo.std_type.loc[0]
    elif self.net_name == "kerber_suburb_2":
      return self.grid.net.trafo.std_type.loc[0]
    elif self.net_name == "simbench_rural_1":
      return ['0.25 MVA 20/0.4 kV']
    elif self.net_name == "simbench_rural_2":
      return ['0.63 MVA 20/0.4 kV', '0.63 MVA 20/0.4 kV', '0.63 MVA 20/0.4 kV']
    elif self.net_name == "simbench_rural_3":
      return ['0.63 MVA 20/0.4 kV', '0.63 MVA 20/0.4 kV', '0.63 MVA 20/0.4 kV', '0.25 MVA 20/0.4 kV']
    elif self.net_name == "simbench_suburb_4":
      return ['0.63 MVA 20/0.4 kV']
    elif self.net_name == "simbench_suburb_5":
      return ['0.63 MVA 20/0.4 kV', '0.63 MVA 20/0.4 kV']
    elif self.net_name == "simbench_urban_6":
      return None
    elif self.net_name == "test_net_one_load_branch":
      return None

  def print_trafo_loading(self):
    print('Trafo %s loaded to %s %%' % (self.grid.net.trafo.std_type.values, (self.trafo_overloading)))
  ########################
  ### END: TRANSFORMER ###
  ########################



  ##########################
  ### START: LINELOADING ###
  ##########################
  def reinforce_lines(self, grid):
    self.grid = grid
    print(' ')
    print(tt.text1('Line reinforcement: '))
    self.print_loading_voltage()

    if (self.line_overloading > 100) or (self.overvoltage > 1.1) or (self.undervoltage < .9) or self.use_data_of_scenario[0] == 5:
      self.install_line_by_gridtype()
    else:
      print(tt.textgreen('No line reinforcement needed.'))

    if self.line_overloading > 100:
      print(tt.textred('Line reinforcement needed (Overloading).'))
      self.fill_grid_with_power_values(self.line_overloading_time)
      pp.runpp(self.grid.net, algorithm='nr', init='results', max_iteration=30, tolerance_mva=1e-6)
      self.line_overloading = self.grid.net.res_line.loading_percent.max()

    if self.overvoltage > 1.1:
      print(tt.textred('Line reinforcement needed (Overvoltage).'))
      self.fill_grid_with_power_values(self.overvoltage_time)
      pp.runpp(self.grid.net, algorithm='nr', init='results', max_iteration=30, tolerance_mva=1e-6)
      self.overvoltage = self.grid.net.res_bus.vm_pu.max().max()

    if self.undervoltage < .9:
      print(tt.textred('Line reinforcement needed (Undervoltage).'))
      self.fill_grid_with_power_values(self.undervoltage_time)
      pp.runpp(self.grid.net, algorithm='nr', init='results', max_iteration=30, tolerance_mva=1e-6)
      self.undervoltage = self.grid.net.res_bus.vm_pu.min().min()

    print('Line(s) changed to: ')
    print(self.result_lines)
    self.print_loading_voltage()
    #pp.plotting.to_html(self.grid.net, 'test.html', respect_switches=True, include_lines=True, include_trafos=True, show_tables=True)
    self.result_lines.round(3).to_csv(self.output_dir + 'reinforced_lines.csv',
                                   mode='w', header=True, index=True)

    print(' ')

    return self.grid


  def install_line_by_gridtype(self):
    if self.net_name == "kerber_rural_1":
      return None
    elif self.net_name == "kerber_rural_2":
      return None
    elif self.net_name == "kerber_rural_3":
      return None
    elif self.net_name == "kerber_rural_4":
      return None
    elif self.net_name == "kerber_village":
      return None
    elif self.net_name == "kerber_suburb_1":
      return None
    elif self.net_name == "kerber_suburb_2":
      return None
    elif self.net_name == "simbench_rural_1":
      return None
    elif self.net_name == "simbench_rural_2":
      # Strang 1
      self.connect_buses(bus_to_trafo=74, former_bus=None, line_type='NAYY 4x240SE 0.6/1kV')
      self.disconnect_buses(22, 68)
      # Strang 2
      self.connect_buses(bus_to_trafo=4, former_bus=16, line_type='NAYY 4x150SE 0.6/1kV')
      # Strang 3
      self.connect_buses(bus_to_trafo=19, former_bus=37, line_type='NAYY 4x150SE 0.6/1kV')
      # Strang 4
      self.connect_buses(bus_to_trafo=75, former_bus=80, line_type='NAYY 4x300SE 0.6/1kV')
      self.connect_buses(bus_to_trafo=10, former_bus=71, line_type='NAYY 4x185SE 0.6/1kV')
      self.connect_buses(bus_to_trafo= 5, former_bus=17, line_type='NAYY 4x185SE 0.6/1kV')
      self.connect_buses(bus_to_trafo= 6, former_bus=92, line_type='NAYY 4x150SE 0.6/1kV')
      return None
    elif self.net_name == "simbench_rural_3":
      # Strang 1
      self.connect_buses(bus_to_trafo=74, former_bus=58, line_type='NAYY 4x185SE 0.6/1kV')
      self.connect_buses(bus_to_trafo=37, former_bus=126, line_type='NAYY 4x150SE 0.6/1kV')
      # Strang 6
      self.connect_buses(bus_to_trafo=46, former_bus=61, line_type='NAYY 4x150SE 0.6/1kV')
      # Strang 7
      self.connect_buses(bus_to_trafo=108, former_bus=33, line_type='NAYY 4x185SE 0.6/1kV')
      self.connect_buses(bus_to_trafo=125, former_bus=53, line_type='NAYY 4x185SE 0.6/1kV')
      # Strang 8
      self.connect_buses(bus_to_trafo=95, former_bus=92, line_type='NAYY 4x185SE 0.6/1kV')
      self.connect_buses(bus_to_trafo=102, former_bus=41, line_type='NAYY 4x150SE 0.6/1kV')
      # Strang 9
      self.connect_buses(bus_to_trafo=111, former_bus=31, line_type='NAYY 4x185SE 0.6/1kV')
      self.connect_buses(bus_to_trafo=48, former_bus=107, line_type='NAYY 4x150SE 0.6/1kV')
      return None
    elif self.net_name == "simbench_suburb_4":
      # Strang 3
      self.connect_buses(bus_to_trafo=22, former_bus=10, line_type='NAYY 4x150SE 0.6/1kV')
      return None
    elif self.net_name == "simbench_suburb_5":
      # Strang 2
      self.connect_buses(bus_to_trafo=79, former_bus=2, line_type='NAYY 4x185SE 0.6/1kV')
      # Strang 4
      self.connect_buses(bus_to_trafo=56, former_bus=10, line_type='NAYY 4x150SE 0.6/1kV')
      self.connect_buses(bus_to_trafo=80, former_bus=59, line_type='NAYY 4x150SE 0.6/1kV')
      return None
    elif self.net_name == "simbench_urban_6":
      return None
    elif self.net_name == "test_net_one_load_branch":
      return None


  def connect_buses(self, bus_to_trafo, former_bus, line_type):
    trafo_lv_bus_nr = self.grid.net.trafo.lv_bus[0]
    dist = top.calc_distance_to_bus(self.grid.net, trafo_lv_bus_nr)
    new_linelength = dist[bus_to_trafo]
    pp.create_line(self.grid.net, trafo_lv_bus_nr, bus_to_trafo, new_linelength, line_type)

    if former_bus != None:
      self.disconnect_buses(bus1=bus_to_trafo, bus2=former_bus)

    result = pd.DataFrame(data=[[line_type, trafo_lv_bus_nr,
                                          bus_to_trafo,
                                          new_linelength,
                                          self.lines_costs_dir[self.grid.category],  
                                          (new_linelength*self.lines_costs_dir[self.grid.category]).round(2)]],
                                          columns=self.result_lines.columns.values)
    self.result_lines = self.result_lines.append(result, ignore_index=True)   

  def disconnect_buses(self, bus1, bus2):
    lines1 = self.grid.net.line[(self.grid.net.line['from_bus'] == bus1)]
    lines2 = self.grid.net.line[(self.grid.net.line['to_bus'] == bus1)]
    lines = [lines1[lines1['to_bus'] == bus2], lines2[lines2['from_bus'] == bus2]]
    lines = pd.concat(lines)
    if lines.empty:
      raise ValueError('No connection between the two buses found.')
    self.grid.net.line.drop(lines.index, inplace=True)

  def print_loading_voltage(self):
    print('Max line loading at '+str(self.line_overloading_time)+': ' + str(self.line_overloading.round(1)) + ' %')
    print('Max bus voltage at  '+str(self.overvoltage_time)+': ' + str(self.overvoltage.round(3)) + ' p.u.')
    print('Min bus voltage at  '+str(self.undervoltage_time)+': ' + str(self.undervoltage.round(3)) + ' p.u.')

  ########################
  ### END: LINELOADING ###
  ########################

  def final_grid_check(self):
    everything_ok = True
    if (self.overvoltage > 1.1):
      print(tt.textred('Overvoltage      at %s: %s' % (self.overvoltage_time, self.overvoltage)))
      self.fill_grid_with_power_values(self.overvoltage_time)
      pp.runpp(self.grid.net, algorithm='nr', init='results', max_iteration=30, tolerance_mva=1e-6)
      everything_ok = False
    if (self.undervoltage < .9):
      print(tt.textred('Undervoltage     at %s: %s' % (self.undervoltage_time, self.undervoltage)))
      self.fill_grid_with_power_values(self.undervoltage_time)
      pp.runpp(self.grid.net, algorithm='nr', init='results', max_iteration=30, tolerance_mva=1e-6)
      everything_ok = False 
    if (self.line_overloading > 100):
      print(tt.textred('Lineoverloading  at %s: %s %%' % (self.line_overloading_time, self.line_overloading)))
      self.fill_grid_with_power_values(self.line_overloading_time)
      pp.runpp(self.grid.net, algorithm='nr', init='results', max_iteration=30, tolerance_mva=1e-6)
      everything_ok = False   
    if (self.trafo_overloading > 100).any():
      print(tt.textred('Trafooverloading at %s: %s %%' % (self.trafo_overloading_time, self.trafo_overloading)))
      self.fill_grid_with_power_values(self.trafo_overloading_time)
      pp.runpp(self.grid.net, algorithm='nr', init='results', max_iteration=30, tolerance_mva=1e-6)
      everything_ok = False
    if everything_ok:
      print(tt.textgreen('All components work within normal parameters.'))

    total_line_costs = self.result_lines.total_costs.sum()
    total_trafo_costs = self.result_trafo.costs.sum()

    print('Total line- and transformercosts: %s Euro' % (round(float(total_line_costs + total_trafo_costs))))

    pf_res_plotly(self.grid.net, aspectratio=(1,1))

