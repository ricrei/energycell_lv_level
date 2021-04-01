import pandapower as pp
import pandapower.networks as pn
from pandapower.plotting.plotly import simple_plotly
from pandapower.plotting.plotly import pf_res_plotly

import simbench as sb

import pandas as pd

import tools.tools as tt


class GridReinforce:

  def __init__(self, grid, output_dir_worst_case):
    self.grid = grid
    self.net_name = self.grid.net_name
    self.output_dir_worst_case = output_dir_worst_case
    self.load_scenario_output_data()

    self.trafo_overloading = int(self.tl.max().values)
    self.trafo_overloading_time = pd.to_datetime(self.tl.idxmax())

    self.line_overloading = int(self.ll.max().max())
    self.line_overloading_time = pd.to_datetime(self.tl.idxmax())



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
    self.grid.net.sgen['p_mw'] = self.pv_p.loc[timestep].values[0]
    self.grid.net.sgen['q_mvar'] = self.pv_q.loc[timestep].values[0]
    self.grid.net.load['p_mw'] = self.load_p.loc[timestep].values[0]
    self.grid.net.load['q_mvar'] = self.load_q.loc[timestep].values[0]
    self.grid.net.ext_grid.vm_pu = self.v_pu_ext_grid.loc[timestep].values[0]

  ##########################
  ### START: TRANSFORMER ###
  ##########################
  def reinforce_transformer(self):
    print(' ')
    print(tt.text1('Transfromer reinforcement: ')+ str(self.trafo_overloading_time[0]))
    print('Maximum trafo loading within the grid: ' + str(self.trafo_overloading) + ' %')
    if self.trafo_overloading > 100:
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
      self.trafo_overloading = self.grid.net.res_trafo.loading_percent.values
      print('Transformer changed to:')
      self.print_trafo_loading()
    else:
      print(tt.textgreen('No transformer reinforcement needed.'))
    print(' ')

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
      return None#['0.25 MVA 20/0.4 kV']
    elif self.net_name == "simbench_rural_2":
      return None#['0.63 MVA 20/0.4 kV']
    elif self.net_name == "simbench_rural_3":
      return None
    elif self.net_name == "simbench_suburb_4":
      return None
    elif self.net_name == "simbench_suburb_5":
      return None
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
  def reinforce_lines(self):
    print(' ')
    print(tt.text1('Line inforcement: ')+ str(self.line_overloading_time[0]))
    print('Maximum line loading within the grid: ' + str(self.line_overloading) + ' %')
    if self.line_overloading > 100:
      print(tt.textred('Line reinforcement needed.'))
      self.fill_grid_with_power_values(self.line_overloading_time)
      self.install_line_by_gridtype()
      pp.runpp(self.grid.net, algorithm='nr', init='results', max_iteration=30, tolerance_mva=1e-6)
      #pf_res_plotly(self.grid.net, aspectratio=(1,1))
    else:
      print(tt.textgreen('No line reinforcement needed.'))
    print(' ')

  # TODO: in process
  def install_line_by_gridtype(self):
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
      return None#['0.25 MVA 20/0.4 kV']
    elif self.net_name == "simbench_rural_2":
      return None#['0.63 MVA 20/0.4 kV']
    elif self.net_name == "simbench_rural_3":
      return None
    elif self.net_name == "simbench_suburb_4":
      return None
    elif self.net_name == "simbench_suburb_5":
      return None
    elif self.net_name == "simbench_urban_6":
      return None
    elif self.net_name == "test_net_one_load_branch":
      return None

  ########################
  ### END: LINELOADING ###
  ########################


  '''
  def is_transformer_overloaded(self):
    return self.tl.max().values > 100

  def get_timeindex_of_max_overload(self):
    return self.tl.idxmax()

  def print_trafo_max_load(self):
    print(self.grid.net.trafo.std_type.values)
    print(str(self.tl.max().values) + ' at ' + str(self.get_timeindex_of_max_overload()))

  def get_new_grid(self, grid):
    self.grid = grid
    self.tl = pd.DataFrame(self.grid.net.res_trafo.loading_percent)


  def reinforce_transformer(self):
    lv_bus = int(self.grid.net.trafo.lv_bus.values)
    hv_bus = int(self.grid.net.trafo.hv_bus.values)
    self.grid.net.trafo.drop(0, inplace=True)
    pp.create_transformer(self.grid.net, hv_bus, lv_bus, '0.63 MVA 20/0.4 kV')
    #self.grid.net.trafo.std_type = '0.25 MVA 20/0.4 kV'
    return self.grid
  '''




#    print(self.grid.net.trafo)
#    print(self.tl.max().values)
#    print(self.tl.idxmax())
