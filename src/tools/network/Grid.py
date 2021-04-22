import pandapower as pp
import pandapower.networks as pn
import simbench as sb

class Grid:

  def __init__(self, net_name, scenario, time_scope):
    self.time_scope = time_scope
    self.scenario = scenario
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
            self.rename_all_buses()
        elif self.net_name == "simbench_rural_2":
            self.net = sb.get_simbench_net('1-LV-rural2--0-sw')
            self.category = 'rural'
            self.rename_all_buses()
        elif self.net_name == "simbench_rural_3":
            self.net = sb.get_simbench_net('1-LV-rural3--0-sw')
            self.category = 'rural'
            self.rename_all_buses()
        elif self.net_name == "simbench_suburb_4":
            self.net = sb.get_simbench_net('1-LV-semiurb4--0-sw')
            self.category = 'suburban'
            self.rename_all_buses()
        elif self.net_name == "simbench_suburb_5":
            self.net = sb.get_simbench_net('1-LV-semiurb5--0-sw')
            self.category = 'suburban'
            self.rename_all_buses()
        elif self.net_name == "simbench_urban_6":
            self.net = sb.get_simbench_net('1-LV-urban6--0-sw')
            self.category = 'urban'
            self.rename_all_buses()
        elif self.net_name == "test_net_one_load_branch":
            self.net = self.create_test_net_one_load_branch()
            self.category = 'rural'
        else:
            raise NameError('Hint: No Network found. Please check net_name')

        # Set vm_pu of external grid
        #print(self.net.ext_grid.vm_pu)
        self.net.ext_grid.vm_pu = 1.0

        # if there are any sgen's within the original network -> remove them first
        for index in self.net.sgen.index:
          self.net.sgen.drop(index=index, inplace=True)

        # needed to create HHL, HP, EV and BSS as each bus
        self.component_buses = self.net.load.bus

        # Run diagnostic if there are problems regarding powerflow
        #pp.diagnostic(self.net, report_style='detailed', warnings_only=False)

  def get_component_index(self):
        self.pv_index = self.net.sgen.index
        self.load_index = self.net.load.index[self.net.load.type.str.contains('load')]
        self.hp_index = self.net.load.index[self.net.load.type.str.contains('hp')]
        self.ev_index = self.net.load.index[self.net.load.type.str.contains('ev')]
        self.bss_index = self.net.storage.index

  def get_label_of_each_component(self):
        self.label_pv = self.net.sgen.type.loc[self.pv_index]
        self.label_pv_p = self.label_pv + '_p'
        self.label_pv_q = self.label_pv + '_q'

        self.label_load_p = [self.net.load.type[i] + '_p' for i in self.load_index]
        self.label_load_q = [self.net.load.type[i] + '_q' for i in self.load_index]

        self.label_hp_p = [self.net.load.type[i] + '_p' for i in self.hp_index]
        self.label_hp_q = [self.net.load.type[i] + '_q' for i in self.hp_index]

        self.label_ev = [self.net.load.type[i] for i in self.ev_index]

  def rename_all_buses(self):
    for i in self.net.bus.index:
      self.net.bus.name[i] = str(self.net.bus.subnet[i]) + ' Bus ' + str(i)

  def create_test_net_one_load_branch(self):
    net = pp.create_empty_network(name='one_load_branch')
    b1 = pp.create_bus(net=net, vn_kv = 10, name='1')
    b2 = pp.create_bus(net=net, vn_kv =.4, name='2')
    b3 = pp.create_bus(net=net, vn_kv =.4, name='3')
    pp.create_ext_grid(net, b1, name='ext_grid')
    pp.create_line(net, b3, b2, 5, 'NAYY 4x50 SE', name='line')
    pp.create_load(net, b3, 0)
    pp.create_transformer(net, b1, b2, '0.25 MVA 10/0.4 kV', name='trafo')
    return net


  def get_vm_pu_ext_grid(self, grid):
    # considering the MV-grid valid voltage deviation of +-4%
    # assuming that the voltage magnitute depends on the residual load
    voltage_deviation_in_percent = .04
    nominal_voltage = 1.0
    residual_load = grid.net.load.p_mw.sum() - grid.net.sgen.p_mw.sum()
    voltage_deviation = -residual_load/(grid.total_installed_pv_power/1000)*voltage_deviation_in_percent

    return nominal_voltage + voltage_deviation
