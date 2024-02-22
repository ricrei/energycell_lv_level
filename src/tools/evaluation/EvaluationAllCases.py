import os
import csv
import time
import numpy as np
import pandas as pd
import tools.tools as tt

import bz2
import _pickle as cPickle


class EvaluationAllCases():
  def __init__(self, net_names, scenarios, time_scopes):
    output_df_dir = 'output-files/000_evaluation_dicts/'
    #output_df_dir = 'output-files/000_evaluation_dicts_shortened_data/' #Tabea

    net_name = ["kerber_rural_1", #0
                "kerber_rural_2", #1
                "kerber_rural_3", #2
                "kerber_rural_4",  #3
                "kerber_village",  #4
                "kerber_suburb_1", #5
                "kerber_suburb_2",  #6
                "simbench_rural_1", #7
                "simbench_rural_2", #8
                "simbench_rural_3", #9
                "simbench_suburb_4", #10
                "simbench_suburb_5", #11
                "simbench_urban_6",  #12
                "test_net_one_load_branch", #13
                "test_net_n_load_branch"]  #14

    df_eva_v = pd.DataFrame(columns=['time', 'voltage', 'scenario', 'timescope', 'gridID', 'busID'])
    df_helper_v = pd.DataFrame(columns=['time', 'voltage', 'scenario', 'timescope', 'gridID', 'busID'])

    df_eva_l = pd.DataFrame(columns=['time', 'lineloading', 'scenario', 'timescope', 'gridID', 'lineID'])
    df_helper_l = pd.DataFrame(columns=['time', 'lineloading', 'scenario', 'timescope', 'gridID', 'lineID'])

    df_eva_t = pd.DataFrame(columns=['time', 'trafoloading', 'scenario', 'timescope', 'gridID', 'trafoID'])
    df_helper_t = pd.DataFrame(columns=['time', 'trafoloading', 'scenario', 'timescope', 'gridID', 'trafoID'])

    print(scenarios)

    print('Load Output Data')
    for scenario_i in scenarios:
      for time_scope_i in time_scopes:
        for net_name_i in net_names:
          scenario_i = self.convert_scenario(scenario_i)
          output_dir = os.path.join("./", "output-files/"+str(scenario_i)+"/"+str(net_name[net_name_i])+"/"+time_scope_i['start_time'][0:10]+"_"+time_scope_i['end_time'][0:10]+"_"+time_scope_i['t_freq']+"/")
          index = 's' + str(scenario_i) + 'n' + str(net_name_i) + str(time_scope_i['name'])
          print('create: ' + str(index))
          eva = {}
          eva[index] = {}
          eva[index]['scenario'] = scenario_i
          eva[index]['net_name'] = net_name[net_name_i]
          eva[index]['net_name_i'] = net_name_i
          eva[index]['time_scope_name'] = time_scope_i['name']
          eva[index]['power'] = self.read_data(output_dir+'power_total_MW.csv')
          print(eva[index]['power']['ev'].sum())
          eva[index]['v'] = self.read_data(output_dir+'res_bus_vm_pu.csv')
          eva[index]['ll'] = self.read_data(output_dir+'res_line_load_percent.csv')
          eva[index]['tl'] = self.read_data(output_dir+'res_trafo_load_percent.csv')
          trafo_p = self.read_data(output_dir+'trafo_active_power_MW.csv')
          losses = self.read_data(output_dir+'losses_active_power_MW.csv')
          eva[index]['curtailed_power'] = self.calculate_aggregated_curtailed_power(output_dir)
          eva[index]['SelfSufficiancy'], eva[index]['PVConsumption']= self.calculate_relevant_outputdata(eva[index]['power'], losses, trafo_p, eva[index]['curtailed_power'])
          eva[index]['v_under'], eva[index]['v_over'], eva[index]['v_events'], eva[index]['ll_over'], eva[index]['l_events'], eva[index]['tl_over'], eva[index]['t_events'] = self.calculate_net_problems_overall_eva(eva[index]['v'], eva[index]['ll'], eva[index]['tl'])
          eva[index]['storage_power'] = self.read_data(output_dir+'storage_active_power_MW.csv')
          eva[index]['soc_bss'] = self.read_data(output_dir+'storage_state_of_charge_percent.csv')

          tt.compress_pickle(output_df_dir + str(index)+'.pbz2', eva[index])
          if index == 'sD111410n8winter':
            print(eva['sD111410n8winter']['power']['ev'].sum())
          if index == 'sE111410n8winter':
            print(eva['sE111410n8winter']['power']['ev'].sum())
          if index == 'sC111410n8winter':
            print(eva['sC111410n8winter']['power']['ev'].sum())
          if index == 'sF111410n8winter':
            print(eva['sF111410n8winter']['power']['ev'].sum())
          if index == 'sG111410n8winter':
            print(eva['sG111410n8winter']['power']['ev'].sum())

  ### Helper Methods ###
  def convert_scenario(self, scenario_i):
    scenario = ''
    for i in scenario_i:
      scenario += str(i)
    return scenario

  def read_data(self, filename):
    data = pd.read_csv(filename, delimiter = ',', low_memory=False)#, engine='python')
    #data = data.drop(['Unnamed: 0'], axis=1)
    #data['TIMESTAMP'] = pd.to_datetime(times['TIMESTAMP'], utc=True)
    #data['timestamp'] = data['timestamp'][0:19]
    #data['timestamp'] = data['timestamp'].tz_localize()
    data['timestamp'] = pd.to_datetime(data['timestamp'], utc=False)
    data = data.set_index('timestamp')
    #data.index = pd.DatetimeIndex(data.index, tz=None, ambiguous='infer')
    #data.index = pd.to_datetime(data.index)
    #data.index = data.index.tz_localize(tz=None, ambiguous='infer')
    #data.index = data.index.tz_convert('UTC')
    data.index = data.index.tz_localize(None)

    return data

  def shorted_data(self, data, t_freq):
    data_shorted = data.resample(t_freq).mean()
    data_shorted = data_shorted.round(4)
    data_shorted.index = pd.DatetimeIndex(data_shorted.index, tz=None, ambiguous='infer')

    return data_shorted

  ### Calculate Output Data ###
  def calculate_relevant_outputdata(self, power, losses, trafo_p, curtail_power):
    losses = losses.sum().sum()
    sum_pv = power.pv.sum()
    sum_total_pv = power.pv.sum() + curtail_power.pv.sum()
    sum_hp = power.hp.sum()
    sum_ev = power.ev.sum()
    sum_load = power.load.sum()
    sum_total_load = sum_hp + sum_load + sum_ev

    Res = -1*trafo_p.values
    
    Res_pos = Res[Res > 0]
    Res_neg = Res[Res < 0]

    SelfSufficiancy = (sum_total_load + losses + Res_neg.sum())*100/(sum_total_load + losses)
    if sum_total_pv > 0:
      PVConsumption = (sum_total_pv - Res_pos.sum() - curtail_power.pv.sum())*100/sum_total_pv
    else:
      PVConsumption = sum_total_pv*0.0

    return SelfSufficiancy, PVConsumption

  def calculate_net_problems_overall_eva(self, v, ll, tl):

    v_limit_over = 1.1
    v_limit_under = .9

    v_events = len(v.index)*len(v.columns)
    ll_events = len(ll.index)*len(ll.columns)
    tl_events = len(tl.index)*len(tl.columns)

    v_over = v[v>v_limit_over].fillna(0)
    v_over[v_over > 0] = 1 
    sum_v_over = v_over[v_over.columns].sum(axis=1).sum()

    v_under = v[v<v_limit_under].fillna(0)
    v_under[v_under > 0] = 1 
    sum_v_under = v_under[v_under.columns].sum(axis=1).sum()

    ll = ll[ll>100].fillna(0)
    ll[ll > 0] = 1 
    sum_ll = ll[ll.columns].sum(axis=1).sum()

    tl = tl[tl>100].fillna(0)
    tl[tl > 0] = 1 
    sum_tl = tl[tl.columns].sum(axis=1).sum()

    return sum_v_under, sum_v_over, v_events, sum_ll, ll_events, sum_tl, tl_events

  def calculate_aggregated_curtailed_power(self, output_dir):
    curtailed_power = self.read_data(output_dir+'curtailed_power_MW.csv')

    curtailed_power_pv = pd.DataFrame(columns=curtailed_power.columns, index=curtailed_power.index).fillna(0)
    curtailed_power_load = pd.DataFrame(columns=curtailed_power.columns, index=curtailed_power.index).fillna(0)
    curtailed_power_pv[curtailed_power >= 0] = curtailed_power[curtailed_power >= 0]
    curtailed_power_load[curtailed_power < 0] = -curtailed_power[curtailed_power < 0]

    df = pd.DataFrame()
    df['load'] = curtailed_power_load.sum(axis=1)
    df['pv'] = curtailed_power_pv.sum(axis=1)
    return df
