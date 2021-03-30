import os
import pandas as pd

class OutputDataHandler():

  def __init__(self):
    pass

  #########################
  ### create output_dir ###
  #########################
  def create_output_dir(self, net_name, scenario, time_scope):
        self.output_dir = os.path.join("./", "output-files/"+str(scenario)+"/"+str(net_name)+"/"+time_scope['start_time'][0:10]+"_"+time_scope['end_time'][0:10]+"_"+time_scope['t_freq']+"/")
        # Create output directory
        if not os.path.isdir(self.output_dir):
          try:
            os.makedirs(self.output_dir)
          except OSError:
            print("Error: Creation of output directory %s failed" % self.output_dir)
          else:
            print("Create outout directory %s" % self.output_dir)

        return self.output_dir

  def create_output_dataframes(self, grid):
        self.vm_pu = pd.DataFrame(columns=grid.net.bus.index)
        self.li_lo = pd.DataFrame(columns=grid.net.line.index)
        self.tr_lo = pd.DataFrame(columns=grid.net.trafo.index)
        self.power = pd.DataFrame(columns=['load', 'pv', 'hp', 'ev'])
        self.pv_reactive_power = pd.DataFrame(columns=grid.net.bus.index)
        self.pv_active_power = pd.DataFrame(columns=grid.net.bus.index)
        self.storage_active_power = pd.DataFrame(columns=grid.net.storage.index)
        self.trafo_active_power = pd.DataFrame(columns=grid.net.trafo.index)
        self.losses_active_power = pd.DataFrame(columns=['trafo','lines'])
        self.vm_pu.index.name = 'timestamp'
        self.li_lo.index.name = 'timestamp'
        self.tr_lo.index.name = 'timestamp'
        self.power.index.name = 'timestamp'
        self.pv_reactive_power.index.name  = 'timestamp'
        self.pv_active_power.index.name = 'timestamp'
        self.storage_active_power.index.name = 'timestamp'
        self.trafo_active_power.index.name = 'timestamp'
        self.losses_active_power.index.name = 'timestamp'

  def write_output_into_dataframe(self, grid, t):
        self.vm_pu.loc[t] = grid.net.res_bus.vm_pu
        self.li_lo.loc[t] = grid.net.res_line.loading_percent
        self.tr_lo.loc[t] = grid.net.res_trafo.loading_percent
        self.power.loc[t] = [grid.net.load.p_mw[grid.load_index].sum(),
                             grid.net.sgen.p_mw.sum(),
                             grid.net.load.p_mw[grid.hp_index].sum(),
                             grid.net.load.p_mw[grid.ev_index].sum()]
        self.pv_reactive_power.loc[t] = grid.net.sgen['q_mvar']
        self.pv_active_power.loc[t]   = grid.net.sgen['p_mw']
        self.storage_active_power.loc[t] = grid.net.storage['p_mw']
        self.trafo_active_power.loc[t] = grid.net.res_trafo.p_hv_mw
        self.losses_active_power.loc[t] = [grid.net.res_trafo.pl_mw.sum(),
                                           grid.net.res_line.pl_mw.sum()]

  def write_dataframe_to_csv(self, mode, header, grid):
        self.vm_pu.round(3).to_csv(self.output_dir + 'res_bus_vm_pu.csv',
                                   mode=mode, header=header, index = True)
        self.li_lo.round(1).to_csv(self.output_dir + 'res_line_load_percent.csv',
                                   mode=mode, header=header, index = True)
        self.tr_lo.round(1).to_csv(self.output_dir + 'res_trafo_load_percent.csv',
                                   mode=mode, header=header, index = True)
        self.power.round(6).to_csv(self.output_dir + 'power_total_MW.csv',
                                   mode=mode, header=header, index = True)
        self.pv_active_power.round(6).to_csv(self.output_dir + 'pv_active_power_MW.csv',
                                             mode=mode, header=header, index = True)
        self.pv_reactive_power.round(6).to_csv(self.output_dir + 'pv_reactive_power_MW.csv',
                                               mode=mode, header=header, index = True)
        self.storage_active_power.round(6).to_csv(self.output_dir + 'storage_active_power_MW.csv',
                                                  mode=mode, header=header, index = True)
        self.trafo_active_power.round(6).to_csv(self.output_dir + 'trafo_active_power_MW.csv',
                                                  mode=mode, header=header, index = True)
        self.losses_active_power.round(6).to_csv(self.output_dir + 'losses_active_power_MW.csv',
                                                  mode=mode, header=header, index = True)



        self.create_output_dataframes(grid)
