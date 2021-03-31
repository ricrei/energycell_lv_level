import pandapower as pp
import pandapower.networks as pn
import simbench as sb

import pandas as pd

import tools.tools as tt

''' belongs in EnergyCell.py

    ######################
    ### reinforce grid ###
    ######################
    def reinforce_grid(self):
      self.load_timeseries()
      # 1. check whether overload exists and where
      # 2. improve grid component
      # 3. run_pf
      i = 0
      if self.grid_reinforce.is_transformer_overloaded():
        timeindex = self.grid_reinforce.get_timeindex_of_max_overload()
        trafo_overloaded = True
        while trafo_overloaded:
          self.grid_reinforce.print_trafo_max_load()
          self.grid = self.grid_reinforce.reinforce_transformer()
          self.grid = self.pf.run_power_flow_through_timeseries(df=self.df.loc[timeindex],
                                                  grid=self.grid,
                                                  pv_controller=self.pv_controller,
                                                  hp_controller=self.hp_controller,
                                                  ev_controller=self.ev_controller,
                                                  bss_controller=self.bss_controller,
                                                  output_data_handler=self.output_data_handler)
          self.grid_reinforce.get_new_grid(self.grid)
          trafo_overloaded = (self.grid.net.res_trafo.loading_percent.values > 100)

        self.grid_reinforce.print_trafo_max_load()

      #  if i == 1:
      #    raise ValueError('breakpoint')
      #  i += 1

'''



class GridReinforce:

  def __init__(self, grid, output_dir_worst_case):
    self.grid = grid
    self.output_dir_worst_case = output_dir_worst_case
    self.load_scenario_output_data()
    

    self.trafo_typs_next = {}

  def run_worst_case(self):
    pass

  def load_scenario_output_data(self):
    # check if scenario 4 exists and load data
    if self.output_dir_worst_case:
       try:
         self.v_pu = tt.read_data(self.output_dir_worst_case + 'res_bus_vm_pu.csv')
         self.ll = tt.read_data(self.output_dir_worst_case+'res_line_load_percent.csv')
         self.tl = tt.read_data(self.output_dir_worst_case+'res_trafo_load_percent.csv')
       except:
         raise KeyError('Run first Scenario 4')         
    else:
       raise KeyError('Run first Scenario 4')


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




#    print(self.grid.net.trafo)
#    print(self.tl.max().values)
#    print(self.tl.idxmax())
