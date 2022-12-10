import numpy as np
import pandapower as pp

import tools.tools as tt

class HPcreator:

  def __init__(self, inputfolder, control_parameter, scenario):
        self.inputfolder = inputfolder
        self.scenario = scenario

        ## choose hp_short_sfhXXX in case of scenario A, B, C
        ## In case of default choose hp_short
        if (self.scenario[0] == 'A'):
          self.hp_data_file = self.inputfolder + '13_hp_short_sfh15.pbz2'
        elif (self.scenario[0] == 'B'):
          self.hp_data_file = self.inputfolder + '13_hp_short_sfh45.pbz2'
        elif (self.scenario[0] == 'C'):
          self.hp_data_file = self.inputfolder + '13_hp_short_sfh100.pbz2'
        else:
          self.hp_data_file = self.inputfolder + '13_hp_short.pbz2'        
         
        self.hp = tt.decompress_pickle(self.hp_data_file)
        self.hp_para = {}
        
        ##obsolet?
        #self.hp_para['hp_types'] = self.hp.columns[self.hp.columns.str.contains('Demand_el_')]
        
        #in case of hp_tes_scenarios use only air_sourced_hp
        if (self.scenario[0] in ['A', 'B', 'C']) :
          #Select only air_spurced hp
          self.hp_para['hp_types'] = self.hp.columns[self.hp.columns.str.contains('_Air') & \
                          self.hp.columns.str.contains('Demand_th_')]
        #in default use air_sourced and ground_sourced
        else :
          self.hp_para['hp_types'] = self.hp.columns[self.hp.columns.str.contains('Demand_th_')]
      

  ###########################################
  ### Create Loads at each bus for all HP ###
  ###########################################
  def create_hp_load_at_each_bus(self, grid):
      if (grid.category == 'rural') or (grid.category == 'village') or (grid.category == 'suburban'):
          self.hp_para['hp_types'] = self.hp_para['hp_types'][self.hp_para['hp_types'].str.contains('DE_HEF')]
      elif (grid.category == 'urban'):
          self.hp_para['hp_types'] = self.hp_para['hp_types'][self.hp_para['hp_types'].str.contains('DE_HMF')]
      else:
          raise ValueError('No valid grid.category defined. Not able to choose HP type.')

      # create hp-loads at each bus
      for index in grid.component_buses.index:
          # calculate distribution of heatpump types and building types within the grid
          pp.create_load(grid.net, grid.net.load.loc[index, "bus"], 0.0, \
                         name='hp_'+str(grid.net.load.loc[index, "bus"]), \
                             type='hp_'+self.hp_para['hp_types'][index%len(self.hp_para['hp_types'])])

      #create columns for HPs grid.net.load
      grid.net.load['hp_cop'] = np.nan#4
      grid.net.load['hp_demand_th'] = np.nan
      grid.net.load['hp_hp_th'] = np.nan
      grid.net.load['hp_tes_th'] = np.nan
      grid.net.load['hp_tes_losses_th'] = np.nan

      #print(grid.net.load['type'].head())

      return grid

  ##########################################
  ### load genearation and load profiles ###
  ##########################################
  def load_hp_profiles(self, df):
        for hp_type in self.hp_para['hp_types']:
            df['hp_'+hp_type+'_p'] = self.hp[hp_type]/1000 # normalized to MW
        return df
