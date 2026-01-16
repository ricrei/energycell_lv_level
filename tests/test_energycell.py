"""
run these tests with `pytest tests/test_something.py` or `pytest tests` or simply `pytest`
pytest will look for all files starting with "test_" and run all functions
within this file. For basic example of tests you can look at our workshop
https://github.com/rl-institut/workshop/tree/master/test-driven-development.
Otherwise https://docs.pytest.org/en/latest/ and https://docs.python.org/3/library/unittest.html
are also good support.
"""
import pytest
from src.tools import EnergyCell
#from spice_ev.generate import generate_schedule
import tools.EnergyCell as ec
import tools.tools as tt
from tools.evaluation.EvaluationSingleCase import EvaluationSingleCase
import pandapower as pp
import pandas as pd
import csv
import os

time_scope = { 'start_time' : '2017-05-30 00:00:00+01:00',
               'end_time'   : '2017-05-31 00:00:00+01:00',
               't_freq'     : '1H',
             }


time_scope_winter = { 'start_time' : '2017-01-03 00:00:00+01:00',
                      'end_time'   : '2017-01-10 00:00:00+01:00',
                      't_freq'     : '1T',
                      'name'       : 'winter'
                    }


time_scope_summer = { 'start_time' : '2017-05-27 00:00:00+02:00',
                      'end_time'   : '2017-06-03 00:00:00+02:00',
                      't_freq'     : '1T',
                      'name'       : 'summer'
                    }

time_scope_autumn = { 'start_time' : '2017-10-20 00:00:00+02:00',
                      'end_time'   : '2017-10-27 00:00:00+02:00',
                      't_freq'     : '1T',
                      'name'       : 'autumn'
                    }

time_scope_spring = { 'start_time' : '2017-03-05 00:00:00+01:00',
                      'end_time'   : '2017-03-12 00:00:00+01:00',
                      't_freq'     : '1T',
                      'name'       : 'spring'
                    }

time_scope_all_seasons = [
                      time_scope_spring,
                      time_scope_summer,
                      time_scope_autumn,
                      time_scope_winter
                      ]

control_parameter = {
  'PV_cos_phi' : .9,
  'BSS_efficiency_AC2Bat' : 0.953,
  'BSS_efficiency_Bat2AC' : 0.955,
  'BSS_efficiency_storage' : 0.959,
  'BSS_start_soc_percent_winter' : 25,
  'BSS_start_soc_percent_summer' : 75,
  'BSS_start_soc_percent'        : 50,
  'BSS_sizing_factor_power_to_capacity' : .75,
  'BSS_sizing_factor_bss_to_pv' : .75,
  'BSS_soc_reserve_percent_winter' : 20,
  'EV_usable_c_bat' : 100,
  'EV_start_soc' : 100,
  'EV_charging_power' : .011,     # in MW
  'EV_charging_efficiency' : .9,  # 0-1
  'EV_direct_charge_limit' : 80,  # in %
  'EV_linear_charge_limit' : 90,
  'EV_linear_charge_limit_summer' : 80,
  'HP_cos_phi' : 1,
  'HP_t_sink' : 45,
  'HP_t_ground_source' : 8,
  'HP_TES_max_capacity_mwh' : .0325,
  'HP_building_capacity_mwh' : .014,
  'HP_TES_start_soc' : .5, # 0-1
  'HP_TES_start_soc_winter' : 0.25, # 0-1
  'HP_TES_start_soc_summer' : 0.75, # 0-1
  'HP_TES_loss_per_s' : 0.04 / 86400,   #4% per day / 86400
  'HP_max_p_kw': 0.012, # in MW
  'HP_upper_TES_reserve': 1., # default = 1
  'HP_lower_TES_reserve': 0., # default = 0
  'HP_upper_TES_reserve_summer': .5, # default = 1
  'HP_lower_TES_reserve_winter': .1, # default = 0
  'EC_size': 99,
  'EC_demografic_category': 'rural', #rural/suburban/urban, only relevant for simulations without power flow analysis
}

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
            "test_net_n_load_branch",  #14
            None]  #15

test_scenarios = [
   [1,0,0,0,0,0,0], # conventional
    [2,0,0,1,1,0,0], # full-electrified
    [2,0,0,1,1,1,0],
    [3,1,0,0,0,0,0], # PV, Q(U)
    [3,1,0,0,0,1,0],
    [4,1,0,1,1,0,1],
    [4,1,0,1,1,0,0], # full-electrified and maximum pv-expansion
    [4,1,0,1,1,1,0],
    [6,1,1,1,1,0,0], # battery storage systems, full-electrified and maximum pv-expansion
    [6,1,1,1,1,1,0],
    [6,1,2,1,1,0,0],
    [6,1,2,1,1,1,0],
    [6,1,3,1,1,0,0],
    [6,1,3,1,1,1,0],
    [6,1,4,1,1,0,0],
    [6,1,4,1,1,1,0],
    [6,1,5,1,1,0,0],
    [6,1,5,1,1,1,0],
    [7,1,0,3,3,0,0],
    [7,1,0,5,2,1,0],
    [7,1,0,2,2,1,0],
    [7,1,0,3,3,1,0],
    [8,1,1,5,2,1,0],
    [8,1,2,2,2,1,0],
    [8,1,3,3,3,0,0],
    [8,1,3,3,3,1,0],
    [8,1,3,3,3,1,1],
    [8,1,4,3,3,1,0],
    [8,1,4,3,3,1,1],
    [9,1,3,3,3,1,0],
    [9,1,3,3,3,1,1],
]

test_scenarios_no_curt = [
   [1,0,0,0,0,0,0], # conventional
    [2,0,0,1,1,0,0], # full-electrified
    [3,2,0,0,0,0,0], # PV, fix cos(phi)
    [4,2,0,1,1,0,0], # full-electrified and maximum pv-expansion
    [6,2,1,1,1,0,0], # battery storage systems, full-electrified and maximum pv-expansion
    [6,2,2,1,1,0,0],
]

def read_csv(path):
    with open(path, newline="", encoding="utf-8") as f:
        return list(csv.reader(f))

def list_files(directory):
    return os.listdir(directory)

def check_pandapower_network(net_number,scenario,control_parameter,time_scope,network_file):
    # create df with pandapower network for example scenario:
    e = ec.EnergyCell(net_name=net_name[net_number],
                      scenario=scenario,
                      control_parameter=control_parameter,
                      time_scope=time_scope,
                      save_full_data=True,  # default: False
                      verbose=True,  # default: False
                      grid_reinforce_dev_mode=False, # default: False
                      grid_analysis=True)  # default: False
    e_data = e.grid.net

    # get dataframe from pickle file:
    example_data = pp.from_pickle(network_file)

    for element in ['bus', 'load', 'sgen', 'storage', 'switch', 'ext_grid', 'line', 'trafo',
                    'bus_geodata', 'loadcases', 'res_bus', 'res_line', 'res_trafo', 'res_ext_grid',
                    'res_load']:
        if element in example_data:
            # rearrange columns of new dataframe according to columns from dataframe from pickle file:
            e_data[element] = e_data[element][example_data[element].columns]
            # remove index name for 'loadcases' since it is not included in pickle file
            if element == 'loadcases':
                e_data[element].index.name = None
            # compare dataframe
            pd.testing.assert_frame_equal(e_data[element], example_data[element])
    return e

def evaluate_results_pf(ecell, energy_results_file, network_results_file, grid_analysis):

    # Run powerflow
    ecell.run_pf_timeseries()
    # Initialize Evaluation
    ecell.initiate_evaluation()

    # test if energy results are correct
    res_dict_energy = ecell.eva.calculate_relevant_outputdata(grid_analysis)
    # get energy results dictionary from pickle file:
    example_energy_results = tt.decompress_pickle(energy_results_file)
    assert res_dict_energy == example_energy_results

    # test if network problem results are correct
    res_dict_net_problems = ecell.eva.calculate_net_problems()
    # get network problem results dictionary from pickle file:
    example_network_results = tt.decompress_pickle(network_results_file)
    assert res_dict_net_problems == example_network_results



def test_creation_pandapower_network_pf_1000000(net_number=8, scenario=[1, 0, 0, 0, 0, 0, 0],
                                                control_parameter=control_parameter,
                                                time_scope=time_scope,
                                                network_file="examples/simbench_rural_2_[1, 0, 0, 0, 0, 0, 0].p"):
    check_pandapower_network(net_number=net_number, scenario=scenario,
                             control_parameter=control_parameter, time_scope=time_scope,
                             network_file=network_file)

def test_calculate_relevant_outputdata_pf_1000000(energy_results_file="examples/simbench_rural_2_[1, 0, 0, 0, 0, 0, 0]_res_dict_energy.pbz2",
                                       network_results_file="examples/simbench_rural_2_[1, 0, 0, 0, 0, 0, 0]_res_dict_network.pbz2"):
    # create df with pandapower network for example scenario:
    e = ec.EnergyCell(net_name=net_name[8],
                      scenario=[1, 0, 0, 0, 0, 0, 0],
                      control_parameter=control_parameter,
                      time_scope=time_scope,
                      save_full_data=True,  # default: False
                      verbose=True,  # default: False
                      grid_reinforce_dev_mode=False,
                      grid_analysis=True)  # default: False

    evaluate_results_pf(ecell=e, energy_results_file=energy_results_file,
                        network_results_file=network_results_file, grid_analysis=True)

def test_scenarios(scenarios=test_scenarios, net_number=8, control_parameter=control_parameter,
                   time_scope=time_scope):

    for scenario in scenarios:
        # define file paths:
        network_file = "examples/" + net_name[net_number] + "_" + str(scenario) + ".p"
        energy_results_file = "examples/" + net_name[net_number] + "_" + str(scenario) \
                              + "_res_dict_energy.pbz2"
        network_results_file = "examples/" + net_name[net_number] + "_" + str(scenario) \
                               + "_res_dict_network.pbz2"

        # test network dataframe:
        e = check_pandapower_network(net_number=net_number, scenario=scenario,
                                     control_parameter=control_parameter, time_scope=time_scope,
                                     network_file=network_file)

        # test evaluation results:
        evaluate_results_pf(ecell=e, energy_results_file=energy_results_file,
                            network_results_file=network_results_file, grid_analysis=True)

def test_compare_output_files(folder_name='2017-05-30_2017-05-31_1H'):
    # test for scenario [6131110] for grid rural 2
    # test_scenarios() must be run through first in order to get the csv files

    file_names = list_files('examples/'+ str(folder_name))

    for file in file_names:

        csv1 = read_csv('examples/'+ str(folder_name) + '/' +str(file))
        csv2 = read_csv('output-files/6131110/simbench_rural_2/'+str(folder_name) + '/'+str(file))

        if file != '01_control_paramters.csv':
            assert len(csv1) == len(csv2), "Unterschiedliche Anzahl an Zeilen"

        if file != '00_simulation_date.csv':
            for i, (row1, row2) in enumerate(zip(csv1, csv2), start=1):
                assert row1 == row2, f"Unterschied in Datei {file} in Zeile {i}: {row1} != {row2}"

def test_scenarios_community():
    # test for comparison of results with and without powerflow
    # only for scenarios without curtailment since curtailment can only be applied on scenarios with grid

    control_parameter['PV_cos_phi'] = 1

    for scenario in test_scenarios_no_curt:
        # create df with pandapower network for example scenario:
        e_pf = ec.EnergyCell(net_name=net_name[8],
                          scenario=scenario,
                          control_parameter=control_parameter,
                          time_scope=time_scope,
                          save_full_data=True,  # default: False
                          verbose=True,  # default: False
                          grid_reinforce_dev_mode=False,
                          grid_analysis=True)  # default: False

        # create df with pandapower network for example scenario:
        e_no_pf = ec.EnergyCell(net_name=net_name[15],
                          scenario=scenario,
                          control_parameter=control_parameter,
                          time_scope=time_scope,
                          save_full_data=True,  # default: False
                          verbose=True,  # default: False
                          grid_reinforce_dev_mode=False,
                          grid_analysis=False)  # default: False

        # Run powerflow or energy balance calculations:
        e_pf.run_pf_timeseries()
        e_no_pf.run_pf_timeseries()
        # Initialize Evaluation
        e_pf.initiate_evaluation()
        e_no_pf.initiate_evaluation()

        # get result dictionaries:
        res_dict_energy_pf = e_pf.eva.calculate_relevant_outputdata(grid_analysis=True)
        res_dict_energy_no_pf = e_no_pf.eva.calculate_relevant_outputdata(grid_analysis=False)

        # test if energy results are correct:
        assert res_dict_energy_no_pf['pv_gen'] == res_dict_energy_pf['pv_gen']
        assert res_dict_energy_no_pf['hp_con'] == res_dict_energy_pf['hp_con']
        assert res_dict_energy_no_pf['ev_con'] == res_dict_energy_pf['ev_con']
        assert res_dict_energy_no_pf['load_con'] == res_dict_energy_pf['load_con']
        assert res_dict_energy_no_pf['ttl_con'] == res_dict_energy_pf['ttl_con']
        assert res_dict_energy_no_pf['ttl_losses'] < res_dict_energy_pf['ttl_losses']
        assert res_dict_energy_no_pf['ratio_gen_con'] == res_dict_energy_pf['ratio_gen_con']
        #assert res_dict_energy_no_pf['self_suff'] > res_dict_energy_pf['self_suff'] # stimmt so nicht, ToDo: Wie kann hierfür ein Test geschrieben werden?
        #assert res_dict_energy_no_pf['pv_con_rate'] <= res_dict_energy_pf['pv_con_rate'] # stimmt so nicht, ToDo: Wie kann hierfür ein Test geschrieben werden?


