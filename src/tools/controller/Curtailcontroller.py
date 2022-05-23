import numpy as np
import pandas as pd
import math
import sys

class Curtailcontroller:

  def __init__(self, grid, set_curtailment):
    self.set_curtail = set_curtailment

    if self.set_curtail == True:
      self.curtailment = Curtailment(grid)
    elif self.set_curtail == False:
      self.curtailment = NO_Curtailment()
    else:
      raise ValueError('Curtailment must be 1 or 0. Defined in scenario[1].')

  def curtail(self, grid, t):
    grid = self.curtailment.curtail(grid, t)

    return grid


class CurtailmentCommunityStorage_at_LVbusbar:
  def __init__(self):
    pass

  def get_residualload_p_per_household(self, grid):
    p_res = grid.net.load.loc[grid.load_index, 'p_mw'].values + \
            grid.net.load.loc[grid.hp_index, 'p_mw'].values + \
            grid.net.load.loc[grid.ev_index, 'p_mw'].values - \
            grid.net.sgen['p_mw'].values
    return p_res

  def curtail_storage_power(self, grid):
   p_bss_down = grid.net.storage.p_mw.copy()
   grid.net.storage.p_mw = 0
   s_res, p_res = grid.get_residualload_s_sum()

   if grid.s_trafo_power < -s_res: # Fall Trafoüberlastung bei Solarüberschuss
     # Speicherleistung wird zurückgesetzt und neu berechnet. 26.01.2022
     q_res_to_the_power_of_2 = s_res**2 - p_res**2
     if q_res_to_the_power_of_2 < grid.s_trafo_power**2: 
       p_trafo_max = (grid.s_trafo_power**2 - q_res_to_the_power_of_2)**(.5)
     else:
       p_trafo_max = 0
     grid.net.storage.p_mw = -(p_res + p_trafo_max)
     p_bss_down -= grid.net.storage.p_mw
     if grid.net.storage.soc_percent[0] < 100:
       grid.net.storage.e_mwh -= p_bss_down*grid.time_scope['intervall_in_seconds']/3600
       grid.net.storage.soc_percent = (grid.net.storage.e_mwh / grid.net.storage.max_e_mwh) * 100 # [%]
     else:
       grid.net.storage.p_mw = 0
       grid.net.storage.e_mwh = grid.net.storage.max_e_mwh
       grid.net.storage.soc_percent = 100

   else:
     grid.net.storage.p_mw = p_bss_down

   return grid

class CurtailmentCommunityStorage_in_feeder:
  def __init__(self):
    pass

  def get_residualload_p_per_household(self, grid):
    p_res = grid.net.load.loc[grid.load_index, 'p_mw'].values + \
            grid.net.load.loc[grid.hp_index, 'p_mw'].values + \
            grid.net.load.loc[grid.ev_index, 'p_mw'].values - \
            grid.net.sgen['p_mw'].values
    return p_res

  def curtail_storage_power(self, grid):
   return grid


class CurtailmentHomeStorage:
  def __init__(self):
    pass

  def get_residualload_p_per_household(self, grid):
    p_res = grid.net.load.loc[grid.load_index, 'p_mw'].values + \
            grid.net.load.loc[grid.hp_index, 'p_mw'].values + \
            grid.net.load.loc[grid.ev_index, 'p_mw'].values - \
            grid.net.sgen['p_mw'].values + \
            grid.net.storage['p_mw'].values
    return p_res

  def curtail_storage_power(self, grid):
    return grid

class Curtailment:

  def __init__(self, grid):
    self.trafo_power = grid.net.trafo.sn_mva.sum()
    self.sf_pv =  1#.95 # safty factor
    self.sf_load = 1#.95 # safty factor
    if grid.scenario[2] in [4]:
      self.Curtailment_regarding_Storage = CurtailmentCommunityStorage_at_LVbusbar()
    elif grid.scenario[2] in [5]:
      self.Curtailment_regarding_Storage = CurtailmentCommunityStorage_in_feeder()
    else:
      self.Curtailment_regarding_Storage = CurtailmentHomeStorage()

  def curtail(self,grid, t):

    res_s, res_p = grid.get_residualload_s_sum()
    #print(res_s)

    grid.curtailed_pv_power_df = grid.net.sgen.p_mw*0 #new
    grid.curtailed_load_power_df = grid.net.load.p_mw*0 #new

    # Calculate curtail_factor_trafo
    res_s, res_p = grid.get_residualload_s_sum()
    res_p_HH = self.Curtailment_regarding_Storage.get_residualload_p_per_household(grid)
    curtail_factor_trafo = 1
    if (-res_s > self.trafo_power*self.sf_pv):
      #print('Trafo PV')
      total_pv_power = (grid.net.sgen.p_mw[res_p_HH < 0].sum()**2 + grid.net.sgen[res_p_HH < 0].q_mvar.sum()**2)**.5
      curtail_power = -res_s - self.trafo_power*self.sf_pv
      curtail_factor_trafo = (1 - curtail_power/total_pv_power)
    if (res_s > self.trafo_power*self.sf_load):
      #print('Trafo Load')
      res_p_HH = np.concatenate((res_p_HH, res_p_HH, res_p_HH))
      total_load_power = (grid.net.load.p_mw[res_p_HH > 0].sum()**2 + grid.net.load.q_mvar[res_p_HH > 0].sum()**2)**.5
      curtail_power = res_s - self.trafo_power*self.sf_load
      curtail_factor_trafo = (1 - curtail_power/total_load_power)

    # Lineoverloading
    for i in range(1,grid.feeder['n_feeder']+1):
       load_index = grid.feeder['load_index_in_feeder'].loc[i]['load_index']
       sgen_index = grid.feeder['sgen_index_in_feeder'].loc[i]['sgen_index']
       storage_index = grid.feeder['storage_index_in_feeder'].loc[i]['storage_index']
       p_res_feeder = grid.net.load.p_mw.loc[load_index].sum()   - grid.net.sgen.p_mw.loc[sgen_index].sum()   + grid.net.storage.p_mw.loc[storage_index].sum()
       q_res_feeder = grid.net.load.q_mvar.loc[load_index].sum() - grid.net.sgen.q_mvar.loc[sgen_index].sum() + grid.net.storage.q_mvar.loc[storage_index].sum()
       s_res_feeder = (p_res_feeder**2 + q_res_feeder**2)**.5

       delta_pv_power = 0
       i_line = 0

       bus1 = grid.monitored_lines.to_bus[grid.monitored_lines.feeder == i].values
       bus2 = grid.monitored_lines.from_bus[grid.monitored_lines.feeder == i].values

       v1 = grid.net.res_bus.vm_pu[bus1].values*.4
       v2 = grid.net.res_bus.vm_pu[bus2].values*.4

       i_line_1 = s_res_feeder/(3**.5 * v1)
       i_line_2 = s_res_feeder/(3**.5 * v2)

       i_line = np.array([i_line_1, i_line_2]).max()

       if i_line > grid.monitored_lines.max_i_ka[grid.monitored_lines.feeder == i].values:
         #print('i_line: ' + str(i_line) + 'kA')
         curtail_factor_line = grid.monitored_lines.max_i_ka[grid.monitored_lines.feeder == i].values/i_line
         if curtail_factor_line < curtail_factor_trafo:
          if p_res_feeder <= 0:
           #print('Line PV')
           delta_pv_power_active_df = grid.net.sgen.p_mw[sgen_index].copy()
           grid.net.sgen.p_mw[sgen_index] = grid.net.sgen.p_mw[sgen_index].copy()*curtail_factor_line     + grid.net.load.p_mw.loc[load_index].copy().sum()*(1-curtail_factor_line)/len(sgen_index)
           grid.net.sgen.q_mvar[sgen_index] = grid.net.sgen.q_mvar[sgen_index].copy()*curtail_factor_line + grid.net.load.q_mvar.loc[load_index].copy().sum()*(1-curtail_factor_line)/len(sgen_index)
           delta_pv_power_active_df -= grid.net.sgen.p_mw[sgen_index].copy()
           grid.curtailed_pv_power_df[sgen_index] += delta_pv_power_active_df
           grid = self.Curtailment_regarding_Storage.curtail_storage_power(grid)
          else:
           #print('Line Load')
           grid.curtailed_load_power += float(grid.net.load.p_mw[load_index].sum()*(1-curtail_factor_line))
           grid.net.load.p_mw[load_index] = grid.net.load.p_mw[load_index]*curtail_factor_line
           grid.net.load.q_mvar[load_index] = grid.net.load.q_mvar[load_index]*curtail_factor_line
    
    # Trafo overloading
    res_s, res_p = grid.get_residualload_s_sum()
    res_p_HH = self.Curtailment_regarding_Storage.get_residualload_p_per_household(grid)
    if (-res_s > self.trafo_power*self.sf_pv):
      #print('Trafo PV')
      total_pv_power = (grid.net.sgen.p_mw[res_p_HH < 0].sum()**2 + grid.net.sgen.q_mvar[res_p_HH < 0].sum()**2)**.5
      total_pv_power_mw_df = grid.net.sgen.p_mw.copy()

      curtail_power = -res_s - self.trafo_power*self.sf_pv
      curtail_factor_trafo = (1 - curtail_power/total_pv_power)

      grid.net.sgen.p_mw[res_p_HH < 0] = grid.net.sgen.p_mw[res_p_HH < 0] * curtail_factor_trafo
      grid.net.sgen.q_mvar[res_p_HH < 0] = grid.net.sgen.q_mvar[res_p_HH < 0] * curtail_factor_trafo
      grid.curtailed_pv_power_df += total_pv_power_mw_df - grid.net.sgen.p_mw.copy()

    if (res_s > self.trafo_power*self.sf_load):
      #print('Trafo Load')
      res_p_HH = np.concatenate((res_p_HH, res_p_HH, res_p_HH))
      total_load_power = (grid.net.load.p_mw[res_p_HH > 0].sum()**2 + grid.net.load.q_mvar[res_p_HH > 0].sum()**2)**.5
      #print(res_s)
      total_load_power_mw_df = grid.net.load.p_mw.copy()
      curtail_power = res_s - self.trafo_power*self.sf_load
      curtail_factor_trafo = (1 - curtail_power/total_load_power)

      grid.net.load.p_mw[res_p_HH > 0] = grid.net.load.p_mw[res_p_HH > 0] * curtail_factor_trafo
      grid.net.load.q_mvar[res_p_HH > 0] = grid.net.load.q_mvar[res_p_HH > 0] * curtail_factor_trafo
      grid.curtailed_load_power_df += total_load_power_mw_df - grid.net.load.p_mw.copy()
      if total_load_power == 0.0:
        print('Warning: total_load_power == ' + str(total_load_power) + ' in ' + str(grid.scenario) + ' and ' + str(grid.time_scope) + ' at ' + str(t) + ' in ' + str(grid.net_name))
    
    return grid

class NO_Curtailment:
  def __init__(self):
    pass
  def curtail(self,grid, t):
    grid.curtailed_pv_power_df = grid.net.sgen.p_mw*0 #new
    grid.curtailed_load_power_df = grid.net.load.p_mw*0 #new
    return grid
