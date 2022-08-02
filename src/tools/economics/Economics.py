import numpy as np 
import pandas as pd
import sys
import os

import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import seaborn as sns

import tools.tools as tt

class MainEconomics():
  def __init__(self, scenario, net_name, time_scope):
    self.time_scope = time_scope
    self.output_dir = os.path.join("./", "output-files/"+''.join(str(num) for num in scenario)+"/"+str(net_name)+"/"+time_scope['start_time'][0:10]+"_"+time_scope['end_time'][0:10]+"_"+time_scope['t_freq']+"/")

    #self.v = self.read_data(self.output_dir+'res_bus_vm_pu.csv')
    #self.ll = self.read_data(self.output_dir+'res_line_load_percent.csv')
    #self.tl = self.read_data(self.output_dir+'res_trafo_load_percent.csv')
    self.power = self.read_data(self.output_dir+'power_total_MW.csv')
    self.curtailed_power = self.read_data(self.output_dir+'curtailed_power_MW.csv')
    self.curtailed_power_pv = pd.DataFrame(columns=self.curtailed_power.columns, index=self.curtailed_power.index).fillna(0)
    self.curtailed_power_load = pd.DataFrame(columns=self.curtailed_power.columns, index=self.curtailed_power.index).fillna(0)
    self.curtailed_power_pv[self.curtailed_power >= 0] = self.curtailed_power[self.curtailed_power >= 0]
    self.curtailed_power_load[self.curtailed_power < 0] = -self.curtailed_power[self.curtailed_power < 0]
    self.losses_p = self.read_data(self.output_dir+'losses_active_power_MW.csv')
    self.storage_p = self.read_data(self.output_dir+'storage_active_power_MW.csv')
    #self.storage_soc = self.read_data(self.output_dir+'storage_state_of_charge_percent.csv') # in powerflow wird aktuell noch e_mwh an soc übergeben
    self.trafo_p = self.read_data(self.output_dir+'trafo_active_power_MW.csv')
    self.pv_p = self.read_data(self.output_dir+'pv_active_power_MW.csv')
    self.load_p = self.read_data(self.output_dir+'load_active_power_MW.csv')
    self.bss_p_flex = self.read_data(self.output_dir+'bss_active_power_flex_MW.csv')
    self.load_p_flex = self.read_data(self.output_dir+'load_active_power_flex_MW.csv')

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


  def energyflow_on_HH_level(self):
    # plot config
    in_percent = True
    # development env
    test_case = True


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

    # BSS Flexibility
    Ec_LV_flex[(dE_HH >= 0) & (flex_bss > 0) & (pv > load)] = dE_HH[(dE_HH >= 0) & (flex_bss > 0) & (pv > load)]
    Ec_LV_flex[(dE_HH >= 0) & (flex_bss > 0) & (pv <= load)] = flex_bss[(dE_HH >= 0) & (flex_bss > 0) & (pv <= load)]

    Eg_LV_flex[(dE_HH < 0) & (flex_bss < 0) & (pv <= load)] = -dE_HH[(dE_HH < 0) & (flex_bss < 0) & (pv <= load)]
    Eg_LV_flex[(dE_HH < 0) & (flex_bss < 0) & (pv > load)] = -flex_bss[(dE_HH < 0) & (flex_bss < 0) & (pv > load)]

    ### CHECKEN !!! ###
    #Ec_self_flex[(flex_bss > 0)] = flex_bss[(flex_bss > 0)] - Ec_LV_flex[(flex_bss > 0)]
    #Ec_self -= Ec_self_flex
    
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


    Ec_LV -= Ec_LV_flex
    Eg_LV -= Eg_LV_flex
    Ec_self -= Ec_self_flex
    Eg_self -= Eg_self_flex

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
      #'''
      for i in [str(i) for i in range(10,20)]:#Ec_LV.columns:#
      #for i in ['15']:#Ec_LV.columns:#
        fig, ax = plt.subplots()
        #ax.plot(dE_HH[i])
        #ax.plot((Ec_self[i] + Ec_LV[i] + Ec_MV[i] + Ec_LV_flex[i] + Ec_self_flex[i]))
        #ax.plot(load[i])
        ax.plot((Eg_self[i] + Eg_LV[i] + Eg_MV[i] + Eg_LV_flex[i] + Eg_self_flex[i]))
        ax.plot((pv[i] - bss[i]))
        #ax.plot(Ec_self[i] + Ec_LV[i] + Ec_MV[i])
        #ax.plot(pv[i])
        #ax.plot(bss[i])
        #ax.plot(Eg_self[i])
        #ax.plot(Eg_LV[i])
        #ax.plot(Eg_MV[i])
        #ax.plot(Eg_LV_flex[i])
        #ax.plot(Ec_self[i])
        #ax.plot(Ec_self_flex[i])
        #ax.plot(Ec_LV_flex[i])
        #ax.plot(load[i])
        #ax.plot(pv[i])
        #ax.plot(flex_load_pos[i])
        #ax.plot(Ec_self_flex[i])
        #ax.plot(Eg_LV[i])
        #ax.plot(Eg_MV[i])
        #ax.plot(load[i])
        #ax.plot(bss[i])
        #ax.plot(flex_bss[i] + bss[i])
        #ax.plot(load[i])
        #ax.plot((abs(Ec_self) + abs(Ec_MV) + abs(Ec_LV) - (load)))
        #ax.plot((abs(Eg_self) + abs(Eg_MV) + abs(Eg_LV) - (pv - bss)))
      ax.set_xlabel('Time')
      ax.set_ylabel('dP of each HH in MW')
      plt.show()
      #'''

      def print_mmm(df):
        print('Min:  ' + str(df.min().min()))
        print('Max:  ' + str(df.max().max()))
        print('Mean: ' + str(df.mean().mean()))
        print('Error: ' + str(df.sum().sum()/60))

      # Bilanzcheck
      print_mmm((abs(Ec_self) + abs(Ec_MV) + abs(Ec_LV) - (load + flex_bss_LV)))#+ abs(Ec_self_flex) + abs(Ec_LV_flex)
      print_mmm((abs(Eg_self) + abs(Eg_MV) + abs(Eg_LV) + abs(Eg_LV_flex) - (pv - bss + flex_bss_LV)))

      print('Generation (incl. BSS) : ' + str(((E.sum(axis=0).Eg_self + E.sum(axis=0).Eg_MV + E.sum(axis=0).Eg_LV)/60).round(3)) + ' MWh') # 60
      print('Consumption (incl. BSS): ' + str(((E.sum(axis=0).Ec_self + E.sum(axis=0).Ec_MV + E.sum(axis=0).Ec_LV + E.sum(axis=0).Ec_LV_flex + E.sum(axis=0).Ec_self_flex)/60).round(3)) + ' MWh') # 60

      #sys.exit(0)

    # Seaborn Colors
    bright = sns.color_palette("bright", 10)
    dark = sns.color_palette("dark", 10)

    #'''
    # Plot PV
    E_barplot1 = E
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
    s1 = sns.barplot(x = E.index, y = 'Eg_self_flex', data = E_barplot1, color = dark[3])
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
    E_barplot2 = E
    E_barplot2['Ec_self'] += E_barplot2['Ec_self_flex']
    E_barplot2['Ec_LV_flex'] += E_barplot2['Ec_self']
    E_barplot2['Ec_LV'] +=  E_barplot2['Ec_LV_flex']
    E_barplot2['Ec_MV'] +=  E_barplot2['Ec_LV']
    E_barplot2['Ecur_load'] +=  E_barplot2['Ec_MV']
    if in_percent == True:
      for i in E_barplot2.index: # plot in percent
        E_barplot2.loc[i] = E_barplot2.loc[i] / E_barplot1['Ecur_load'].loc[i] * 100
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

    if self.time_scope['t_freq'] != None:#'1D':
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


