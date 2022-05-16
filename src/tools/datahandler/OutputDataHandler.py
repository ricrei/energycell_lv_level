import os
import pandas as pd

class OutputDataHandler():

  def __init__(self, save_full_data = False):
    self.save_full_data = save_full_data

  #########################
  ### create output_dir ###
  #########################
  def create_output_dir(self, net_name, scenario_frame, time_scope):
        self.output_dir = os.path.join("./", "output-files/"+''.join(str(num) for num in scenario_frame)+"/"+str(net_name)+"/"+time_scope['start_time'][0:10]+"_"+time_scope['end_time'][0:10]+"_"+time_scope['t_freq']+"/")
        # Create output directory
        if not os.path.isdir(self.output_dir):
          try:
            os.makedirs(self.output_dir)
          except OSError:
            print("Error: Creation of output directory %s failed" % self.output_dir)
          else:
            #print("Create outout directory %s" % self.output_dir)
            pass

        return self.output_dir

  def create_output_dataframes(self, grid):
        self.vm_pu = pd.DataFrame(columns=grid.net.bus.index)
        self.vm_pu.index.name = 'timestamp'
        self.li_lo = pd.DataFrame(columns=grid.net.line.index)
        self.li_lo.index.name = 'timestamp'
        self.tr_lo = pd.DataFrame(columns=grid.net.trafo.index)
        self.tr_lo.index.name = 'timestamp'
        self.power = pd.DataFrame(columns=['load', 'pv', 'hp', 'ev'])
        self.power.index.name = 'timestamp'
        self.storage_active_power = pd.DataFrame(columns=grid.net.storage.index)
        self.storage_active_power.index.name = 'timestamp'
        self.storage_state_of_charge = pd.DataFrame(columns=grid.net.storage.index)
        self.storage_state_of_charge.index.name = 'timestamp'
        self.trafo_active_power = pd.DataFrame(columns=grid.net.trafo.index)
        self.trafo_active_power.index.name = 'timestamp'
        self.losses_active_power = pd.DataFrame(columns=['trafo','lines'])
        self.losses_active_power.index.name = 'timestamp'
        self.curtailed_power_pv = pd.DataFrame(columns=grid.net.sgen.index)
        self.curtailed_power_pv.index.name  = 'timestamp'
        self.curtailed_power_load = pd.DataFrame(columns=grid.net.load.index)
        self.curtailed_power_load.index.name  = 'timestamp'
        if self.save_full_data == True:
          self.pv_active_power = pd.DataFrame(columns=grid.net.sgen.index)
          self.pv_active_power.index.name = 'timestamp'
          self.pv_reactive_power = pd.DataFrame(columns=grid.net.sgen.index)
          self.pv_reactive_power.index.name  = 'timestamp'
          self.load_active_power = pd.DataFrame(columns=grid.net.load.index)
          self.load_active_power.index.name = 'timestamp'
          self.load_reactive_power = pd.DataFrame(columns=grid.net.load.index)
          self.load_reactive_power.index.name = 'timestamp'
          self.storage_energy_content = pd.DataFrame(columns=grid.net.storage.index)
          self.storage_energy_content.index.name = 'timestamp'
          self.ev_soc = pd.DataFrame(columns=grid.ev_index)
          self.ev_soc.index.name = 'timestamp'
          self.hp_demand_th = pd.DataFrame(columns=grid.hp_index)
          self.hp_demand_th.index.name = 'timestamp'
          self.hp_soc = pd.DataFrame(columns=grid.hp_index)
          self.hp_soc.index.name  = 'timestamp'
          self.hp_cop = pd.DataFrame(columns=grid.hp_index)
          self.hp_cop.index.name  = 'timestamp'
          self.hp_hp_th = pd.DataFrame(columns=grid.hp_index)
          self.hp_hp_th.index.name  = 'timestamp'
          self.hp_tes_th = pd.DataFrame(columns=grid.hp_index)
          self.hp_tes_th.index.name  = 'timestamp'
          self.hp_tes_losses_th = pd.DataFrame(columns=grid.hp_index)
          self.hp_tes_losses_th.index.name  = 'timestamp'
          self.trafo_reactive_power = pd.DataFrame(columns=grid.net.trafo.index)
          self.trafo_reactive_power.index.name = 'timestamp'
          self.v_pu_ext_grid = pd.DataFrame(columns=['v_pu'])
          self.v_pu_ext_grid.index.name  = 'timestamp'

  def write_output_into_dataframe(self, grid, t):
        self.vm_pu.loc[t] = grid.net.res_bus.vm_pu
        self.li_lo.loc[t] = grid.net.res_line.loading_percent
        self.tr_lo.loc[t] = grid.net.res_trafo.loading_percent
        self.power.loc[t] = [grid.net.load.p_mw[grid.load_index].sum(),
                             grid.net.sgen.p_mw.sum(),
                             grid.net.load.p_mw[grid.hp_index].sum(),
                             grid.net.load.p_mw[grid.ev_index].sum()]
        self.storage_active_power.loc[t] = grid.net.storage['p_mw']
        self.storage_state_of_charge.loc[t] = grid.net.storage['soc_percent']
        self.trafo_active_power.loc[t] = grid.net.res_trafo.p_hv_mw
        self.losses_active_power.loc[t] = [grid.net.res_trafo.pl_mw.sum(),grid.net.res_line.pl_mw.sum()]
        self.curtailed_power_pv.loc[t] = grid.curtailed_pv_power_df
        self.curtailed_power_load.loc[t] = grid.curtailed_load_power_df
        if self.save_full_data == True:
          self.pv_active_power.loc[t]   = grid.net.sgen['p_mw']
          self.pv_reactive_power.loc[t] = grid.net.sgen['q_mvar']
          self.load_active_power.loc[t] = grid.net.load['p_mw']
          self.load_reactive_power.loc[t] = grid.net.load['q_mvar']
          self.storage_energy_content.loc[t] = grid.net.storage['e_mwh']
          self.ev_soc.loc[t] = grid.net.load.ev_soc.loc[grid.ev_index]
          self.hp_demand_th.loc[t] = grid.net.load.hp_demand_th.loc[grid.hp_index]
          self.hp_soc.loc[t] = grid.net.load.hp_soc_mwh.loc[grid.hp_index]
          self.hp_cop.loc[t] = grid.net.load.hp_cop.loc[grid.hp_index]
          self.hp_hp_th.loc[t] = grid.net.load.hp_hp_th.loc[grid.hp_index]
          self.hp_tes_th.loc[t] = grid.net.load.hp_tes_th.loc[grid.hp_index]
          self.hp_tes_losses_th.loc[t] = grid.net.load.hp_tes_losses_th.loc[grid.hp_index]
          self.trafo_reactive_power.loc[t] = grid.net.res_trafo.q_hv_mvar
          self.v_pu_ext_grid.loc[t] = grid.net.ext_grid.vm_pu.values

  def write_dataframe_to_csv(self, mode, header, grid):
        self.vm_pu.round(3).to_csv(self.output_dir + 'res_bus_vm_pu.csv',
                                   mode=mode, header=header, index = True)
        self.li_lo.round(1).to_csv(self.output_dir + 'res_line_load_percent.csv',
                                   mode=mode, header=header, index = True)
        self.tr_lo.round(1).to_csv(self.output_dir + 'res_trafo_load_percent.csv',
                                   mode=mode, header=header, index = True)
        self.power.round(6).to_csv(self.output_dir + 'power_total_MW.csv',
                                   mode=mode, header=header, index = True)
        self.storage_active_power.round(6).to_csv(self.output_dir + 'storage_active_power_MW.csv',
                                                  mode=mode, header=header, index = True)
        self.storage_state_of_charge.round(6).to_csv(self.output_dir + 'storage_state_of_charge_percent.csv',
                                                  mode=mode, header=header, index = True) 
        self.trafo_active_power.round(6).to_csv(self.output_dir + 'trafo_active_power_MW.csv',
                                                  mode=mode, header=header, index = True)
        self.losses_active_power.round(6).to_csv(self.output_dir + 'losses_active_power_MW.csv',
                                                  mode=mode, header=header, index = True)
        self.curtailed_power_pv.round(6).to_csv(self.output_dir + 'curtailed_power_pv_MW.csv',
                                                  mode=mode, header=header, index = True)
        self.curtailed_power_load.round(6).to_csv(self.output_dir + 'curtailed_power_load_MW.csv',
                                                  mode=mode, header=header, index = True)
        if self.save_full_data == True:
          self.pv_active_power.round(6).to_csv(self.output_dir + 'pv_active_power_MW.csv',
                                               mode=mode, header=header, index = True)
          self.pv_reactive_power.round(6).to_csv(self.output_dir + 'pv_reactive_power_MW.csv',
                                               mode=mode, header=header, index = True)
          self.load_active_power.round(6).to_csv(self.output_dir + 'load_active_power_MW.csv',
                                               mode=mode, header=header, index = True)
          self.load_reactive_power.round(6).to_csv(self.output_dir + 'load_reactive_power_MW.csv',
                                               mode=mode, header=header, index = True)
          self.storage_energy_content.round(6).to_csv(self.output_dir + 'storage_energy_content_MWh.csv',
                                                  mode=mode, header=header, index = True)
          self.ev_soc.round(3).to_csv(self.output_dir + 'ev_soc.csv',
                                               mode=mode, header=header, index = True)
          self.hp_demand_th.round(6).to_csv(self.output_dir + 'hp_demand_th.csv',
                                               mode=mode, header=header, index = True)
          self.hp_soc.round(6).to_csv(self.output_dir + 'hp_soc.csv',
                                               mode=mode, header=header, index = True)
          self.hp_cop.round(3).to_csv(self.output_dir + 'hp_cop.csv',
                                               mode=mode, header=header, index = True)
          self.hp_hp_th.round(6).to_csv(self.output_dir + 'hp_hp_th.csv',
                                               mode=mode, header=header, index = True)
          self.hp_tes_th.round(6).to_csv(self.output_dir + 'hp_tes_th.csv',
                                               mode=mode, header=header, index = True)
          self.hp_tes_losses_th.round(6).to_csv(self.output_dir + 'hp_tes_losses_th.csv',
                                               mode=mode, header=header, index = True)
          self.trafo_reactive_power.round(6).to_csv(self.output_dir + 'trafo_reactive_power_MW.csv',
                                                  mode=mode, header=header, index = True)
          self.v_pu_ext_grid.round(3).to_csv(self.output_dir + 'v_pu_ext_grid.csv',
                                                  mode=mode, header=header, index = True)

        self.create_output_dataframes(grid)
