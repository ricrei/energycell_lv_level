import os
import csv
import time
import numpy as np
import pandas as pd
import pandapower as pp
import pandapower.networks as pn
import pandapower.toolbox as tb
import simbench as sb
import tools.progress as prog
import tools.tools as tt

import bz2
import _pickle as cPickle

class PVcreator:

  def __init__(self, set_pv):
    self.set_pv = set_pv
    # installed PV-power per roof-top side in kW, rural:18kW, village:16.7kW, suburban:11.6kW
    # rate: frequency of occurrence of pv-orientation
    self.pv_para = {'orientation' : [90, 100, 110, 120, 130, 140, 150, 160, 170, 180, 190, 200, 210, 220, 230, 240, 250, 260],
                        'rate' : pd.DataFrame([10.8, 4.8, 4.4, 4, 4, 4.4, 5.2, 6.3, 6.3, 10.8, 4.9, 4.7, 4.3, 4, 4.3, 5, 5.9, 5.9]),
                        'installed_power_scaling' : [2, 2, 2, 2, 2, 1, 1, 1, 1, 1, 1, 1, 1, 1, 2, 2, 2, 2], #[1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1],
                        'power_rural' : 18, 'power_village' : 16.7, 'power_suburban' : 11.6, 'power_urban': 10,
                        'cos_phi' : .95,
                        'q_u_cont': True, 'tan_phi' : np.tan(np.arccos(.9)), 'U1' : .93, 'U2' : .97, 'U3' : 1.03, 'U4' : 1.07}
    #TODO: power urban has to be verified


  ############################################################
  ### Create sGen and Loads at each bus for all PV, HP, EV ###
  ############################################################
  def create_pv_sgen_at_each_bus(self, grid):
        # create sgen per load and set all values to zero
        # asign pv-orientaiton to every sgen
        if self.set_pv == True:
          return self.set_pv_distribution(grid)
        else:
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
  def load_pv_profiles(self, df, pv_data_file, category):
        ### load pv profiles ###
        pv = tt.decompress_pickle(pv_data_file)

        # Define maximum installed pv-power per roof-top side (in kW)
        pv_power_installed = self.pv_para['power_'+str(category)]
        cos_phi = self.pv_para['cos_phi']
        for i in range(0,len(self.pv_para['orientation'])):
              # calculate installed power per household and normalize timeseries to MW
              pv_dc_power = pv[str(self.pv_para['orientation'][i])]*pv_power_installed*self.pv_para['installed_power_scaling'][i]/1000
              # calculate active and reactive power of pv-system
              df['pv_'+str(self.pv_para['orientation'][i])+'_p'] = pv_dc_power
              df['pv_'+str(self.pv_para['orientation'][i])+'_q'] = -pv_dc_power*np.tan(np.arccos(cos_phi))
        return df

