import os
import csv
import time
import numpy as np
import pandas as pd
import pandapower as pp
import pandapower.networks as pn
import pandapower.toolbox as tb
import simbench as sb
import tools.tools as tt

import bz2
import _pickle as cPickle

class PVQcontrolQU:

  def __init__(self, grid, pv_para):
      self.pv_para = pv_para
      self.control_q_u_init(grid)

  def qcontrol(self, grid):
      grid = self.control_q_u(grid)
      return grid.net.sgen['q_mvar']

  def control_q_u_init(self, grid):
      self.t_minus_x = pd.DataFrame()
      self.t_minus_x['q_t-1'] = grid.net.sgen['q_mvar']
      self.t_minus_x['p_t-1'] = grid.net.sgen['p_mw']
      self.t_minus_x['v_t-1'] = grid.net.sgen['bus']*0 + 1.0

  def control_q_u(self, grid):
      a = .2
      q_sgen_t = (self.t_minus_x['q_t-1'])
      self.get_v_of_last_timestep(grid)
      v = (self.t_minus_x['v_t-1'])
      P = grid.net.sgen["p_mw"]
      Q = P * self.pv_para['tan_phi']
      m = Q/(self.pv_para['U2'] - self.pv_para['U1'])

      grid.net.sgen.loc[v <= self.pv_para['U1'], 'q_mvar'] = Q
      grid.net.sgen.loc[(v <= self.pv_para['U2']) & (v >= self.pv_para['U1']), 'q_mvar'] = -m*(v-self.pv_para['U2'])
      grid.net.sgen.loc[(v <= self.pv_para['U3']) & (v >= self.pv_para['U2']), 'q_mvar'] = 0
      grid.net.sgen.loc[(v <= self.pv_para['U4']) & (v >= self.pv_para['U3']), 'q_mvar'] = -m*(v-self.pv_para['U3'])
      grid.net.sgen.loc[v >= self.pv_para['U4'], 'q_mvar'] = -Q

      grid.net.sgen['q_mvar'] = a*grid.net.sgen['q_mvar'] + (1-a)*q_sgen_t
      grid.net.sgen.loc[grid.net.sgen['q_mvar'] < -Q, 'q_mvar'] = -Q
      grid.net.sgen.loc[grid.net.sgen['q_mvar'] >  Q, 'q_mvar'] = Q

      self.calculate_past_time_steps(grid)

      return grid

  def calculate_past_time_steps(self, grid):
      self.t_minus_x['q_t-1'] = grid.net.sgen['q_mvar']
      self.t_minus_x['p_t-1'] = grid.net.sgen['p_mw']

  def get_v_of_last_timestep(self, grid):
      v_buses = grid.net.res_bus.vm_pu[grid.net.sgen['bus']]
      self.t_minus_x['v_t-1'] = v_buses.values
