import os
import csv
import numpy as np
import pandas as pd
import datetime

class OutputDataHandler():

  def __init__(self, save_full_data = False, control_parameter=None, grid=None):
    self.save_full_data = save_full_data
    self.control_parameter = control_parameter
    self.grid = grid

  #########################
  ### create output_dir ###
  #########################
  def create_output_dir(self, net_name, scenario_frame, time_scope):
        self.scenario_frame = scenario_frame
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

        if self.control_parameter != None:
          self.write_control_parameter_to_csv()
        if self.grid != None:
          self.write_component_data_to_csv()
        
        return self.output_dir

  def write_control_parameter_to_csv(self):
    date = datetime.datetime.today()
    with open(self.output_dir + '00_simulation_date.csv', 'w') as f:
        f.write(str(date))

    with open(self.output_dir + '01_control_paramters.csv', 'w') as f:
      for key in self.control_parameter.keys():
        f.write("%s, %s\n"%(key,self.control_parameter[key]))

  def write_component_data_to_csv(self):
    is_pv  = 1 if self.scenario_frame[0] in [3,4,6,7,8,9] else 0
    is_bss = 1 if self.scenario_frame[0] in [6,8,9]       else 0
    is_hp  = 1 if self.scenario_frame[0] in [2,4,6,7,8,9] else 0
    is_tes = 1 if self.scenario_frame[0] in [7,8,9]       else 0
    is_ev  = 1 if self.scenario_frame[0] in [2,4,6,7,8,9] else 0

    # PV-P, BSS-P, BSS-E, HP-P, TES-E, EV-E, 
    df = pd.DataFrame(index=self.grid.net.sgen.index)
    df['PV_power']   = is_pv  * self.grid.net.sgen.installed_power / 1000 # MW
    df['BSS_power']  = is_bss * self.grid.net.storage.max_p_mw
    df['BSS_energy'] = is_bss * self.grid.net.storage.max_e_mwh
    df['HP_power']   = is_hp  * self.grid.net.load.hp_max_p_kw.loc[self.grid.hp_index].values
    df['TES_energy'] = is_tes * self.grid.net.load.hp_max_capacity_mwh.loc[self.grid.hp_index].values
    df['EV_energy']  = is_ev  * self.grid.net.load.ev_c_bat.loc[self.grid.ev_index].values / 1000 # MWh
    df.round(6).to_csv(self.output_dir + '02_component_data.csv', header=True, index = True)
    

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
        self.curtailed_power = pd.DataFrame(columns=grid.net.sgen.index)
        self.curtailed_power.index.name  = 'timestamp'
        self.pv_active_power = pd.DataFrame(columns=grid.net.sgen.index)
        self.pv_active_power.index.name = 'timestamp'
        self.load_active_power = pd.DataFrame(columns=grid.net.load.index)
        self.load_active_power.index.name = 'timestamp'
        self.load_active_power_flex = pd.DataFrame(columns=grid.load_index)#grid.net.load.index)
        self.load_active_power_flex.index.name = 'timestamp'
        self.bss_active_power_flex = pd.DataFrame(columns=grid.net.storage.index)
        self.bss_active_power_flex.index.name = 'timestamp'
        self.pv_reactive_power = pd.DataFrame(columns=grid.net.sgen.index)
        self.pv_reactive_power.index.name  = 'timestamp'
        self.load_reactive_power = pd.DataFrame(columns=grid.net.load.index)
        self.load_reactive_power.index.name = 'timestamp'
        self.v_pu_ext_grid = pd.DataFrame(columns=['v_pu'])
        self.v_pu_ext_grid.index.name  = 'timestamp'
        self.residual_load_no_grid = pd.DataFrame(columns=['residual load'])
        self.residual_load_no_grid.index.name = 'timestamp'
        if self.save_full_data == True:
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


  def write_output_into_dataframe(self, grid, t, grid_analysis):
        if grid_analysis == True:
            self.vm_pu.loc[t] = grid.net.res_bus.vm_pu
            self.li_lo.loc[t] = grid.net.res_line.loading_percent
            self.tr_lo.loc[t] = grid.net.res_trafo.loading_percent
            self.pv_reactive_power.loc[t] = grid.net.sgen['q_mvar']
            self.load_reactive_power.loc[t] = grid.net.load['q_mvar']
            self.v_pu_ext_grid.loc[t] = grid.net.ext_grid.vm_pu.values
        else:
            self.residual_load_no_grid.loc[t] = grid.net.load.p_mw.sum() - grid.net.sgen.p_mw.sum() + grid.net.storage['p_mw'].sum()
        self.power.loc[t] = [grid.net.load.p_mw[grid.load_index].sum(),
                             grid.net.sgen.p_mw.sum(),
                             grid.net.load.p_mw[grid.hp_index].sum(),
                             grid.net.load.p_mw[grid.ev_index].sum()]
        self.storage_active_power.loc[t] = grid.net.storage['p_mw']
        self.storage_state_of_charge.loc[t] = grid.net.storage['soc_percent']
        self.trafo_active_power.loc[t] = grid.net.res_trafo.p_hv_mw
        self.losses_active_power.loc[t] = [grid.net.res_trafo.pl_mw.sum(),grid.net.res_line.pl_mw.sum()]
        self.curtailed_power.loc[t] = (grid.curtailed_pv_power_df - \
                                     (grid.curtailed_load_power_df[grid.load_index] + \
                                      grid.curtailed_load_power_df[grid.hp_index].set_axis(grid.load_index, axis='index', inplace=False) + \
                                      grid.curtailed_load_power_df[grid.ev_index].set_axis(grid.load_index, axis='index', inplace=False)))
        self.pv_active_power.loc[t]   = grid.net.sgen['p_mw']
        self.load_active_power.loc[t] = grid.net.load['p_mw']
        self.load_active_power_flex.loc[t] = (grid.net.load.p_mw_flex[grid.hp_index].set_axis(grid.load_index, axis='index', inplace=False) + \
                                             grid.net.load.p_mw_flex[grid.ev_index].set_axis(grid.load_index, axis='index', inplace=False))
        self.bss_active_power_flex.loc[t] = grid.net.storage['p_mw_flex']
        if self.save_full_data == True:
          self.storage_energy_content.loc[t] = grid.net.storage['e_mwh']
          self.ev_soc.loc[t] = grid.net.load.ev_soc.loc[grid.ev_index]
          self.hp_demand_th.loc[t] = grid.net.load.hp_demand_th.loc[grid.hp_index]
          self.hp_soc.loc[t] = grid.net.load.hp_soc_mwh.loc[grid.hp_index]
          self.hp_cop.loc[t] = grid.net.load.hp_cop.loc[grid.hp_index]
          self.hp_hp_th.loc[t] = grid.net.load.hp_hp_th.loc[grid.hp_index]
          self.hp_tes_th.loc[t] = grid.net.load.hp_tes_th.loc[grid.hp_index]
          self.hp_tes_losses_th.loc[t] = grid.net.load.hp_tes_losses_th.loc[grid.hp_index]
          self.trafo_reactive_power.loc[t] = grid.net.res_trafo.q_hv_mvar

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
        self.curtailed_power.round(6).replace(0.0, np.nan).to_csv(self.output_dir + 'curtailed_power_MW.csv',
                                                  mode=mode, header=header, index = True)
        self.pv_active_power.round(6).to_csv(self.output_dir + 'pv_active_power_MW.csv',
                                                  mode=mode, header=header, index = True)
        self.load_active_power.round(6).to_csv(self.output_dir + 'load_active_power_MW.csv',
                                                  mode=mode, header=header, index = True)
        self.load_active_power_flex.round(6).replace(0.0, np.nan).to_csv(self.output_dir + 'load_active_power_flex_MW.csv',
                                                  mode=mode, header=header, index = True)
        self.bss_active_power_flex.round(6).replace(0.0, np.nan).to_csv(self.output_dir + 'bss_active_power_flex_MW.csv',
                                                  mode=mode, header=header, index = True)
        self.pv_reactive_power.round(6).to_csv(self.output_dir + 'pv_reactive_power_MW.csv',
                                                  mode=mode, header=header, index = True)
        self.load_reactive_power.round(6).to_csv(self.output_dir + 'load_reactive_power_MW.csv',
                                                  mode=mode, header=header, index = True)
        self.v_pu_ext_grid.round(3).to_csv(self.output_dir + 'v_pu_ext_grid.csv',
                                                  mode=mode, header=header, index = True)
        self.residual_load_no_grid.round(3).to_csv(self.output_dir + 'residual_load_no_grid.csv',
                                           mode=mode, header=header, index=True) #neu
        if self.save_full_data == True:
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

        self.create_output_dataframes(grid)
