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

class Grid:

  def __init__(self, net_name):
    self.net_name = net_name
    self.create_net()
    pp.runpp(self.net, algorithm='nr')  # Has be execute to get initial net.res_bus for Q(U)-control


  ######################
  ### create network ###
  ######################
  def create_net(self):
        #print('Create grid ...')
        # create net: only load without pv
        if self.net_name == "kerber_rural_1":
            self.net = pn.create_kerber_landnetz_freileitung_1()
            self.category = 'rural'
        elif self.net_name == "kerber_rural_2":
            self.net = pn.create_kerber_landnetz_freileitung_2()
            self.category = 'rural'
        elif self.net_name == "kerber_rural_3":
            self.net = pn.create_kerber_landnetz_kabel_1()
            self.category = 'rural'
        elif self.net_name == "kerber_rural_4":
            self.net = pn.create_kerber_landnetz_kabel_2()
            self.category = 'rural'
        elif self.net_name == "kerber_village":
            self.net = pn.create_kerber_dorfnetz()
            self.category = 'village'
        elif self.net_name == "kerber_suburb_1":
            self.net = pn.create_kerber_vorstadtnetz_kabel_1()
            self.category = 'suburban'
        elif self.net_name == "kerber_suburb_2":
            self.net = pn.create_kerber_vorstadtnetz_kabel_2()
            self.category = 'suburban'
        elif self.net_name == "simbench_rural_1":
            self.net = sb.get_simbench_net('1-LV-rural1--0-sw')
            self.category = 'rural'
        elif self.net_name == "simbench_rural_2":
            self.net = sb.get_simbench_net('1-LV-rural2--0-sw')
            self.category = 'rural'
        elif self.net_name == "simbench_rural_3":
            self.net = sb.get_simbench_net('1-LV-rural3--0-sw')
            self.category = 'rural'
        elif self.net_name == "simbench_suburb_4":
            self.net = sb.get_simbench_net('1-LV-semiurb4--0-sw')
            self.category = 'suburban'
        elif self.net_name == "simbench_suburb_5":
            self.net = sb.get_simbench_net('1-LV-semiurb5--0-sw')
            self.category = 'suburban'
        elif self.net_name == "simbench_urban_6":
            self.net = sb.get_simbench_net('1-LV-urban6--0-sw')
            self.category = 'urban'
        else:
            raise NameError('Hint: No Network found. Please check net_name')

        # Set vm_pu of external grid
        #print(self.net.ext_grid.vm_pu)
        self.net.ext_grid.vm_pu = 1.0

        # if there are any sgen's within the original network -> remove them first
        for index in self.net.sgen.index:
          self.net.sgen.drop(index=index, inplace=True)

        # Run diagnostic if there are problems regarding powerflow
        #pp.diagnostic(self.net, report_style='detailed', warnings_only=False)

  def get_component_index(self):
        self.pv_index = self.net.sgen.index
        self.load_index = self.net.load.index[self.net.load.type.str.contains('load')]
        self.hp_index = self.net.load.index[self.net.load.type.str.contains('hp')]
        self.ev_index = self.net.load.index[self.net.load.type.str.contains('ev')]

  def get_label_of_each_component(self):
      self.label_pv = self.net.sgen.type.loc[self.pv_index]
      self.label_pv_p = self.label_pv + '_p'
      self.label_pv_q = self.label_pv + '_q'

      self.label_load_p = [self.net.load.type[i] + '_p' for i in self.load_index]
      self.label_load_q = [self.net.load.type[i] + '_q' for i in self.load_index]

      self.label_hp_p = [self.net.load.type[i] + '_p' for i in self.hp_index]
      self.label_hp_q = [self.net.load.type[i] + '_q' for i in self.hp_index]

      self.label_ev = [self.net.load.type[i] for i in self.ev_index]
