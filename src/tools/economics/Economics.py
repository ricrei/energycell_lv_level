import numpy as np 
import pandas as pd
import sys
import os

import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import seaborn as sns

import tools.tools as tt

import parameter_economics

class MainEconomics():
  def __init__(self, scenario, net_name, time_scope):
    self.scenario = scenario
    self.net_name = net_name
    self.time_scope = time_scope
    self.output_dir = len(self.time_scope) * [' ']
    self.conclusion_folder = os.path.join("./", "output-files/00_conclusion/")
    i = 0
    for t in self.time_scope:
      self.output_dir[i] = os.path.join("./", "output-files/"+''.join(str(num) for num in scenario)+"/"+str(net_name)+"/"+t['start_time'][0:10]+"_"+t['end_time'][0:10]+"_"+t['t_freq']+"/")
      if t['name'] == 'summer':
        self.output_dir_components = self.output_dir[i]
        scenario_reinforce = scenario.copy()
        scenario_reinforce[-1] = 1
        self.output_dir_components_grid_reinforce = os.path.join("./", "output-files/"+''.join(str(num) for num in scenario_reinforce)+"/"+str(net_name)+"/"+t['start_time'][0:10]+"_"+t['end_time'][0:10]+"_"+t['t_freq']+"/")
      i += 1

    self.power = pd.DataFrame()
    self.curtailed_power = pd.DataFrame()
    self.curtailed_power_pv = pd.DataFrame()
    self.curtailed_power_load = pd.DataFrame()
    self.losses_p = pd.DataFrame()
    self.storage_p = pd.DataFrame()
    self.trafo_p = pd.DataFrame()
    self.pv_p = pd.DataFrame()
    self.load_p = pd.DataFrame()
    self.bss_p_flex = pd.DataFrame()
    self.load_p_flex = pd.DataFrame()

    for output_dir in self.output_dir:
      self.power = self.concat_dfs(self.power, output_dir+'power_total_MW.csv')
      curtailed_power = self.read_data(output_dir+'curtailed_power_MW.csv')
      curtailed_power_pv = pd.DataFrame(columns=curtailed_power.columns, index=curtailed_power.index).fillna(0)
      curtailed_power_load = pd.DataFrame(columns=curtailed_power.columns, index=curtailed_power.index).fillna(0)
      curtailed_power_pv[curtailed_power >= 0] = curtailed_power[curtailed_power >= 0]
      curtailed_power_load[curtailed_power < 0] = -curtailed_power[curtailed_power < 0]
      self.curtailed_power_pv = pd.concat([self.curtailed_power_pv, curtailed_power_pv])
      self.curtailed_power_load = pd.concat([self.curtailed_power_load, curtailed_power_load])
      self.losses_p = self.concat_dfs(self.losses_p, output_dir+'losses_active_power_MW.csv')
      self.storage_p = self.concat_dfs(self.storage_p, output_dir+'storage_active_power_MW.csv')
      self.trafo_p = self.concat_dfs(self.trafo_p, output_dir+'trafo_active_power_MW.csv')
      self.pv_p = self.concat_dfs(self.pv_p, output_dir+'pv_active_power_MW.csv')
      self.load_p = self.concat_dfs(self.load_p, output_dir+'load_active_power_MW.csv')
      self.bss_p_flex = self.concat_dfs(self.bss_p_flex, output_dir+'bss_active_power_flex_MW.csv')
      self.load_p_flex = self.concat_dfs(self.load_p_flex, output_dir+'load_active_power_flex_MW.csv')

    self.component_parameter = pd.read_csv(self.output_dir_components + '02_component_data.csv', delimiter = ',', low_memory=False).drop('Unnamed: 0', axis=1)

    self.economics_folder = os.path.join("./", "output-files/001_economics/"+''.join(str(num) for num in scenario)+"/"+str(net_name)+"/")
    # Create output directory
    if not os.path.isdir(self.economics_folder):
      try:
        os.makedirs(self.economics_folder)
      except OSError:
        print("Error: Creation of output directory %s failed" % self.economics_folder)
      else:
        #print("Create outout directory %s" % self.economics_folder)
        pass

  def concat_dfs(self, df, new_output_dir):
    data = self.read_data(new_output_dir)
    data_list = [df, data]
    return pd.concat(data_list)

  def read_data(self, filename):
    data = pd.read_csv(filename, delimiter = ',', low_memory=False)
    data['timestamp'] = pd.to_datetime(data['timestamp'], utc=True)
    data = data.set_index('timestamp')

    return data

  def shorted_data(self, data, t_freq):
    data_shorted = data.resample(t_freq).mean()
    data_shorted = data_shorted.round(4)
    data_shorted.index = pd.DatetimeIndex(data_shorted.index, tz=None, ambiguous='infer')

    return data_shorted

  def energyflow(self):
    if self.scenario[2] in [0,1,2,3]:
      self.energyflow_HomeBSS()
    elif self.scenario[2] in [4,5]:
      self.energyflow_CommunityBSS()
    else:
      raise ValueError('No proper scenario to calculate energyflow.')

  def energyflow_HomeBSS(self):
    # plot config
    in_percent = True
    # development env
    test_case = 0

    projection_full_year = 365/(4*7) # 4 weeks and 7 days per week

    index = self.load_p.columns
    index_cut = int((int(self.load_p.columns[-1])+1)/3)
    load_index = index[0:index_cut]
    hp_index = index[index_cut:2*index_cut]
    ev_index = index[2*index_cut:3*index_cut]

    load_index = [str(i) for i in load_index]
    hp_index = [str(i) for i in hp_index]
    ev_index = [str(i) for i in ev_index]

    # HP-load per HH
    hp_load = self.load_p[hp_index]
    hp_load.columns = load_index
    # EV-load per HH
    ev_load = self.load_p[ev_index]
    ev_load.columns = load_index
    # HH-load per HH
    hh_load = self.load_p[load_index]

    load = hh_load + hp_load + ev_load
    # PV per HH
    pv = self.pv_p
    # BSS per HH
    bss = self.storage_p
    # total losses
    losses = self.losses_p.sum(axis=1)

    flex_bss =  self.bss_p_flex.fillna(0)
    flex_load = self.load_p_flex.fillna(0)

    # residual load per HH
    dE_HH = load - pv + bss

    flex_bss_LV = pd.DataFrame(index=bss.index, columns=bss.columns).fillna(0)
    flex_bss_LV[(dE_HH >= 0) & (flex_bss > 0) & (pv > load)] = dE_HH[(dE_HH >= 0) & (flex_bss > 0) & (pv > load)]
    flex_bss_LV[(dE_HH >= 0) & (flex_bss > 0) & (pv <= load)] = flex_bss[(dE_HH >= 0) & (flex_bss > 0) & (pv <= load)]

    # residual load whole grid
    dE_LV = pd.DataFrame(index=dE_HH.index, columns=dE_HH.columns)
    for c in dE_LV.columns:
      dE_LV[c] = dE_HH.sum(axis=1)# + losses

    # Sum of all PV excess
    sum_PV_LV_excess = pd.DataFrame(index=dE_HH.index, columns=dE_HH.columns).fillna(0)
    sum_Con_LV_lack = pd.DataFrame(index=dE_HH.index, columns=dE_HH.columns).fillna(0)
    for c in dE_LV.columns:
      sum_PV_LV_excess[c] = dE_HH[dE_HH < 0].sum(axis=1) # PV Überschuss gesamtes Netz
      sum_Con_LV_lack[c] = dE_HH[dE_HH >= 0].sum(axis=1) # Lastüberschuss gesamtes Netz

    # create
    Ec_MV = pd.DataFrame(index=pv.index, columns=pv.columns).fillna(0)
    Ec_LV = pd.DataFrame(index=pv.index, columns=pv.columns).fillna(0)
    Ec_self = pd.DataFrame(index=pv.index, columns=pv.columns).fillna(0)
    Eg_self = pd.DataFrame(index=pv.index, columns=pv.columns).fillna(0)
    Eg_LV = pd.DataFrame(index=pv.index, columns=pv.columns).fillna(0)
    Eg_MV = pd.DataFrame(index=pv.index, columns=pv.columns).fillna(0)
    Ecur_load = self.curtailed_power_load
    Ecur_pv = self.curtailed_power_pv

    ### Calculate how much of the pos and neg flexibility is included in self-sonsumption and locally traded energy
    Ec_self_flex = pd.DataFrame(index=dE_HH.index, columns=dE_HH.columns).fillna(0)
    Ec_LV_flex   = pd.DataFrame(index=dE_HH.index, columns=dE_HH.columns).fillna(0)
    Eg_self_flex = pd.DataFrame(index=dE_HH.index, columns=dE_HH.columns).fillna(0)
    Eg_LV_flex   = pd.DataFrame(index=dE_HH.index, columns=dE_HH.columns).fillna(0)

    # if PV+BSS gen greater than con -> calculate self consumption
    Ec_self[dE_HH < 0] = load[dE_HH < 0]
    Eg_self[dE_HH < 0] = load[dE_HH < 0]
    Ec_MV[dE_HH < 0] = 0
    Ec_LV[dE_HH < 0] = 0
    Eg_MV[(dE_HH < 0) & (dE_LV >= 0)] = 0
    Eg_LV[(dE_HH < 0) & (dE_LV >= 0)] = -dE_HH[(dE_HH < 0) & (dE_LV >= 0)]
    Eg_MV[(dE_HH < 0) & (dE_LV < 0)] = -dE_HH[(dE_HH < 0) & (dE_LV < 0)] / sum_PV_LV_excess[(dE_HH < 0) & (dE_LV < 0)] * dE_LV[(dE_HH < 0) & (dE_LV < 0)]
    Eg_LV[(dE_HH < 0) & (dE_LV < 0)] = -dE_HH[(dE_HH < 0) & (dE_LV < 0)] / sum_PV_LV_excess[(dE_HH < 0) & (dE_LV < 0)] * (sum_PV_LV_excess[(dE_HH < 0) & (dE_LV < 0)] - dE_LV[(dE_HH < 0) & (dE_LV < 0)])

    # if PV+BSS gen lower than con -> calculate self consumption
    Ec_self[dE_HH >= 0] = pv[dE_HH >= 0] - bss[dE_HH >= 0] + flex_bss_LV[dE_HH >= 0]
    Eg_self[dE_HH >= 0] = pv[dE_HH >= 0] - bss[dE_HH >= 0] + flex_bss_LV[dE_HH >= 0]
    Ec_MV[(dE_HH >= 0) & (dE_LV >= 0)] = dE_HH[(dE_HH >= 0) & (dE_LV >= 0)] / sum_Con_LV_lack[(dE_HH >= 0) & (dE_LV >= 0)] * dE_LV[(dE_HH >= 0) & (dE_LV >= 0)]
    Ec_LV[(dE_HH >= 0) & (dE_LV >= 0)] = dE_HH[(dE_HH >= 0) & (dE_LV >= 0)] / sum_Con_LV_lack[(dE_HH >= 0) & (dE_LV >= 0)] * (sum_Con_LV_lack[(dE_HH >= 0) & (dE_LV >= 0)] - dE_LV[(dE_HH >= 0) & (dE_LV >= 0)])
    Ec_MV[(dE_HH >= 0) & (dE_LV < 0)] = 0
    Ec_LV[(dE_HH >= 0) & (dE_LV < 0)] = dE_HH[(dE_HH >= 0) & (dE_LV < 0)]
    Eg_MV[dE_HH >= 0] = 0
    Eg_LV[dE_HH >= 0] = 0

    Ec_self[Ec_self < 0] = 0
    Eg_self[Eg_self < 0] = 0

    # Load Flexibility
    flex_load_pos = flex_load.copy() * 0
    flex_load_neg = flex_load.copy() * 0
    flex_load_pos[flex_load > 0] = flex_load[flex_load > 0] # Last wird vergrößert
    flex_load_neg[flex_load < 0] = flex_load[flex_load < 0] # Last wird verringert = Generation wird vergrößert

    Ec_LV_flex[  (pv < load) & (flex_load > 0) & (flex_load_pos > (load - pv))] += load - pv
    Ec_self_flex[(pv < load) & (flex_load > 0) & (flex_load_pos > (load - pv))] += flex_load_pos - (load - pv)

    Ec_LV_flex[  (pv < load) & (flex_load > 0) & (flex_load_pos < (load - pv))] += flex_load_pos
    Ec_self_flex[(pv < load) & (flex_load > 0) & (flex_load_pos < (load - pv))] += 0

    Ec_LV_flex[  (pv > load) & (flex_load > 0)] += 0
    Ec_self_flex[(pv > load) & (flex_load > 0)] += flex_load_pos


    Eg_LV_flex[  (flex_load < 0) & (pv < load)] += -flex_load_neg
    Eg_self_flex[(flex_load < 0) & (pv < load)] += 0

    Eg_LV_flex[  (flex_load < 0) & (pv > load)] += load-pv
    Eg_self_flex[(flex_load < 0) & (pv > load)] += -flex_load_neg - (load-pv)

    #Ec_self -= Ec_self_flex
    #Eg_self -= Eg_self_flex

    # BSS Flexibility
    Ec_LV_flex[(dE_HH >= 0) & (flex_bss > 0) & (pv > load) & (flex_bss <= dE_HH)] += flex_bss[(dE_HH >= 0) & (flex_bss > 0) & (pv > load) & (flex_bss <= dE_HH)]
    Ec_LV_flex[(dE_HH >= 0) & (flex_bss > 0) & (pv > load) & (flex_bss > dE_HH)] += dE_HH[(dE_HH >= 0) & (flex_bss > 0) & (pv > load) & (flex_bss > dE_HH)]

    Ec_LV_flex[(dE_HH >= 0) & (flex_bss > 0) & (pv <= load)] += flex_bss[(dE_HH >= 0) & (flex_bss > 0) & (pv <= load)]

    Eg_LV_flex[(dE_HH < 0) & (flex_bss < 0) & (pv <= load) & (flex_bss <= dE_HH)] += -flex_bss[(dE_HH < 0) & (flex_bss < 0) & (pv <= load) & (flex_bss <= dE_HH)]
    Eg_LV_flex[(dE_HH < 0) & (flex_bss < 0) & (pv <= load) & (flex_bss > dE_HH)] += -dE_HH[(dE_HH < 0) & (flex_bss < 0) & (pv <= load) & (flex_bss > dE_HH)]

    Eg_LV_flex[(dE_HH < 0) & (flex_bss < 0) & (pv > load)] += -flex_bss[(dE_HH < 0) & (flex_bss < 0) & (pv > load)]

    Ec_self_flex[(flex_bss > 0)] += flex_bss[(flex_bss > 0)] - Ec_LV_flex[(flex_bss > 0)]
    Eg_self_flex[(flex_bss < 0)] += -flex_bss[(flex_bss < 0)] - Eg_LV_flex[(flex_bss < 0)]

    Eg_LV_flex[Eg_LV_flex < 0] = 0

    Ec_LV -= Ec_LV_flex
    Eg_LV -= Eg_LV_flex

    E = pd.DataFrame(index=Ec_self.columns)

    E['Ec_self'] = Ec_self.sum()
    E['Eg_self'] = Eg_self.sum()
    E['Ec_MV'] = Ec_MV.sum()
    E['Ec_LV'] = Ec_LV.sum()
    E['Eg_MV'] = Eg_MV.sum()
    E['Eg_LV'] = Eg_LV.sum()
    E['Ecur_pv'] = Ecur_pv.sum()
    E['Ecur_load'] = Ecur_load.sum()
    E['Ec_LV_flex'] = Ec_LV_flex.sum()
    E['Eg_LV_flex'] = Eg_LV_flex.sum()
    E['Ec_self_flex'] = Ec_self_flex.sum()
    E['Eg_self_flex'] = Eg_self_flex.sum()

    if test_case == True:

      flex_bss_pos = flex_bss*0
      flex_bss_neg = flex_bss*0
      flex_bss_pos[flex_bss > 0] = flex_bss[flex_bss > 0]
      flex_bss_neg[flex_bss <= 0] = -flex_bss[flex_bss <= 0]

      print(load.sum().sum() + flex_bss_pos.sum().sum())
      print(Ec_self.sum().sum()+Ec_LV.sum().sum()+Ec_MV.sum().sum()+Ec_LV_flex.sum().sum()+Ec_self_flex.sum().sum())

      #'''
      #for i in [str(i) for i in range(10,20)]:#Ec_LV.columns:#
      for i in ['15']:#Ec_LV.columns:#
        fig, ax = plt.subplots()
        #ax.plot(dE_HH[i], label='dE_HH')
        '''
        ax.plot((Ec_self[i] + Ec_LV[i] + Ec_MV[i] + Ec_LV_flex[i] + Ec_self_flex[i]), label='Ec_self_flex')
        ax.plot((Ec_self[i] + Ec_LV[i] + Ec_MV[i] + Ec_LV_flex[i]), label='Ec_LV_flex')
        ax.plot((Ec_self[i] + Ec_LV[i] + Ec_MV[i]), label='Ec_MW')
        ax.plot((Ec_self[i] + Ec_LV[i]), label='Ec_LV')
        ax.plot((Ec_self[i]), label='Ec_self')
        '''
        #ax.plot((Ec_self[i] + Ec_LV[i] + Ec_MV[i]), label='Ec')        
        ax.plot(flex_bss[i], label='flex_bss')
        ax.plot((Ec_self_flex[i]+Ec_LV_flex[i]), label='Ec_flex')
        #ax.plot((Eg_self[i] + Eg_LV[i] + Eg_MV[i] + Eg_LV_flex[i]), label='Eg')
        #ax.plot((pv[i] - bss[i] + flex_bss_LV[i]), label='pv+bss')
        #ax.plot(Ec_self[i] + Ec_LV[i] + Ec_MV[i])
        #ax.plot(pv[i], label='pv')
        #ax.plot(load[i], label='load')
        #ax.plot(Eg_self[i])
        #ax.plot(Eg_LV[i])
        #ax.plot(Eg_MV[i])
        #ax.plot(Ec_self[i], label='Ec_self')
        #ax.plot(Ec_self_flex[i], label='Ec_self_flex')
        #ax.plot(Ec_LV_flex[i], label='Ec_LV_flex')
        #ax.plot(-Eg_self_flex[i], label='Eg_self_flex')
        #ax.plot(-Eg_self_flex[i] - Eg_LV_flex[i], label='Eg_LV_flex')
        #ax.plot()
        #ax.plot(load[i])
        #ax.plot(pv[i])
        #ax.plot(Eg_self_flex[i])
        #ax.plot(Eg_LV[i])
        #ax.plot(Eg_MV[i])
        #ax.plot(load[i])
        #ax.plot(bss[i])
        #ax.plot(flex_bss[i], label='flex_bss')
        #ax.plot(flex_bss_LV[i], label='flex_bss_LV')
        #ax.plot(load[i])
        #ax.plot((abs(Ec_self) + abs(Ec_MV) + abs(Ec_LV) - (load)))
        #ax.plot((abs(Eg_self) + abs(Eg_MV) + abs(Eg_LV) - (pv - bss)))
      ax.set_xlabel('Time')
      ax.set_ylabel('P in MW')
      ax.legend()
      plt.show()
      #'''

      def print_mmm(df):
        print('Min:  ' + str(df.min().min()))
        print('Max:  ' + str(df.max().max()))
        print('Mean: ' + str(df.mean().mean()))
        print('Error: ' + str(df.sum().sum()/60))

      # Bilanzcheck
      print_mmm((abs(Ec_self) + abs(Ec_MV) + abs(Ec_LV) + abs(Ec_LV_flex) - (load + flex_bss_LV)))#+ abs(Ec_self_flex) + abs(Ec_LV_flex)
      print_mmm((abs(Eg_self) + abs(Eg_MV) + abs(Eg_LV) + abs(Eg_LV_flex) - (pv - bss + flex_bss_LV)))

      print('Generation (incl. BSS) : ' + str(((E.sum(axis=0).Eg_self + E.sum(axis=0).Eg_MV + E.sum(axis=0).Eg_LV + E.sum(axis=0).Eg_LV_flex + E.sum(axis=0).Eg_self_flex - flex_bss_neg.sum().sum())/60).round(3)) + ' MWh') # 60
      print('Consumption (incl. BSS): ' + str(((E.sum(axis=0).Ec_self + E.sum(axis=0).Ec_MV + E.sum(axis=0).Ec_LV + E.sum(axis=0).Ec_LV_flex + E.sum(axis=0).Ec_self_flex - flex_bss_pos.sum().sum())/60).round(3)) + ' MWh') # 60

      sys.exit(0)

    # Seaborn Colors
    bright = sns.color_palette("bright", 10)
    dark = sns.color_palette("dark", 10)
    colors = ['red', dark[3], 'blue', dark[0], 'green', 'yellow']

    #'''
    # Plot PV
    E_barplot1 = E.copy()
    E_barplot1['Eg_self'] += E_barplot1['Eg_self_flex']
    E_barplot1['Eg_LV_flex'] += E_barplot1['Eg_self']
    E_barplot1['Eg_LV'] +=  E_barplot1['Eg_LV_flex']
    E_barplot1['Eg_MV'] +=  E_barplot1['Eg_LV']
    E_barplot1['Ecur_pv'] += E_barplot1['Eg_MV']
    if in_percent == True:
      for i in E_barplot1.index: # plot in percent
        E_barplot1.loc[i] = E_barplot1.loc[i] / E_barplot1['Ecur_pv'].loc[i] * 100
    s4 = sns.barplot(x = E.index, y = 'Ecur_pv', data = E_barplot1, color = 'yellow')
    s3 = sns.barplot(x = E.index, y = 'Eg_MV', data = E_barplot1, color = 'green')
    s2 = sns.barplot(x = E.index, y = 'Eg_LV', data = E_barplot1, color = 'blue')
    s2f = sns.barplot(x = E.index, y = 'Eg_LV_flex', data = E_barplot1, color = dark[0])
    s1 = sns.barplot(x = E.index, y = 'Eg_self', data = E_barplot1, color = 'red')
    s1f = sns.barplot(x = E.index, y = 'Eg_self_flex', data = E_barplot1, color = dark[3])
    Ecur_pv_bar = mpatches.Patch(color='yellow', label='curtailed')
    Eg_MV_bar = mpatches.Patch(color='green', label='MV feed-in')
    Eg_LV_bar = mpatches.Patch(color='blue', label='LV consumed')
    Eg_self_bar = mpatches.Patch(color='red', label='self consumed')
    Eg_self_bar_flex = mpatches.Patch(color=dark[3], label='flex self feed-in')
    Eg_LV_bar_flex = mpatches.Patch(color=dark[0], label='flex LV grid feed-in')
    plt.legend(handles=[Ecur_pv_bar, Eg_MV_bar, Eg_LV_bar, Eg_self_bar, Eg_LV_bar_flex, Eg_self_bar_flex])
    plt.xlabel('Households')
    if in_percent == True:
      plt.ylabel('Generation in %')
    else:
      plt.ylabel('Generation in MWh')
    plt.show()
    #'''
    #'''
    # Plot load
    E_barplot2 = E.copy()
    E_barplot2['Ec_self'] += E_barplot2['Ec_self_flex']
    E_barplot2['Ec_LV_flex'] += E_barplot2['Ec_self']
    E_barplot2['Ec_LV'] +=  E_barplot2['Ec_LV_flex']
    E_barplot2['Ec_MV'] +=  E_barplot2['Ec_LV']
    E_barplot2['Ecur_load'] +=  E_barplot2['Ec_MV']
    if in_percent == True:
      for i in E_barplot2.index: # plot in percent
        E_barplot2.loc[i] = E_barplot2.loc[i] / E_barplot2['Ecur_load'].loc[i] * 100
    s4 = sns.barplot(x = E.index, y = 'Ecur_load', data = E_barplot2, color = 'yellow')
    s3 = sns.barplot(x = E.index, y = 'Ec_MV', data = E_barplot2, color = 'green')
    s2 = sns.barplot(x = E.index, y = 'Ec_LV', data = E_barplot2, color = 'blue')
    s2f = sns.barplot(x = E.index, y = 'Ec_LV_flex', data = E_barplot2, color = dark[0])
    s1 = sns.barplot(x = E.index, y = 'Ec_self', data = E_barplot2, color = 'red')
    s1f = sns.barplot(x = E.index, y = 'Ec_self_flex', data = E_barplot2, color = dark[3])
    Ecur_load_bar = mpatches.Patch(color='yellow', label='curtailed')
    Ec_MV_bar = mpatches.Patch(color='green', label='MV grid obtained')
    Ec_LV_bar = mpatches.Patch(color='blue', label='LV grid obtained')
    Ec_self_bar = mpatches.Patch(color='red', label='self consumed')
    Ec_self_bar_flex = mpatches.Patch(color=dark[3], label='flex self consumed')
    Ec_LV_bar_flex = mpatches.Patch(color=dark[0], label='flex LV grid obtained')
    plt.legend(handles=[Ecur_load_bar, Ec_MV_bar, Ec_LV_bar, Ec_LV_bar_flex, Ec_self_bar, Ec_self_bar_flex])
    plt.xlabel('Households')
    if in_percent == True:
      plt.ylabel('Consumption in %')
    else:
      plt.ylabel('Consumption in MWh')
    plt.show()
    #'''

    print('Generation (4 weeks): ' + str(sum([E['Eg_self'].sum(), E['Eg_LV'].sum(), E['Eg_MV'].sum(), E['Ecur_pv'].sum()])/60) + ' MWh')
    print('Load (4 weeks): ' + str(sum([E['Ec_self'].sum(), E['Ec_LV'].sum(), E['Ec_MV'].sum(), E['Ecur_load'].sum()])/60) + ' MWh')

    #define Seaborn color palette to use
    #colors = sns.color_palette('pastel')[0:5]

    #define data
    data = [(E['Ec_self'].sum() - E['Ec_self_flex'].sum()), E['Ec_self_flex'].sum(), (E['Ec_LV'].sum() - E['Ec_LV_flex'].sum()), E['Ec_LV_flex'].sum(), E['Ec_MV'].sum(), E['Ecur_load'].sum()]
    labels = ['self-consumed', 'self-consumed (flex)', 'P2P', 'P2P (flex)', 'MV-grid obtained', 'curtailed Load']

    #create pie chart
    plt.pie(data, labels = labels, colors = colors, autopct='%.0f%%')
    plt.show()

    #define data
    data = [(E['Eg_self'].sum() - E['Eg_self_flex'].sum()), E['Eg_self_flex'].sum(), (E['Eg_LV'].sum() - E['Eg_LV_flex'].sum()), E['Eg_LV_flex'].sum(), E['Eg_MV'].sum(), E['Ecur_pv'].sum()]
    labels = ['self-consumed', 'self-consumed (flex)', 'P2P', 'P2P (flex)', 'MV-grid feed-in', 'curtailed PV']

    #create pie chart
    plt.pie(data, labels = labels, colors = colors, autopct='%.0f%%')
    plt.show()

    E = E / 60 # MW -> MWh
    E = E * projection_full_year

    E.round(6).to_csv(self.economics_folder + 'energy_share_MWh.csv', header=True, index = True)
    Eg_LV.round(6).to_csv(self.economics_folder + 'Eg_LV_MW.csv', header=True, index = True)
    Ec_LV.round(6).to_csv(self.economics_folder + 'Ec_LV_MW.csv', header=True, index = True)
    Eg_LV_flex.round(6).to_csv(self.economics_folder + 'Eg_LV_flex_MW.csv', header=True, index = True)
    Ec_LV_flex.round(6).to_csv(self.economics_folder + 'Ec_LV_flex_MW.csv', header=True, index = True)

  def energyflow_CommunityBSS(self):
    # plot config
    in_percent = True
    # development env
    test_case = 0

    projection_full_year = 365/(4*7) # 4 weeks and 7 days per week

    index = self.load_p.columns
    index_cut = int((int(self.load_p.columns[-1])+1)/3)
    load_index = index[0:index_cut]
    hp_index = index[index_cut:2*index_cut]
    ev_index = index[2*index_cut:3*index_cut]

    load_index = [str(i) for i in load_index]
    hp_index = [str(i) for i in hp_index]
    ev_index = [str(i) for i in ev_index]

    # HP-load per HH
    hp_load = self.load_p[hp_index]
    hp_load.columns = load_index
    # EV-load per HH
    ev_load = self.load_p[ev_index]
    ev_load.columns = load_index
    # HH-load per HH
    hh_load = self.load_p[load_index]

    load = hh_load + hp_load + ev_load
    # PV per HH
    pv = self.pv_p
    # BSS ECM
    bss = self.storage_p
    # total losses
    losses = self.losses_p.sum(axis=1)

    flex_bss =  self.bss_p_flex.fillna(0)
    flex_load = self.load_p_flex.fillna(0)

    # residual load per HH
    dE_HH = load - pv

    #flex_bss_LV = pd.DataFrame(index=bss.index, columns=bss.columns).fillna(0)
    #flex_bss_LV[(dE_HH >= 0) & (flex_bss > 0) & (pv > load)] = dE_HH[(dE_HH >= 0) & (flex_bss > 0) & (pv > load)]
    #flex_bss_LV[(dE_HH >= 0) & (flex_bss > 0) & (pv <= load)] = flex_bss[(dE_HH >= 0) & (flex_bss > 0) & (pv <= load)]

    # residual load whole grid
    dE_LV = pd.DataFrame(index=dE_HH.index, columns=dE_HH.columns)
    for c in dE_LV.columns:
      dE_LV[c] = dE_HH.sum(axis=1) + bss.sum(axis=1)# + losses

    # Sum of all PV excess
    sum_PV_LV_excess = pd.DataFrame(index=dE_HH.index, columns=dE_HH.columns).fillna(0)
    sum_Con_LV_lack = pd.DataFrame(index=dE_HH.index, columns=dE_HH.columns).fillna(0)
    for c in dE_LV.columns:
      sum_PV_LV_excess[c] = dE_HH[dE_HH < 0].sum(axis=1) # PV Überschuss gesamtes Netz
      sum_Con_LV_lack[c] = dE_HH[dE_HH >= 0].sum(axis=1) # Lastüberschuss gesamtes Netz

    # create
    Ec_MV = pd.DataFrame(index=pv.index, columns=pv.columns).fillna(0)
    Ec_LV = pd.DataFrame(index=pv.index, columns=pv.columns).fillna(0)
    Ec_self = pd.DataFrame(index=pv.index, columns=pv.columns).fillna(0)
    Eg_self = pd.DataFrame(index=pv.index, columns=pv.columns).fillna(0)
    Eg_LV = pd.DataFrame(index=pv.index, columns=pv.columns).fillna(0)
    Eg_MV = pd.DataFrame(index=pv.index, columns=pv.columns).fillna(0)
    Ecur_load = self.curtailed_power_load
    Ecur_pv = self.curtailed_power_pv

    ### Calculate how much of the pos and neg flexibility is included in self-sonsumption and locally traded energy
    Ec_self_flex = pd.DataFrame(index=dE_HH.index, columns=dE_HH.columns).fillna(0)
    Ec_LV_flex   = pd.DataFrame(index=dE_HH.index, columns=dE_HH.columns).fillna(0)
    Eg_self_flex = pd.DataFrame(index=dE_HH.index, columns=dE_HH.columns).fillna(0)
    Eg_LV_flex   = pd.DataFrame(index=dE_HH.index, columns=dE_HH.columns).fillna(0)

    # if PV+BSS gen greater than con -> calculate self consumption
    Ec_self[dE_HH < 0] = load[dE_HH < 0]
    Eg_self[dE_HH < 0] = load[dE_HH < 0]
    Ec_MV[dE_HH < 0] = 0
    Ec_LV[dE_HH < 0] = 0
    Eg_MV[(dE_HH < 0) & (dE_LV >= 0)] = 0
    Eg_LV[(dE_HH < 0) & (dE_LV >= 0)] = -dE_HH[(dE_HH < 0) & (dE_LV >= 0)]
    Eg_MV[(dE_HH < 0) & (dE_LV < 0)] = -dE_HH[(dE_HH < 0) & (dE_LV < 0)] / sum_PV_LV_excess[(dE_HH < 0) & (dE_LV < 0)] * dE_LV[(dE_HH < 0) & (dE_LV < 0)]
    Eg_LV[(dE_HH < 0) & (dE_LV < 0)] = -dE_HH[(dE_HH < 0) & (dE_LV < 0)] / sum_PV_LV_excess[(dE_HH < 0) & (dE_LV < 0)] * (sum_PV_LV_excess[(dE_HH < 0) & (dE_LV < 0)] - dE_LV[(dE_HH < 0) & (dE_LV < 0)])

    # if PV+BSS gen lower than con -> calculate self consumption
    Ec_self[dE_HH >= 0] = pv[dE_HH >= 0]# - bss[dE_HH >= 0] + flex_bss_LV[dE_HH >= 0]
    Eg_self[dE_HH >= 0] = pv[dE_HH >= 0]# - bss[dE_HH >= 0] + flex_bss_LV[dE_HH >= 0]
    Ec_MV[(dE_HH >= 0) & (dE_LV >= 0)] = dE_HH[(dE_HH >= 0) & (dE_LV >= 0)] / sum_Con_LV_lack[(dE_HH >= 0) & (dE_LV >= 0)] * dE_LV[(dE_HH >= 0) & (dE_LV >= 0)]
    Ec_LV[(dE_HH >= 0) & (dE_LV >= 0)] = dE_HH[(dE_HH >= 0) & (dE_LV >= 0)] / sum_Con_LV_lack[(dE_HH >= 0) & (dE_LV >= 0)] * (sum_Con_LV_lack[(dE_HH >= 0) & (dE_LV >= 0)] - dE_LV[(dE_HH >= 0) & (dE_LV >= 0)])
    Ec_MV[(dE_HH >= 0) & (dE_LV < 0)] = 0
    Ec_LV[(dE_HH >= 0) & (dE_LV < 0)] = dE_HH[(dE_HH >= 0) & (dE_LV < 0)]
    Eg_MV[dE_HH >= 0] = 0
    Eg_LV[dE_HH >= 0] = 0

    Ec_self[Ec_self < 0] = 0
    Eg_self[Eg_self < 0] = 0

    # Load Flexibility
    flex_load_pos = flex_load.copy() * 0
    flex_load_neg = flex_load.copy() * 0
    flex_load_pos[flex_load > 0] = flex_load[flex_load > 0] # Last wird vergrößert
    flex_load_neg[flex_load < 0] = flex_load[flex_load < 0] # Last wird verringert = Generation wird vergrößert

    Ec_LV_flex[  (pv < load) & (flex_load > 0) & (flex_load_pos > (load - pv))] += load - pv
    Ec_self_flex[(pv < load) & (flex_load > 0) & (flex_load_pos > (load - pv))] += flex_load_pos - (load - pv)

    Ec_LV_flex[  (pv < load) & (flex_load > 0) & (flex_load_pos < (load - pv))] += flex_load_pos
    Ec_self_flex[(pv < load) & (flex_load > 0) & (flex_load_pos < (load - pv))] += 0

    Ec_LV_flex[  (pv > load) & (flex_load > 0)] += 0
    Ec_self_flex[(pv > load) & (flex_load > 0)] += flex_load_pos


    Eg_LV_flex[  (flex_load < 0) & (pv < load)] += -flex_load_neg
    Eg_self_flex[(flex_load < 0) & (pv < load)] += 0

    Eg_LV_flex[  (flex_load < 0) & (pv > load)] += load-pv
    Eg_self_flex[(flex_load < 0) & (pv > load)] += -flex_load_neg - (load-pv)

    #Ec_self -= Ec_self_flex
    #Eg_self -= Eg_self_flex

    '''
    # BSS Flexibility
    Ec_LV_flex[(dE_HH >= 0) & (flex_bss > 0) & (pv > load) & (flex_bss <= dE_HH)] += flex_bss[(dE_HH >= 0) & (flex_bss > 0) & (pv > load) & (flex_bss <= dE_HH)]
    Ec_LV_flex[(dE_HH >= 0) & (flex_bss > 0) & (pv > load) & (flex_bss > dE_HH)] += dE_HH[(dE_HH >= 0) & (flex_bss > 0) & (pv > load) & (flex_bss > dE_HH)]

    Ec_LV_flex[(dE_HH >= 0) & (flex_bss > 0) & (pv <= load)] += flex_bss[(dE_HH >= 0) & (flex_bss > 0) & (pv <= load)]

    Eg_LV_flex[(dE_HH < 0) & (flex_bss < 0) & (pv <= load) & (flex_bss <= dE_HH)] += -flex_bss[(dE_HH < 0) & (flex_bss < 0) & (pv <= load) & (flex_bss <= dE_HH)]
    Eg_LV_flex[(dE_HH < 0) & (flex_bss < 0) & (pv <= load) & (flex_bss > dE_HH)] += -dE_HH[(dE_HH < 0) & (flex_bss < 0) & (pv <= load) & (flex_bss > dE_HH)]

    Eg_LV_flex[(dE_HH < 0) & (flex_bss < 0) & (pv > load)] += -flex_bss[(dE_HH < 0) & (flex_bss < 0) & (pv > load)]

    Ec_self_flex[(flex_bss > 0)] += flex_bss[(flex_bss > 0)] - Ec_LV_flex[(flex_bss > 0)]
    Eg_self_flex[(flex_bss < 0)] += -flex_bss[(flex_bss < 0)] - Eg_LV_flex[(flex_bss < 0)]

    Eg_LV_flex[Eg_LV_flex < 0] = 0
    '''

    Ec_LV -= Ec_LV_flex
    Eg_LV -= Eg_LV_flex

    E = pd.DataFrame(index=Ec_self.columns)

    E['Ec_self'] = Ec_self.sum()
    E['Eg_self'] = Eg_self.sum()
    E['Ec_MV'] = Ec_MV.sum()
    E['Ec_LV'] = Ec_LV.sum()
    E['Eg_MV'] = Eg_MV.sum()
    E['Eg_LV'] = Eg_LV.sum()
    E['Ecur_pv'] = Ecur_pv.sum()
    E['Ecur_load'] = Ecur_load.sum()
    E['Ec_LV_flex'] = Ec_LV_flex.sum()
    E['Eg_LV_flex'] = Eg_LV_flex.sum()
    E['Ec_self_flex'] = Ec_self_flex.sum()
    E['Eg_self_flex'] = Eg_self_flex.sum()

    bss_neg = bss.copy()
    bss_pos = bss.copy()
    bss_neg[bss>0] = 0
    bss_neg = -bss_neg
    bss_pos[bss<0] = 0

    if test_case == True:

      print(bss_pos.sum())
      print(bss_neg.sum())
      print(Ec_LV.sum().sum())
      print(Eg_LV.sum().sum())

      #'''
      #for i in [str(i) for i in range(10,20)]:#Ec_LV.columns:#
      #for i in Ec_LV.columns:#
      fig, ax = plt.subplots()
      ax.plot(bss_pos)
      ax.plot(bss_neg)
      ax.plot(Ec_LV.sum(axis=1))
      ax.plot(-Eg_LV.sum(axis=1))
        #ax.plot(dE_HH[i], label='dE_HH')
        #'''
        #ax.plot((Ec_self[i] + Ec_LV[i] + Ec_MV[i] + Ec_LV_flex[i] + Ec_self_flex[i]), label='Ec_self_flex')
        #ax.plot((Ec_self[i] + Ec_LV[i] + Ec_MV[i] + Ec_LV_flex[i]), label='Ec_LV_flex')
        #ax.plot((Ec_self[i] + Ec_LV[i] + Ec_MV[i]), label='Ec_MW')
        #ax.plot((Ec_self[i] + Ec_LV[i]), label='Ec_LV')
        #ax.plot((Ec_self[i]), label='Ec_self')
        #'''
        #ax.plot((Ec_self[i] + Ec_LV[i] + Ec_MV[i]), label='Ec')        
        #ax.plot(flex_bss[i], label='flex_bss')
        #ax.plot((Ec_self_flex[i]+Ec_LV_flex[i]), label='Ec_flex')
        #ax.plot((Eg_self[i] + Eg_LV[i] + Eg_MV[i] + Eg_LV_flex[i]), label='Eg')
        #ax.plot((pv[i] - bss[i] + flex_bss_LV[i]), label='pv+bss')
        #ax.plot(Ec_self[i] + Ec_LV[i] + Ec_MV[i])
        #ax.plot(pv[i], label='pv')
        #ax.plot(load[i], label='load')
        #ax.plot(Eg_self[i])
        #ax.plot(Eg_LV[i])
        #ax.plot(Eg_MV[i])
        #ax.plot(Ec_self[i], label='Ec_self')
        #ax.plot(Ec_self_flex[i], label='Ec_self_flex')
        #ax.plot(Ec_LV_flex[i], label='Ec_LV_flex')
        #ax.plot(-Eg_self_flex[i], label='Eg_self_flex')
        #ax.plot(-Eg_self_flex[i] - Eg_LV_flex[i], label='Eg_LV_flex')
        #ax.plot()
        #ax.plot(load[i])
        #ax.plot(pv[i])
        #ax.plot(Eg_self_flex[i])
        #ax.plot(Eg_LV[i])
        #ax.plot(Eg_MV[i])
        #ax.plot(load[i])
        #ax.plot(bss[i])
        #ax.plot(flex_bss[i], label='flex_bss')
        #ax.plot(flex_bss_LV[i], label='flex_bss_LV')
        #ax.plot(load[i])
        #ax.plot((abs(Ec_self) + abs(Ec_MV) + abs(Ec_LV) - (load)))
        #ax.plot((abs(Eg_self) + abs(Eg_MV) + abs(Eg_LV) - (pv - bss)))
      ax.set_xlabel('Time')
      ax.set_ylabel('P in MW')
      ax.legend(['bss_pos','bss_neg','Ec','Eg'])
      plt.show()
      #'''

      def print_mmm(df):
        print('Min:  ' + str(df.min().min()))
        print('Max:  ' + str(df.max().max()))
        print('Mean: ' + str(df.mean().mean()))
        print('Error: ' + str(df.sum().sum()/60))

      # Bilanzcheck
      #print_mmm((abs(Ec_self) + abs(Ec_MV) + abs(Ec_LV) + abs(Ec_LV_flex) - (load)))#+ abs(Ec_self_flex) + abs(Ec_LV_flex)
      #print_mmm((abs(Eg_self) + abs(Eg_MV) + abs(Eg_LV) + abs(Eg_LV_flex) - (pv - bss)))

      #print('Generation (incl. BSS) : ' + str(((E.sum(axis=0).Eg_self + E.sum(axis=0).Eg_MV + E.sum(axis=0).Eg_LV + E.sum(axis=0).Eg_LV_flex + E.sum(axis=0).Eg_self_flex - flex_bss_neg.sum().sum())/60).round(3)) + ' MWh') # 60
      #print('Consumption (incl. BSS): ' + str(((E.sum(axis=0).Ec_self + E.sum(axis=0).Ec_MV + E.sum(axis=0).Ec_LV + E.sum(axis=0).Ec_LV_flex + E.sum(axis=0).Ec_self_flex - flex_bss_pos.sum().sum())/60).round(3)) + ' MWh') # 60

      sys.exit(0)

    # Seaborn Colors
    bright = sns.color_palette("bright", 10)
    dark = sns.color_palette("dark", 10)
    colors = ['red', dark[3], 'blue', dark[0], 'green', 'yellow']

    #'''
    # Plot PV
    E_barplot1 = E.copy()
    E_barplot1['Eg_self'] += E_barplot1['Eg_self_flex']
    E_barplot1['Eg_LV_flex'] += E_barplot1['Eg_self']
    E_barplot1['Eg_LV'] +=  E_barplot1['Eg_LV_flex']
    E_barplot1['Eg_MV'] +=  E_barplot1['Eg_LV']
    E_barplot1['Ecur_pv'] += E_barplot1['Eg_MV']
    if in_percent == True:
      for i in E_barplot1.index: # plot in percent
        E_barplot1.loc[i] = E_barplot1.loc[i] / E_barplot1['Ecur_pv'].loc[i] * 100
    s4 = sns.barplot(x = E.index, y = 'Ecur_pv', data = E_barplot1, color = 'yellow')
    s3 = sns.barplot(x = E.index, y = 'Eg_MV', data = E_barplot1, color = 'green')
    s2 = sns.barplot(x = E.index, y = 'Eg_LV', data = E_barplot1, color = 'blue')
    s2f = sns.barplot(x = E.index, y = 'Eg_LV_flex', data = E_barplot1, color = dark[0])
    s1 = sns.barplot(x = E.index, y = 'Eg_self', data = E_barplot1, color = 'red')
    s1f = sns.barplot(x = E.index, y = 'Eg_self_flex', data = E_barplot1, color = dark[3])
    Ecur_pv_bar = mpatches.Patch(color='yellow', label='curtailed')
    Eg_MV_bar = mpatches.Patch(color='green', label='MV feed-in')
    Eg_LV_bar = mpatches.Patch(color='blue', label='LV consumed')
    Eg_self_bar = mpatches.Patch(color='red', label='self consumed')
    Eg_self_bar_flex = mpatches.Patch(color=dark[3], label='flex self feed-in')
    Eg_LV_bar_flex = mpatches.Patch(color=dark[0], label='flex LV grid feed-in')
    plt.legend(handles=[Ecur_pv_bar, Eg_MV_bar, Eg_LV_bar, Eg_self_bar, Eg_LV_bar_flex, Eg_self_bar_flex])
    plt.xlabel('Households')
    if in_percent == True:
      plt.ylabel('Generation in %')
    else:
      plt.ylabel('Generation in MWh')
    plt.show()
    #'''
    #'''
    # Plot load
    E_barplot2 = E.copy()
    E_barplot2['Ec_self'] += E_barplot2['Ec_self_flex']
    E_barplot2['Ec_LV_flex'] += E_barplot2['Ec_self']
    E_barplot2['Ec_LV'] +=  E_barplot2['Ec_LV_flex']
    E_barplot2['Ec_MV'] +=  E_barplot2['Ec_LV']
    E_barplot2['Ecur_load'] +=  E_barplot2['Ec_MV']
    if in_percent == True:
      for i in E_barplot2.index: # plot in percent
        E_barplot2.loc[i] = E_barplot2.loc[i] / E_barplot2['Ecur_load'].loc[i] * 100
    s4 = sns.barplot(x = E.index, y = 'Ecur_load', data = E_barplot2, color = 'yellow')
    s3 = sns.barplot(x = E.index, y = 'Ec_MV', data = E_barplot2, color = 'green')
    s2 = sns.barplot(x = E.index, y = 'Ec_LV', data = E_barplot2, color = 'blue')
    s2f = sns.barplot(x = E.index, y = 'Ec_LV_flex', data = E_barplot2, color = dark[0])
    s1 = sns.barplot(x = E.index, y = 'Ec_self', data = E_barplot2, color = 'red')
    s1f = sns.barplot(x = E.index, y = 'Ec_self_flex', data = E_barplot2, color = dark[3])
    Ecur_load_bar = mpatches.Patch(color='yellow', label='curtailed')
    Ec_MV_bar = mpatches.Patch(color='green', label='MV grid obtained')
    Ec_LV_bar = mpatches.Patch(color='blue', label='LV grid obtained')
    Ec_self_bar = mpatches.Patch(color='red', label='self consumed')
    Ec_self_bar_flex = mpatches.Patch(color=dark[3], label='flex self consumed')
    Ec_LV_bar_flex = mpatches.Patch(color=dark[0], label='flex LV grid obtained')
    plt.legend(handles=[Ecur_load_bar, Ec_MV_bar, Ec_LV_bar, Ec_LV_bar_flex, Ec_self_bar, Ec_self_bar_flex])
    plt.xlabel('Households')
    if in_percent == True:
      plt.ylabel('Consumption in %')
    else:
      plt.ylabel('Consumption in MWh')
    plt.show()
    #'''

    print('Generation (4 weeks): ' + str(sum([E['Eg_self'].sum(), E['Eg_LV'].sum(), E['Eg_MV'].sum(), E['Ecur_pv'].sum()])/60) + ' MWh')
    print('Load (4 weeks): ' + str(sum([E['Ec_self'].sum(), E['Ec_LV'].sum(), E['Ec_MV'].sum(), E['Ecur_load'].sum()])/60) + ' MWh')

    #define Seaborn color palette to use
    #colors = sns.color_palette('pastel')[0:5]

    #define data
    data = [(E['Ec_self'].sum() - E['Ec_self_flex'].sum()), E['Ec_self_flex'].sum(), (E['Ec_LV'].sum() - E['Ec_LV_flex'].sum()), E['Ec_LV_flex'].sum(), E['Ec_MV'].sum(), E['Ecur_load'].sum()]
    labels = ['self-consumed', 'self-consumed (flex)', 'P2P', 'P2P (flex)', 'MV-grid obtained', 'curtailed Load']

    #create pie chart
    plt.pie(data, labels = labels, colors = colors, autopct='%.0f%%')
    plt.show()

    #define data
    data = [(E['Eg_self'].sum() - E['Eg_self_flex'].sum()), E['Eg_self_flex'].sum(), (E['Eg_LV'].sum() - E['Eg_LV_flex'].sum()), E['Eg_LV_flex'].sum(), E['Eg_MV'].sum(), E['Ecur_pv'].sum()]
    labels = ['self-consumed', 'self-consumed (flex)', 'P2P', 'P2P (flex)', 'MV-grid feed-in', 'curtailed PV']

    #create pie chart
    plt.pie(data, labels = labels, colors = colors, autopct='%.0f%%')
    plt.show()

    E = E / 60 # MW -> MWh
    E = E * projection_full_year

    E.round(6).to_csv(self.economics_folder + 'energy_share_MWh.csv', header=True, index = True)
    Eg_LV.round(6).to_csv(self.economics_folder + 'Eg_LV_MW.csv', header=True, index = True)
    Ec_LV.round(6).to_csv(self.economics_folder + 'Ec_LV_MW.csv', header=True, index = True)
    Eg_LV_flex.round(6).to_csv(self.economics_folder + 'Eg_LV_flex_MW.csv', header=True, index = True)
    Ec_LV_flex.round(6).to_csv(self.economics_folder + 'Ec_LV_flex_MW.csv', header=True, index = True)
    bss_neg.round(6).to_csv(self.economics_folder + 'Eg_LV_ECM_MW.csv', header=True, index = True)
    bss_pos.round(6).to_csv(self.economics_folder + 'Ec_LV_ECM_MW.csv', header=True, index = True)


  ### calculate and print relevant parameters ###
  def calculate_relevant_outputdata(self):

    power = self.power
    losses = self.losses_p
    trafo_p = self.trafo_p
    curtail_pv = self.curtailed_power_pv.sum(axis=1)
    curtail_load = self.curtailed_power_load.sum(axis=1)
    curtail_p = pd.DataFrame()
    curtail_p['curtail_pv'] = curtail_pv
    curtail_p['curtail_load'] = curtail_load

    if self.time_scope[0]['t_freq'] != None:#'1D':
      power = self.shorted_data(power, '1H')
      losses = self.shorted_data(losses, '1H')
      trafo_p = self.shorted_data(trafo_p, '1H')
      curtail_p = self.shorted_data(curtail_p, '1H')
      f = 1
    else:
      f = 24

    sum_curtailed_pv = curtail_p.curtail_pv.sum()*f
    sum_curtailed_load = curtail_p.curtail_load.sum()*f
    losses = losses.sum().sum()
    sum_pv = power.pv.sum()*f
    sum_total_pv = power.pv.sum()*f + curtail_p.curtail_pv.sum()*f
    sum_hp = power.hp.sum()*f
    sum_ev = power.ev.sum()*f
    sum_load = power.load.sum()*f
    sum_total_load = sum_hp + sum_load + sum_ev

    Res = -1*trafo_p.values
    
    Res_pos = Res[Res > 0]
    Res_neg = Res[Res < 0]

    SelfSufficiancy = (sum_total_load + losses + Res_neg.sum())*100/(sum_total_load + losses)
    if sum_total_pv > 0:
      PVConsumption = (sum_total_pv - Res_pos.sum() - curtail_p.curtail_pv.sum()*f)*100/sum_total_pv
    else:
      PVConsumption = sum_total_pv*0.0
      
    print(' ')
    print('PV-Generation: %s MWh' % sum_pv.round(2))
    print('HP-Consumption: %s MWh' % sum_hp.round(2))
    print('EV-Consumption: %s MWh' % sum_ev.round(2))
    print('Load-Consumption: %s MWh' % sum_load.round(2))
    print('Total Consumption: %s MWh' % sum_total_load.round(2))
    print(' ')
    print('Total Losses (lines+trafo): %s MWh' % losses.round(2))
    print('Curtailed PV Energy: %s MWh' % sum_curtailed_pv.round(2))
    print('Curtailed Load Energy: %s MWh' % sum_curtailed_load.round(2))
    print(' ')
    print('Generation/Consumption ratio: %s %%' % ((sum_pv/sum_total_load*100).round(1)))
    print('Self-sufficiancy: %s %%' % ((SelfSufficiancy).round(2)))
    print('PV consumption rate: %s %%' % ((PVConsumption).round(2)))
    print(' ')

  #################################
  ### 01 annuity of investmentcosts
  #################################
  def determine_annuity_investments(self, include_grid_reinforce = True):
    investment_costs = parameter_economics.investment_costs

    #print(self.component_parameter)
    #print(investment_costs)

    def calculate_anf(i, n):
      anf = (i * (1 + i)**n) / ((1 + i)**n - 1)
      return anf

    E_invest_HH = pd.DataFrame(index=self.component_parameter.index)
    E_invest_ECM = pd.DataFrame(index=[0])

    ### HH ###
    # BSS #
    anf_bss_HH = calculate_anf(investment_costs['intrest_rate'], investment_costs['battery_lifespan'])
    E_invest_HH['BSS_capex'] = self.component_parameter['BSS_energy']*1000 * investment_costs['battery'] * anf_bss_HH if self.scenario[2] in [0, 1, 2, 3] else 0.

    # TES #
    anf_tes = calculate_anf(investment_costs['intrest_rate'], investment_costs['tes_lifespan'])
    E_invest_HH['TES_capex'] = self.component_parameter['TES_energy']*1000 * investment_costs['tes'] * anf_tes

    # smart consumers #
    anf_sgr = calculate_anf(investment_costs['intrest_rate'], investment_costs['smart_grid_lifespan'])
    E_invest_HH['SG_capex'] = investment_costs['smart_grid'] * anf_sgr if self.scenario[0] in [7, 8] else 0.

    ### ECM ###
    # BSS #
    anf_bss_ECM = calculate_anf(investment_costs['intrest_rate'], investment_costs['battery_lifespan'])
    E_invest_ECM['BSS_capex'] = self.component_parameter['BSS_energy'].sum()*1000 * investment_costs['battery'] * anf_bss_ECM if self.scenario[2] in [4, 5] else 0.

    # Grid #
    anf_grid_ECM = calculate_anf(investment_costs['intrest_rate'], investment_costs['grid_lifespan'])
    costs_trafo, costs_lines = self.get_grid_reinforcment_costs(include_grid_reinforce)
    E_invest_ECM['Grid_Lines_capex'] = costs_lines * anf_grid_ECM
    E_invest_ECM['Grid_Trafo_capex'] = costs_trafo * anf_grid_ECM

    E_invest_HH.round(2).to_csv(self.economics_folder + '01_invest_per_HH_in_Euro.csv', header=True, index = True)
    E_invest_ECM.round(2).to_csv(self.economics_folder + '01_invest_ECM_in_Euro.csv', header=True, index = True)


  def get_grid_reinforcment_costs(self, include_grid_reinforce):
    file_line_costs = 'reinforced_lines.csv'
    file_trafo_costs = 'reinforced_trafo.csv'
    if include_grid_reinforce == False:
      return 0., 0.
    elif include_grid_reinforce == True:
      if os.path.exists(self.output_dir_components_grid_reinforce + file_line_costs) and os.path.exists(self.output_dir_components_grid_reinforce + file_trafo_costs):
        line_costs = pd.read_csv(self.output_dir_components_grid_reinforce + file_line_costs, delimiter = ',', low_memory=False).drop('Unnamed: 0', axis=1)
        trafo_costs = pd.read_csv(self.output_dir_components_grid_reinforce + file_trafo_costs, delimiter = ',', low_memory=False).drop('Unnamed: 0', axis=1)
        return line_costs['total_costs'].sum(), trafo_costs['costs'].sum()
      else:
        #print('Warning: include_grid_reinforce is set to True. But files reinforced_lines.csv and reinforced_trafo.csv could not be found. Grid cost = 0 is returned.')
        return 0., 0.
    else:
      raise ValueError('Not sure wheater include grid reinforcment costs or not. Please set include_grid_reinforce True or False.')    

  #####################################
  ### 02 determine operational expanses
  #####################################
  def determine_operational_expanses(self):
    E_invest_HH = pd.read_csv(self.economics_folder + '01_invest_per_HH_in_Euro.csv', delimiter = ',', low_memory=False).drop('Unnamed: 0', axis=1)
    E_invest_ECM = pd.read_csv(self.economics_folder + '01_invest_ECM_in_Euro.csv', delimiter = ',', low_memory=False).drop('Unnamed: 0', axis=1)

    E_opex_HH = pd.DataFrame(index=self.component_parameter.index)
    E_opex_ECM = pd.DataFrame(index=[0])

    percent = parameter_economics.operating_costs['percent']

    ### HH ###
    # BSS #
    E_opex_HH['BSS_opex'] = E_invest_HH['BSS_capex'] * percent

    # smart consumers #
    E_opex_HH['TES_opex'] = E_invest_HH['TES_capex'] * percent

    # smart consumers #
    E_opex_HH['SG_opex'] = E_invest_HH['SG_capex'] * percent

    ### ECM ###
    # BSS #
    E_opex_ECM['BSS_opex'] = E_invest_ECM['BSS_capex'] * percent

    # Grid #
    E_opex_ECM['Grid_Lines_opex'] = E_invest_ECM['Grid_Lines_capex'] * percent
    E_opex_ECM['Grid_Trafo_opex'] = E_invest_ECM['Grid_Trafo_capex'] * percent

    E_opex_HH.round(2).to_csv(self.economics_folder + '02_opex_per_HH_in_Euro.csv', header=True, index = True)
    E_opex_ECM.round(2).to_csv(self.economics_folder + '02_opex_EMC_in_Euro.csv', header=True, index = True)


  ########################################
  ### 03 costs and revenues of energyflows
  ########################################
  def determine_local_energy_trading_price(self):
    # Calculate supply-demand-ratio according to Dyn22

    index = self.load_p.columns
    index_cut = int((int(self.load_p.columns[-1])+1)/3)
    load_index = index[0:index_cut]
    hp_index = index[index_cut:2*index_cut]
    ev_index = index[2*index_cut:3*index_cut]

    load_index = [str(i) for i in load_index]
    hp_index = [str(i) for i in hp_index]
    ev_index = [str(i) for i in ev_index]

    # HP-load per HH
    hp_load = self.load_p[hp_index]
    hp_load.columns = load_index
    # EV-load per HH
    ev_load = self.load_p[ev_index]
    ev_load.columns = load_index
    # HH-load per HH
    hh_load = self.load_p[load_index]

    bss = self.storage_p
    bss_neg = bss.copy()
    bss_pos = bss.copy()
    bss_neg[bss_neg > 0] = 0
    bss_pos[bss_pos < 0] = 0

    l = hh_load + hp_load + ev_load + bss_pos
    g = self.pv_p - bss_neg

    s = g - l
    s[s<0] = 0
    d = l - g
    d[d<0] = 0

    s_total = s.sum(axis=1)
    d_total = d.sum(axis=1)

    r = s_total / d_total
    r[r>1.] = 1.

    p_fit = parameter_economics.energycosts_income['C_market_fit']
    p_u = parameter_economics.energycosts_income['C_market_obtain']

    p_t = r*0
    p_t[r<1.] = r[r<1.]*p_fit + (1 - r[r<1.])*p_u
    p_t[r>=1.] = p_fit

    '''
    fig, ax = plt.subplots()
    ax.plot(bss)
    ax.set_xlabel('Time')
    ax.set_ylabel('P in MW')
    ax.legend()
    plt.show()
    '''
    p_t.round(3).to_csv(self.economics_folder + 'trading_price_LV_euro_per_MWh.csv', header=True, index = True)

  def determine_grid_charges(self):
    investment_costs = parameter_economics.investment_costs

    def calculate_anf(i, n):
      anf = (i * (1 + i)**n) / ((1 + i)**n - 1)
      return anf

    trafo_costs, line_costs = self.get_grid_reinforcment_costs(include_grid_reinforce = True)
    anf_grid = calculate_anf(investment_costs['intrest_rate'], investment_costs['grid_lifespan'])
    trafo_costs *= anf_grid
    line_costs  *= anf_grid

    E = pd.read_csv(self.economics_folder + 'energy_share_MWh.csv', delimiter = ',', low_memory=False).drop('Unnamed: 0', axis=1)
    grid_charges = pd.DataFrame()

    # grid charges based on load
    Ecur_load = E['Ecur_load'].sum()
    Ec_MV = E['Ec_MV'].sum()
    Ec_LV = E['Ec_LV'].sum()

    a_load = (Ecur_load + Ec_MV)/(Ec_LV + Ecur_load + Ec_MV)

    grid_charge_MV_load = (a_load*line_costs + trafo_costs)/(Ecur_load + Ec_MV)
    grid_charge_LV_load = ((1-a_load)*line_costs + trafo_costs)/(Ec_LV)

    #print("grid charges load LV: " + str(grid_charge_MV_load))
    #print("grid charges load MV: " + str(grid_charge_LV_load))

    # grid charges based on pv
    Ecur_pv = E['Ecur_pv'].sum()
    Eg_MV = E['Eg_MV'].sum()
    Eg_LV = E['Eg_LV'].sum()

    a_pv = (Ecur_pv + Eg_MV)/(Eg_LV + Ecur_pv + Eg_MV)

    grid_charge_MV_pv = (a_pv*line_costs + trafo_costs)/(Ecur_pv + Eg_MV)
    grid_charge_LV_pv = ((1-a_pv)*line_costs + trafo_costs)/(Eg_LV)

    #print("grid charges pv LV: " + str(grid_charge_MV_pv))
    #print("grid charges pv MV: " + str(grid_charge_LV_pv))

    grid_charges['grid_charge_MV_load'] = grid_charge_MV_load
    grid_charges['grid_charge_LV_load'] = grid_charge_LV_load
    grid_charges['grid_charge_MV_pv'] = grid_charge_MV_pv
    grid_charges['grid_charge_LV_pv'] = grid_charge_LV_pv

    grid_charges.round(3).to_csv(self.economics_folder + 'grid_charges_euro_per_MWh.csv', header=True, index = True)

  def determine_energy_costs_revenues(self):
    E = pd.read_csv(self.economics_folder + 'energy_share_MWh.csv', delimiter = ',', low_memory=False)

    # EnergyCell management costs and revenues
    EC_costs = {
      'flex_LV' : 0,
      'flex_self' : 0,
      'curtailed_load' : 0,
      'curtailed_pv' : 0,
      'bss_LV' : 0,
    }
    EC_reven = {
      'grid_charges' : 0,
      'bss_LV' : 0,
    }

    # LV traded energy, LV flex, costs and revenues
    p_t = self.read_data(self.economics_folder + 'trading_price_LV_euro_per_MWh.csv')
    Eg_LV = self.read_data(self.economics_folder + 'Eg_LV_MW.csv') / 60
    Ec_LV = self.read_data(self.economics_folder + 'Ec_LV_MW.csv') / 60
    Eg_LV_flex = self.read_data(self.economics_folder + 'Eg_LV_flex_MW.csv') / 60
    Ec_LV_flex = self.read_data(self.economics_folder + 'Ec_LV_flex_MW.csv') / 60
    df_HH = pd.DataFrame(columns=Ec_LV_flex.columns)

    if os.path.exists(self.economics_folder + 'Eg_LV_ECM_MW.csv') and os.path.exists(self.economics_folder + 'Ec_LV_ECM_MW.csv'):
      Eg_LV_ECM = self.read_data(self.economics_folder + 'Eg_LV_ECM_MW.csv') / 60
      Ec_LV_ECM = self.read_data(self.economics_folder + 'Ec_LV_ECM_MW.csv') / 60
    else:
      Eg_LV_ECM = 0
      Ec_LV_ECM = 0

    p_flex_LV = parameter_economics.energycosts_income['C_flex_LV']

    Ec_LV_costs = Ec_LV.copy()*0
    Eg_LV_reven = Eg_LV.copy()*0
    Ec_LV_flex_reven = Ec_LV_flex.copy()*0
    Eg_LV_flex_reven = Eg_LV_flex.copy()*0

    for c in Ec_LV.columns:
      Ec_LV_costs[c] = Ec_LV[c] * p_t['0']
      Eg_LV_reven[c] = Eg_LV[c] * p_t['0']
      Ec_LV_flex_reven[c] = Ec_LV_flex[c] * p_flex_LV
      Eg_LV_flex_reven[c] = Eg_LV_flex[c] * (p_t['0'] + p_flex_LV)
      EC_costs['flex_LV'] += (Ec_LV_flex[c] * p_flex_LV).sum()
      EC_costs['flex_LV'] += (Eg_LV_flex[c] * (p_t['0'] + p_flex_LV)).sum()

    # Self consumed flex energy
    Ec_self_flex_reven = df_HH.copy()
    Eg_self_flex_reven = df_HH.copy()
    p_flex_self = parameter_economics.energycosts_income['C_flex_self']

    Ec_self_flex_reven = E['Ec_self_flex'] * p_flex_self
    Eg_self_flex_reven = E['Eg_self_flex'] * p_flex_self
    EC_costs['flex_self'] += (E['Ec_self_flex'] * p_flex_self).sum()
    EC_costs['flex_self'] += (E['Eg_self_flex'] * p_flex_self).sum()

    # Curtailed Energy
    Ec_cur_load_reven = df_HH.copy()
    Eg_cur_pv_reven   = df_HH.copy()
    p_cur_load = parameter_economics.energycosts_income['C_cur_load']
    p_cur_pv = parameter_economics.energycosts_income['C_cur_pv']

    Ec_cur_load_reven = E['Ecur_load'] * p_cur_load
    Eg_cur_pv_reven   = E['Ecur_pv'] * p_cur_pv
    EC_costs['curtailed_load'] += (E['Ecur_load'] * p_cur_load).sum()
    EC_costs['curtailed_pv'] += (E['Ecur_pv'] * p_cur_pv).sum()

    # MV grid obtained, feed-in
    Ec_MV_costs = df_HH.copy()
    Eg_MV_reven = df_HH.copy()
    p_MV_fit = parameter_economics.energycosts_income['C_market_fit']
    p_MV_obtain = parameter_economics.energycosts_income['C_market_obtain']

    Ec_MV_costs = E['Ec_MV'] * p_MV_obtain
    Eg_MV_reven = E['Eg_MV'] * p_MV_fit

    # For ECM, only with community storage
    EC_costs['bss_LV'] = (Ec_LV_ECM * p_t).sum().values
    EC_reven['bss_LV'] = (Eg_LV_ECM * p_t).sum().values

    # Put all together in a DataFrame and save it
    E_costs = pd.DataFrame(index=E.index)
    E_reven = pd.DataFrame(index=E.index)

    E_costs['Ec_LV_costs'] = Ec_LV_costs.sum().values
    E_costs['Ec_MV_costs'] = Ec_MV_costs

    E_reven['Ec_LV_flex_reven'] = Ec_LV_flex_reven.sum().values
    E_reven['Eg_LV_flex_reven'] = Eg_LV_flex_reven.sum().values
    E_reven['Ec_self_flex_reven'] = Ec_self_flex_reven
    E_reven['Eg_self_flex_reven'] = Eg_self_flex_reven
    E_reven['Ec_cur_load_reven'] = Ec_cur_load_reven
    E_reven['Eg_cur_pv_reven'] = Eg_cur_pv_reven
    E_reven['Eg_MV_reven'] = Eg_MV_reven
    E_reven['Eg_LV_reven'] = Eg_LV_reven.sum().values

    E_costs.round(3).to_csv(self.economics_folder + '03_Costs_per_HH_in_Euro.csv', header=True, index = True)
    E_reven.round(3).to_csv(self.economics_folder + '03_Revenues_per_HH_in_Euro.csv', header=True, index = True)
    EC_costs = pd.DataFrame(data=EC_costs, index=[0])
    EC_costs.round(3).to_csv(self.economics_folder + '03_Costs_ECM_in_Euro.csv', header=True, index = True)
    EC_reven = pd.DataFrame(data=EC_reven, index=[0])
    EC_reven.round(3).to_csv(self.economics_folder + '03_Revenues_ECM_in_Euro.csv', header=True, index = True)


  ########################################
  ### Sum up of annuity Costs and Revenues
  ########################################
  def plot_costs_revenues_per_HH(self):
    E_costs = pd.read_csv(self.economics_folder + '03_Costs_per_HH_in_Euro.csv', delimiter = ',', low_memory=False).drop('Unnamed: 0', axis=1)
    E_reven = pd.read_csv(self.economics_folder + '03_Revenues_per_HH_in_Euro.csv', delimiter = ',', low_memory=False).drop('Unnamed: 0', axis=1)

    print(E_costs.sum())
    print(E_reven.sum())

    bright = sns.color_palette("bright", 10)
    dark = sns.color_palette("dark", 10)
    colors = ['red', dark[3], 'blue', dark[0], 'green', 'yellow']

    # Plot PV
    E_barplot1 = E_costs.copy()
    E_barplot2 = E_reven.copy()

    E_barplot1['Ec_MV_costs'] += E_barplot1['Ec_LV_costs']

    E_barplot2['Eg_MV_reven'] += E_barplot2['Eg_LV_reven']
    E_barplot2['Eg_self_flex_reven'] += E_barplot2['Eg_MV_reven']
    E_barplot2['Ec_self_flex_reven'] += E_barplot2['Eg_self_flex_reven']
    E_barplot2['Eg_LV_flex_reven'] += E_barplot2['Ec_self_flex_reven']
    E_barplot2['Ec_LV_flex_reven'] += E_barplot2['Eg_LV_flex_reven']
    E_barplot2['Eg_cur_pv_reven'] += E_barplot2['Ec_LV_flex_reven']
    E_barplot2['Ec_cur_load_reven'] += E_barplot2['Eg_cur_pv_reven']

    s10 = sns.barplot(x = E_barplot1.index, y = 'Ec_MV_costs', data = -E_barplot1, color = dark[1])
    s9 = sns.barplot(x = E_barplot1.index, y = 'Ec_LV_costs', data = -E_barplot1, color = dark[0])

    s8 = sns.barplot(x = E_barplot2.index, y = 'Ec_cur_load_reven', data = E_barplot2, color = bright[7])
    s7 = sns.barplot(x = E_barplot2.index, y = 'Eg_cur_pv_reven', data = E_barplot2, color = bright[6])
    s6 = sns.barplot(x = E_barplot2.index, y = 'Ec_LV_flex_reven', data = E_barplot2, color = bright[5])
    s5 = sns.barplot(x = E_barplot2.index, y = 'Eg_LV_flex_reven', data = E_barplot2, color = bright[4])
    s4 = sns.barplot(x = E_barplot2.index, y = 'Ec_self_flex_reven', data = E_barplot2, color = bright[3])
    s3 = sns.barplot(x = E_barplot2.index, y = 'Eg_self_flex_reven', data = E_barplot2, color = bright[2])
    s2 = sns.barplot(x = E_barplot2.index, y = 'Eg_MV_reven', data = E_barplot2, color = bright[1])
    s1 = sns.barplot(x = E_barplot2.index, y = 'Eg_LV_reven', data = E_barplot2, color = bright[0])

    Ec_MV_bar = mpatches.Patch(color=dark[1], label='MV obtained')
    Ec_LV_bar = mpatches.Patch(color=dark[0], label='LV obtained')

    Ec_cur_load_bar = mpatches.Patch(color=bright[7], label='curtailed load')
    Eg_cur_pv_flex_bar = mpatches.Patch(color=bright[6], label='curtailed pv')
    Ec_LV_flex_bar = mpatches.Patch(color=bright[5], label='LV flex con')
    Eg_LV_flex_bar = mpatches.Patch(color=bright[4], label='LV flex gen')
    Ec_self_flex_bar = mpatches.Patch(color=bright[3], label='self flex con')
    Eg_self_flex_bar = mpatches.Patch(color=bright[2], label='self flex gen')
    Eg_MV_bar = mpatches.Patch(color=bright[1], label='MV feed-in')
    Eg_LV_bar = mpatches.Patch(color=bright[0], label='LV traded')
    plt.legend(handles=[Ec_cur_load_bar, Eg_cur_pv_flex_bar, Ec_LV_flex_bar, Eg_LV_flex_bar, Ec_self_flex_bar, Eg_self_flex_bar, Eg_MV_bar, Eg_LV_bar, Ec_LV_bar, Ec_MV_bar])
    plt.xlabel('Households')
    plt.ylabel('Revenue in Euro')
    plt.show()

  def write_to_conclusion_table(self):
    capex_ECM = pd.read_csv(self.economics_folder + '01_invest_ECM_in_Euro.csv', delimiter = ',', low_memory=False).drop('Unnamed: 0', axis=1)
    capex_HH = pd.read_csv(self.economics_folder + '01_invest_per_HH_in_Euro.csv', delimiter = ',', low_memory=False).drop('Unnamed: 0', axis=1)
    opex_ECM = pd.read_csv(self.economics_folder + '02_opex_EMC_in_Euro.csv', delimiter = ',', low_memory=False).drop('Unnamed: 0', axis=1)
    opex_HH = pd.read_csv(self.economics_folder + '02_opex_per_HH_in_Euro.csv', delimiter = ',', low_memory=False).drop('Unnamed: 0', axis=1)
    E_costs_ECM = pd.read_csv(self.economics_folder + '03_Costs_ECM_in_Euro.csv', delimiter = ',', low_memory=False).drop('Unnamed: 0', axis=1)
    E_reven_ECM = pd.read_csv(self.economics_folder + '03_Revenues_ECM_in_Euro.csv', delimiter = ',', low_memory=False).drop('Unnamed: 0', axis=1)
    E_costs_HH = pd.read_csv(self.economics_folder + '03_Costs_per_HH_in_Euro.csv', delimiter = ',', low_memory=False).drop('Unnamed: 0', axis=1)
    E_reven_HH = pd.read_csv(self.economics_folder + '03_Revenues_per_HH_in_Euro.csv', delimiter = ',', low_memory=False).drop('Unnamed: 0', axis=1)

    print(self.scenario)
    C = pd.DataFrame()
    C = pd.concat([C, -capex_HH], axis=1)
    C = pd.concat([C, -opex_HH], axis=1)
    C['E_costs'] = -E_costs_HH.sum(axis=1)
    C['E_reven'] = E_reven_HH.sum(axis=1)
    #C = pd.concat([C, E_costs_HH], axis=1)
    #C = pd.concat([C, E_reven_HH], axis=1)

    print(C)
    print(C.sum(axis=1))
    '''
    if os.path.exists(self.conclusion_folder + str(net_name)):
      C = pd.read_csv(self.conclusion_folder + str(net_name), delimiter = ',', low_memory=False).drop('Unnamed: 0', axis=1)
    else:
      pass
    '''
