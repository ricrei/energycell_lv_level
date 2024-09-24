import tools.tools as tt
import pandas as pd

class HHLcreator:

  def __init__(self, inputfolder, control_parameter, grid_analysis):
        self.inputfolder = inputfolder
        self.load_p_data_file = self.inputfolder + '11_p0_short.pbz2'
        if grid_analysis == True:
            self.load_q_data_file = self.inputfolder + '11_q0_short.pbz2'
        self.ec_size = control_parameter['EC_size']

  ###########################################
  ### Create Loads at each bus for all HP ###
  ###########################################
  def create_hh_load_at_each_bus(self, grid):
      # create hp-loads at each bus 
      for index in grid.component_buses.index:
          grid.net.load.name.loc[index] = 'load_'+str(grid.net.load.loc[index, "bus"])
          grid.net.load.type.loc[index] = 'load_'+str(index%74)

      return grid

  ##########################################
  ### load genearation and load profiles ###
  ##########################################
  def load_hhl_profiles(self, df, grid_analysis):
        ### load load profiles ###
        p0 = tt.decompress_pickle(self.load_p_data_file)
        if grid_analysis == True:
            q0 = tt.decompress_pickle(self.load_q_data_file)
        for i in range(0,74):
            df['load_'+str(i)+'_p'] = p0["p"+str(i)]/1000	# normalized to MW
            if grid_analysis == True:
                df['load_'+str(i)+'_q'] = q0["q"+str(i)]/1000	# normalized to MW

        return df
