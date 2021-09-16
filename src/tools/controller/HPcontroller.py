import numpy as np
import pandas as pd
import datetime as dt
from tools.controller.HPstorages import HPstorages

class HPcontroller:

  def __init__(self, grid, control='greedy'):
      self.set_hp = (grid.scenario in [2, 4, 5, 6])
      self.intervall_in_seconds = grid.time_scope['intervall_in_seconds']
      self.busses_num = len(grid.component_buses.index)

      if (control=='greedy' or control=='evu_lock' or control=='resi_load_driven' or control=='curative'):
          self.set_hp = (grid.scenario in [2, 4, 5, 51, 52, 6])

      if (control=='greedy' or control=='evu_lock' or control=='resi_load_driven' or control=='curative'):
        self.control = control
        self.cos_phi = .95
        self.tan_phi = np.tan(np.arccos(self.cos_phi))
      else:
        raise ValueError('The entered HP control is not a valid option.')

      if self.set_hp == True:
        if self.control == 'greedy':
          self.P_controller = HP_P_control_greedy(grid)
        if self.control == 'evu_lock':
          self.P_controller = HP_P_control_evu_lock(grid)          
        elif self.control == 'resi_load_driven':
          self.P_controller = HP_P_control_resi_load_driven(grid)    
        elif self.control == 'curative':
          raise ValueError('HP curative control is not implemented.')
      else:
        self.P_controller =  HP_P_control_no_hp(grid)

  def get_active_power(self, grid, d, t):
      return self.P_controller.pcontrol(grid, d, t)

  def get_reactive_power(self, grid, d, t):
      return self.P_controller.get_q(grid, d, t, self.tan_phi)


class HP_P_control:
  def __init__(self, grid):
      pass

  def pcontrol(self):
      pass

  def get_q(self, grid, d, t, tan_phi):
      return grid.net.load.loc[grid.hp_index, 'p_mw'] * tan_phi

class HP_P_control_no_hp(HP_P_control):

  def __init__(self, grid):
      super().__init__(grid)

  def pcontrol(self, grid, d, t):
      HP_P_control.pcontrol(self)
      return d.values*0


class HP_P_control_greedy(HP_P_control):

    def __init__(self, grid):
        super().__init__(grid)

    def pcontrol(self, grid, d, t):
        HP_P_control.pcontrol(self)
        return d.values


class HP_P_control_evu_lock(HP_P_control):

    def __init__(self, grid):
        super().__init__(grid)
        self.HP_storages = HPstorages()
        self.HP_storages.create_hp_storages(grid)

    def pcontrol(self, grid, d, t):
        
        time1 = t.time()
        hp_load_old = d.copy()
        hp_load_new = d.copy()
        evu_lock_active = False
        
        morningstart = dt.datetime(1970, 1, 1, 10, 45, 00)
        morningstop = dt.datetime(1970, 1, 1, 12, 15, 00)

        eveningstart = dt.datetime(1970, 1, 1, 17, 15, 00)
        eveningstop = dt.datetime(1970, 1, 1, 18, 45, 00)

        #morninglock = {'start_time' : '2017-01-05 00:00:00+08:29',
        #               'end_time'   : '2017-01-05 00:00:00+11:00'}
        #if (t >= morninglock['start_time']) & (t < morninglock['stop_time']) : 
        #if (t >= morninglock['start_time']) & (t < morninglock['stop_time']) : 

        if((t.time() > morningstart.time()) & (t.time() < morningstop.time())) :
            evu_lock_active = True
        if((t.time() > eveningstart.time()) & (t.time() < eveningstop.time())) :
            evu_lock_active = True
        
        print(t)
        print(self.HP_storages.get_level(grid, grid.hp_index).values)

        #when evu_lock active no demand from grid
        #feed_out from storage
        if(evu_lock_active) :
            print('storage unload')
            #print(self.HP_storages.get_level(grid, 99))
            self.HP_storages.feed_out(grid, grid.hp_index, hp_load_old.values)
            hp_load_new = hp_load_new * 0
        
        #feed_in to storage until comfort_level
        #feed_in maximum 1kW
        if(evu_lock_active == False) :
            print('storage reload')
            greater = self.HP_storages.greater('level', 'comfort_level')
            hp_load_new[greater.values] = hp_load_new[greater.values] + 0.001
            self.HP_storages.feed_in(grid, greater, 0.001)

        #HP_P_control.pcontrol(self)

        return hp_load_new.values

class HP_P_control_resi_load_driven(HP_P_control):

    def __init__(self, grid):
        super().__init__(grid)
        self.HP_storages = HPstorages()
        self.HP_storages.create_hp_storages(grid)

    def pcontrol(self, grid, d, t):

        hp_load_new = d.copy()

        hps = grid.net.load.loc[grid.hp_index]

        #residualload greater zero -> demand from grid
        #residualload less_equal zero -> feed into grid
        residual_load_per_hh =  grid.net.load.loc[grid.load_index, 'p_mw'].values + \
                                grid.net.load.loc[grid.hp_index, 'p_mw'].values + \
                                grid.net.load.loc[grid.ev_index, 'p_mw'].values - \
                                grid.net.sgen['p_mw'].values
                                
        hp_soc_kwh_ref = residual_load_per_hh
        hp_soc_kwh_ref[hps.hp_soc_kwh + hp_soc_kwh_ref > hps.hp_el_capacity_kwh] = \
            hps.hp_el_capacity_kwh[hps.hp_soc_kwh + hp_soc_kwh_ref > hps.hp_el_capacity_kwh]
        hp_soc_kwh_ref[hps.hp_soc_kwh + hp_soc_kwh_ref <= 0] = 0
        
        hps.p_mw = hp_soc_kwh_ref * 0.001
        hps.hp_soc_kwh += hp_soc_kwh_ref
        grid.net.load.loc[grid.hp_index] = hps

        '''
        df_resiload = pd.DataFrame(data = residual_load_per_hh)
        df_resiload = df_resiload.set_index(grid.hp_index)

        #check residualload greater zero -> demand from grid
        greater = np.greater(residual_load_per_hh, np.zeros(len(grid.component_buses)))
        #greater = df_resiload > 0
        
        #check residualload less_equal zero -> feed into grid
        less_equal = np.less_equal(residual_load_per_hh, np.zeros(len(grid.component_buses)))
        #less_equal = df_resiload <= 0

        #check for full storages
        #full = np.greater(self.HP_storages.get_level(grid, grid.hp_index).values,
        #                    self.HP_storages.get_capacity(grid, grid.hp_index).values)
        #full = self.HP_storages.get_level(grid, grid.hp_index) >= \
        #           self.HP_storages.get_capacity(grid, grid.hp_index)
        #full = hps.set_index(grid.load_index).hp_soc_kwh >= \
        #        hps.set_index(grid.load_index).hp_el_capacity_kwh
        full = np.greater(hps.set_index(grid.load_index).hp_soc_kwh.values, \
                hps.set_index(grid.load_index).hp_el_capacity_kwh.values)



        #check for empty storages
        #empty = np.less_equal(self.HP_storages.get_level(grid, grid.hp_index).values,
        #                      np.zeros(len(hp_load_new)))

        #empty = self.HP_storages.get_level(grid, grid.hp_index) <= \
        #            self.HP_storages.get_capacity(grid, grid.hp_index)        
        #empty = hps.set_index(grid.load_index).hp_soc_kwh <= \
        #        hps.set_index(grid.load_index).hp_el_capacity_kwh
        empty = np.less(hps.set_index(grid.load_index).hp_soc_kwh.values, \
                hps.set_index(grid.load_index).hp_el_capacity_kwh.values)
                

        #case1 resiload[greater] & storage[full] -> feed out from storage, reduce demand from grid
        case1 = greater & np.logical_not(empty)
        hp_load_new[case1] = d[case1] - 0.001
        df_case1 = pd.DataFrame(data = case1)
        #self.HP_storages.feed_out(grid, df_case1.set_index(grid.hp_index), 0.001)

        hps.set_index(grid.load_index).hp_soc_kwh[case1] = \
            hps.set_index(grid.load_index).hp_soc_kwh[case1]

        #case2 resiload[greater] & storage[empty] -> demand only from grid
        #case2 = greater & empty

        #case3 resiload[less_equal] & storage[full] -> feed in to grid
        #case3 = less_equal & full

        #case4 resiload[less_equal] & storage[empty] -> feed into storage
        case4 = less_equal & np.logical_not(full)
        #df_case4 = pd.DataFrame(data = case4)
        #hp_load_new[df_case4] = d[df_case4.set_index(grid.load_index)] + 0.001
        #self.HP_storages.feed_in(grid, df_case4, 0.001)


        hps.hp_soc_kwh[hps.hp_soc_kwh < hps.hp_el_capacity_kwh] = \
            hps.hp_soc_kwh + residual_load_per_hh
        '''

        #print(' ')
        print('Durchlauf')
        print(t)
        print(residual_load_per_hh)
        print(hps.hp_soc_kwh.values)
        #print(case1)
        #print(case2)
        #print(case4)
        #print(case4)
#        print(self.HP_storages.get_capacity(grid, grid.hp_index).values)
#        print(full)
#        print(empty)

        HP_P_control.pcontrol(self)

        return hp_load_new.values