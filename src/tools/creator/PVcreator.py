import numpy as np
import pandas as pd
import pandapower as pp

import tools.tools as tt

class PVcreator:

  def __init__(self, inputfolder):
    self.inputfolder = inputfolder
    self.pv_data_file = self.inputfolder + '12_pv_short.pbz2'

    # installed PV-power per roof-top side in kW, rural:18kW, village:16.7kW, suburban:11.6kW
    # rate: frequency of occurrence of pv-orientation
    self.pv_para = {'orientation' : [90, 100, 110, 120, 130, 140, 150, 160, 170, 180, 190, 200, 210, 220, 230, 240, 250, 260],
                        'rate' : pd.DataFrame([10.8, 4.8, 4.4, 4, 4, 4.4, 5.2, 6.3, 6.3, 10.8, 4.9, 4.7, 4.3, 4, 4.3, 5, 5.9, 5.9]),
                        'installed_power_scaling' : [2, 2, 2, 2, 2, 1, 1, 1, 1, 1, 1, 1, 1, 1, 2, 2, 2, 2], #[1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1],
                        'power_rural' : 18, 'power_village' : 16.7, 'power_suburban' : 11.6, 'power_urban': 10}
    self.pv_para_shared = {'orientation' : [180], #examplary parameters for single community PV plant
                        'installed_power_scaling' : [1],
                        'power' : 2000}
    #TODO: power urban has to be verified

    #########################################
    ### Mastermethod: choose pv position ###
    #########################################
  def create_pv_sgen(self, grid, pv_control):
    if pv_control in [None, 'qu', 'cos_phi']:
        grid = self.create_pv_sgen_at_each_bus(grid, pv_control)
    elif pv_control in ['qu_LVbus', 'cos_phi_LVbus']:
        grid = self.create_pv_sgen_at_lvbb(grid, pv_control)

    return grid

  ############################################################
  ### Create sGen and Loads at each bus for all PV, HP, EV ###
  ############################################################
  def create_pv_sgen_at_each_bus(self, grid, pv_control):
        # create sgen per load and set all values to zero
        # asign pv-orientation to every sgen
        grid = self.set_pv_distribution(grid)
        grid = self.total_installed_pv_power = self.get_installed_power_within_the_grid(grid, pv_control)
        return grid

  ###########################
  ### Create sGen at LVBB ###
  ###########################
  def create_pv_sgen_at_lvbb(self, grid, pv_control):
      # create sgen at lvbb and set all values to zero
      # create PV sgen at LVBB
      pp.create_sgen(grid.net, grid.net.trafo.lv_bus[0], 0.0,
                     name='pv_' + str(grid.net.trafo.lv_bus.sum()),
                     type='pv_180') #Todo: type ändern
      grid = self.total_installed_pv_power = self.get_installed_power_within_the_grid(grid, pv_control)

      return grid

  ############################################
  ### distribute PV systems within the net ###
  ############################################   
  def set_pv_distribution(self, grid):
            # calculate distribution of pv systems with different orientation
            n_pv_systems = grid.net.load.index.max() + 1
            pv_orientation_proberbility = self.pv_para['rate']/100
            n_pv_systems_orientation = pd.DataFrame(columns=['orientation', 'amount', 'decimal_amount', 'final_amount'])
            n_pv_systems_orientation['orientation'] = self.pv_para['orientation']      
            n_pv_systems_orientation['amount'] = n_pv_systems * pv_orientation_proberbility
            n_pv_systems_orientation['final_amount'] = n_pv_systems_orientation['amount'].apply(np.floor)
            n_pv_systems_orientation['decimal_amount'] = n_pv_systems_orientation['amount'] - n_pv_systems_orientation['final_amount']
            n_pv_systems_left = n_pv_systems - n_pv_systems_orientation['final_amount'].sum()
      
            n_pv_systems_orientation = n_pv_systems_orientation.sort_values(by=['decimal_amount'], ascending=False).reset_index(drop=True)

            i = 0
            while n_pv_systems_left > 0:
               n_pv_systems_orientation['final_amount'].loc[i] += 1
               n_pv_systems_left -= 1
               i += 1
            n_pv_systems_orientation = n_pv_systems_orientation.sort_values(by=['orientation'], ascending=True).reset_index(drop=True)
            n_pv_systems_to_distribute = n_pv_systems_orientation[['orientation', 'final_amount']]

            j = 0
            for index in grid.net.load.index:
                # create PV sgen at every load
                pp.create_sgen(grid.net, grid.net.load.loc[index, "bus"], 0.0, name='pv_'+str(grid.net.load.loc[index, "bus"]))
                grid.net.load.loc[index, "p_mw"] = 0.0
                # asign pv-orientation to every PV sgen
                if n_pv_systems_to_distribute.final_amount.sum() > 0:
                  if index%10 == 0 and n_pv_systems_to_distribute['final_amount'].loc[9] > 0:
                    grid.net.sgen.type.loc[index] = 'pv_180'
                    n_pv_systems_to_distribute['final_amount'].loc[9] -= 1
                  elif (index+5)%10 == 0 and n_pv_systems_to_distribute['final_amount'].loc[0] > 0:
                    grid.net.sgen.type.loc[index] = 'pv_90'
                    n_pv_systems_to_distribute['final_amount'].loc[0] -= 1
                  else:
                    for k in range(0,18):
                      i = (k + j)%18
                      if i != 0 and i !=9:
                        if n_pv_systems_to_distribute['final_amount'].loc[i] > 0:
                          grid.net.sgen.type.loc[index] = 'pv_' + str(n_pv_systems_to_distribute['orientation'][i])
                          n_pv_systems_to_distribute['final_amount'].loc[i] -= 1
                          j = i + 1
                          break
                        elif k == 17:
                          for l in [0, 9]:
                            if n_pv_systems_to_distribute['final_amount'].loc[l] > 0:
                              grid.net.sgen.type.loc[index] = 'pv_' + str(n_pv_systems_to_distribute['orientation'][l])
                              n_pv_systems_to_distribute['final_amount'].loc[l] -= 1
                              break
                else:
                  print('Error: No pv-system orientation to distrubute. Number of pv-systems by orientation does not match with number of sgen in the grid')
            if n_pv_systems_to_distribute['final_amount'].sum() != 0 or n_pv_systems_to_distribute['final_amount'].max() != 0:
              print('Assignment of PV-systems (orientation) to sgen failed.')

            return grid

  ##########################################
  ### load genearation and load profiles ###
  ##########################################
  def load_pv_profiles(self, df, category, pv_control):
        ### load pv profiles ###
        pv = tt.decompress_pickle(self.pv_data_file)

        # Define maximum installed pv-power per (roof-top) side (in kW)
        if pv_control in [None, 'qu', 'cos_phi']:
            pv_power_installed = self.pv_para['power_'+str(category)]
        elif pv_control in ['qu_LVbus', 'cos_phi_LVbus']:
            pv_power_installed = self.pv_para_shared['power']
        for i in range(0,len(self.pv_para['orientation'])):
              # calculate installed power per household and normalize timeseries to MW
              pv_dc_power = pv[self.pv_para['orientation'][i]]*pv_power_installed*self.pv_para['installed_power_scaling'][i]/1000
              # calculate active and reactive power of pv-system
              df['pv_'+str(self.pv_para['orientation'][i])+'_p'] = pv_dc_power
        return df


  #################################################
  ### get total installed power within the grid ###
  #################################################
  def get_installed_power_within_the_grid(self, grid, pv_control):
    df_power_by_orientation = pd.DataFrame(columns=['orientation', 'installed_power_scaling'], index=range(0,len(self.pv_para['orientation'])))
    df_power_by_orientation.orientation = ['pv_'+str(self.pv_para['orientation'][i]) for i in range(len(self.pv_para['orientation']))]
    df_power_by_orientation['installed_power_scaling'] = self.pv_para['installed_power_scaling']
    if pv_control in [None, 'qu', 'cos_phi']:
        df_power_by_orientation['power_per_orientation'] = df_power_by_orientation['installed_power_scaling']*self.pv_para['power_'+str(grid.category)]
    elif pv_control in ['qu_LVbus', 'cos_phi_LVbus']:
        df_power_by_orientation['power_per_orientation'] = df_power_by_orientation['installed_power_scaling'] * self.pv_para_shared['power'] # nur hierfür steht pv_control in Methoden
        #ToDO: Vielleicht doch lieber pv_power_shared in pv para aufnehmen und keine Variable pv_control?
    grid.total_installed_pv_power = 0
    grid.net.sgen['installed_power'] = 0
    index = 0
    for pv_type in grid.net.sgen.type:
      grid.net.sgen['installed_power'].loc[index] = int(df_power_by_orientation['power_per_orientation'][str(pv_type) == df_power_by_orientation['orientation']].values)
      index += 1
    grid.total_installed_pv_power = grid.net.sgen['installed_power'].sum()

    return grid
