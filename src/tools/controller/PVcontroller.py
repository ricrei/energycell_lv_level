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

class PVcontroller:

  def __init__(self, grid):
      self.control_q_u_init(grid)
      # 'control': 'qu', 'cos_phi'
      self.pv_para = {'control' : 'qu',
                      'cos_phi' : .9,
                      'U1' : .93, 'U2' : .97, 'U3' : 1.03, 'U4' : 1.07}
      self.pv_para['tan_phi'] = np.tan(np.arccos(self.pv_para['cos_phi']))

  def control_cos_phi(self, grid):
      grid.net.sgen["q_mvar"] = -1*grid.net.sgen["p_mw"]*self.pv_para['tan_phi']
      return grid

  def control_q_u_init(self, grid):
      self.t_minus_x = pd.DataFrame()
      self.t_minus_x['q_t-1'] = grid.net.sgen['q_mvar']
      #self.t_minus_x['q_t-2'] = grid.net.sgen['q_mvar']
      #self.t_minus_x['q_t-3'] = grid.net.sgen['q_mvar']
      #self.t_minus_x['q_t-4'] = grid.net.sgen['q_mvar']
      #self.t_minus_x['q_t-5'] = grid.net.sgen['q_mvar']
      self.t_minus_x['p_t-1'] = grid.net.sgen['p_mw']
      self.t_minus_x['v_t-1'] = grid.net.sgen['bus']*0 + 1.0
      #self.t_minus_x['v_t-2'] = grid.net.sgen['bus']*0 + 1.0
      #self.t_minus_x['v_t-3'] = grid.net.sgen['bus']*0 + 1.0
      #self.t_minus_x['v_t-4'] = grid.net.sgen['bus']*0 + 1.0
      #self.t_minus_x['v_t-5'] = grid.net.sgen['bus']*0 + 1.0

  def control_q_u(self, grid):
      a = .2
      q_sgen_t = (self.t_minus_x['q_t-1'])#+self.t_minus_x['q_t-2']+self.t_minus_x['q_t-3']+self.t_minus_x['q_t-4']+self.t_minus_x['q_t-5'])/5
      v = (self.t_minus_x['v_t-1'])#+self.t_minus_x['v_t-2']+self.t_minus_x['v_t-3']+self.t_minus_x['v_t-4']+self.t_minus_x['v_t-5'])/5
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

  def get_v_of_last_timestep(self, v_buses):
      self.t_minus_x['v_t-1'] = v_buses

  def calculate_past_time_steps(self, grid):
      #self.t_minus_x['v_t-5'] = self.t_minus_x['v_t-4']
      #self.t_minus_x['v_t-4'] = self.t_minus_x['v_t-3']
      #self.t_minus_x['v_t-3'] = self.t_minus_x['v_t-2']
      #self.t_minus_x['v_t-2'] = self.t_minus_x['v_t-1']
      #self.t_minus_x['q_t-5'] = self.t_minus_x['q_t-4']
      #self.t_minus_x['q_t-4'] = self.t_minus_x['q_t-3']
      #self.t_minus_x['q_t-3'] = self.t_minus_x['q_t-2']
      #self.t_minus_x['q_t-2'] = self.t_minus_x['q_t-1']
      self.t_minus_x['q_t-1'] = grid.net.sgen['q_mvar']
      self.t_minus_x['p_t-1'] = grid.net.sgen['p_mw']
