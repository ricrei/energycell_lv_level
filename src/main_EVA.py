import os
import csv
import sys
import time
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib as mpl
import pandapower.plotting.plotly as ppply
import seaborn as sns
from datetime import datetime, timedelta

import tools.evaluation.Evaluation as evaluation
import tools.evaluation.EvaluationHP as evaluationHP

# Handle date time conversions between pandas and matplotlib
from pandas.plotting import register_matplotlib_converters
register_matplotlib_converters()

import tools.tools as tt

import bz2
import _pickle as cPickle

### RUN in development mode ###
'''
run script to load data
  python -i main_EVA.py
import importlib once
  import importlib
to excecute method run this command everytime
  importlib.reload(evaluation), evaluation.plot_curtailed_power(eva, save_fig_dir=save_fig_dir)
'''

#############################
### Define all gird names ###
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
            "test_net_one_load_branch"]  #13
############################

#############################
### Define all gird names ###
sfh_name = ["SFH15", 	#A
            "SFH45", 	#B
            "SFH100" ] 	#C
############################



# Image output directory
save_fig_dir = 'img/'

output_df_dir = 'output-files/000_evaluation_dicts/'

def load_scenario_data(scenarios, grids=['n7','n8','n9','n10','n11'], seasons=['spring','summer','autumn','winter']):
  print('Load eva dicts ...')
  files = os.listdir(output_df_dir)

  eva = {}
  for index in files:
    if index[1:8] in scenarios:
      for n in grids:
        if n in index:
          for s in seasons:
            if s in index:
              #print('Load: '+str(index))
              name = index[0:-5]
              eva[str(name)] = tt.decompress_pickle(output_df_dir + index)

  return eva

n = 4    # Number of timescopes
m = 4*4  # Number of timescopes * Number of scenarios


##################################
########## Print Output ##########
##################################
# --- Power --- #
'''
scenarios = ['4101110']
eva = load_scenario_data(scenarios)
for grid in ['n7','n8','n9','n10','n11']:
  evaluation.calculate_outputdata(eva, scenarios, grid, save_fig_dir=save_fig_dir+'calculated_data.png')
'''

#sys.exit(0)


###############################
########## Timeplots ##########
###############################

# --- Power --- #


# --- Power and Components loading --- #
scenarios = ['A002010', 'A302010', 'A102010', 'A003010', 'A303010', 'A103010', \
             'A004010', 'A304010', 'A104010', 'A005010', 'A305010', 'A105010', \
             'B002010', 'B302010', 'B102010', 'B003010', 'B303010', 'B103010', \
             'B004010', 'B304010', 'B104010', 'B005010', 'B305010', 'B105010', \
             'C002010', 'C302010', 'C102010', 'C003010', 'C303010', 'C103010', \
             'C004010', 'C304010', 'C104010', 'C005010', 'C305010', 'C105010', \
             'A006010', 'A306010', 'A106010', 'A007010', 'A307010', 'A107010', \
             'A008010', 'A308010', 'A108010', 'A009010', 'A309010', 'A109010', \
             'B006010', 'B306010', 'B106010', 'B007010', 'B307010', 'B107010', \
             'B008010', 'B308010', 'B108010', 'B009010', 'B309010', 'B109010', \
             'C006010', 'C306010', 'C106010', 'C007010', 'C307010', 'C107010', \
             'C008010', 'C308010', 'C108010', 'C009010', 'C309010', 'C109010']
'''
  
#eva = load_scenario_data(scenarios, grids=['n8'], seasons=['winter'])
#plot_residualload_overall_eva(power, save_fig_dir=save_fig_dir+ 'res_grid_sfh100_plot1.png')
#evaluation.plot_residualload_grid_issues_subplot_overall_eva(eva1=eva['sC108010n8spring'], eva2=eva['sC109010n8spring'], save_fig_dir=save_fig_dir+ 'res_grid_sfh100.png')
#evaluation.plot_residualload_grid_issues_subplot_overall_eva(eva1=eva['sC105010n8winter'], eva2=eva['sC109010n8winter'], save_fig_dir=save_fig_dir+ 'res_grid_sfh100.png')
#evaluation.plot_residualload_grid_issues_subplot_overall_eva(eva1=eva['sC106010n8summer'], eva2=eva['sC109010n8summer'], save_fig_dir=save_fig_dir+ 'res_grid_sfh100.png')

'''
eva = load_scenario_data(scenarios, grids=['n8'], seasons=['spring'])
evaluation.plot_residualload_grid_issues_subplot_overall_eva_4_plots(SFHscenario='A' ,eva1=eva['sA102010n8spring'], eva2=eva['sA103010n8spring'], eva3=eva['sA104010n8spring'], eva4=eva['sA105010n8spring'], save_fig_dir=save_fig_dir+ 'ResiLoad_res_sfh15_spring_all_tes_pv_large.png')
evaluation.plot_residualload_grid_issues_subplot_overall_eva_4_plots(SFHscenario='A' ,eva1=eva['sA106010n8spring'], eva2=eva['sA107010n8spring'], eva3=eva['sA108010n8spring'], eva4=eva['sA109010n8spring'], save_fig_dir=save_fig_dir+ 'LinChFID_res_sfh15_spring_all_tes_pv_large.png')
evaluation.plot_residualload_grid_issues_subplot_overall_eva_4_plots(SFHscenario='B' ,eva1=eva['sB102010n8spring'], eva2=eva['sB103010n8spring'], eva3=eva['sB104010n8spring'], eva4=eva['sB105010n8spring'], save_fig_dir=save_fig_dir+ 'ResiLoad_res_sfh45_spring_all_tes_pv_large.png')
evaluation.plot_residualload_grid_issues_subplot_overall_eva_4_plots(SFHscenario='B' ,eva1=eva['sB106010n8spring'], eva2=eva['sB107010n8spring'], eva3=eva['sB108010n8spring'], eva4=eva['sB109010n8spring'], save_fig_dir=save_fig_dir+ 'LinChFID_res_sfh45_spring_all_tes_pv_large.png')
evaluation.plot_residualload_grid_issues_subplot_overall_eva_4_plots(SFHscenario='C' ,eva1=eva['sC102010n8spring'], eva2=eva['sC103010n8spring'], eva3=eva['sC104010n8spring'], eva4=eva['sC105010n8spring'], save_fig_dir=save_fig_dir+ 'ResiLoad_res_sfh100_spring_all_tes_pv_large.png')
evaluation.plot_residualload_grid_issues_subplot_overall_eva_4_plots(SFHscenario='C' ,eva1=eva['sC106010n8spring'], eva2=eva['sC107010n8spring'], eva3=eva['sC108010n8spring'], eva4=eva['sC109010n8spring'], save_fig_dir=save_fig_dir+ 'LinChFID_res_sfh100_spring_all_tes_pv_large.png')

evaluation.plot_residualload_grid_issues_subplot_overall_eva_4_plots(SFHscenario='A' ,eva1=eva['sA302010n8spring'], eva2=eva['sA303010n8spring'], eva3=eva['sA304010n8spring'], eva4=eva['sA305010n8spring'], save_fig_dir=save_fig_dir+ 'ResiLoad_res_sfh15_spring_all_tes_pv_medium.png')
evaluation.plot_residualload_grid_issues_subplot_overall_eva_4_plots(SFHscenario='A' ,eva1=eva['sA306010n8spring'], eva2=eva['sA307010n8spring'], eva3=eva['sA308010n8spring'], eva4=eva['sA309010n8spring'], save_fig_dir=save_fig_dir+ 'LinChFID_res_sfh15_spring_all_tes_pv_medium.png')
evaluation.plot_residualload_grid_issues_subplot_overall_eva_4_plots(SFHscenario='B' ,eva1=eva['sB302010n8spring'], eva2=eva['sB303010n8spring'], eva3=eva['sB304010n8spring'], eva4=eva['sB305010n8spring'], save_fig_dir=save_fig_dir+ 'ResiLoad_res_sfh45_spring_all_tes_pv_medium.png')
evaluation.plot_residualload_grid_issues_subplot_overall_eva_4_plots(SFHscenario='B' ,eva1=eva['sB306010n8spring'], eva2=eva['sB307010n8spring'], eva3=eva['sB308010n8spring'], eva4=eva['sB309010n8spring'], save_fig_dir=save_fig_dir+ 'LinChFID_res_sfh45_spring_all_tes_pv_medium.png')
evaluation.plot_residualload_grid_issues_subplot_overall_eva_4_plots(SFHscenario='C' ,eva1=eva['sC302010n8spring'], eva2=eva['sC303010n8spring'], eva3=eva['sC304010n8spring'], eva4=eva['sC305010n8spring'], save_fig_dir=save_fig_dir+ 'ResiLoad_res_sfh100_spring_all_tes_pv_medium.png')
evaluation.plot_residualload_grid_issues_subplot_overall_eva_4_plots(SFHscenario='C' ,eva1=eva['sC306010n8spring'], eva2=eva['sC307010n8spring'], eva3=eva['sC308010n8spring'], eva4=eva['sC309010n8spring'], save_fig_dir=save_fig_dir+ 'LinChFID_res_sfh100_spring_all_tes_pv_medium.png')

evaluation.plot_residualload_grid_issues_subplot_overall_eva_4_plots(SFHscenario='A' ,eva1=eva['sA002010n8spring'], eva2=eva['sA003010n8spring'], eva3=eva['sA004010n8spring'], eva4=eva['sA005010n8spring'], save_fig_dir=save_fig_dir+ 'ResiLoad_res_sfh15_spring_all_tes_pv_no.png')
evaluation.plot_residualload_grid_issues_subplot_overall_eva_4_plots(SFHscenario='A' ,eva1=eva['sA006010n8spring'], eva2=eva['sA007010n8spring'], eva3=eva['sA008010n8spring'], eva4=eva['sA009010n8spring'], save_fig_dir=save_fig_dir+ 'LinChFID_res_sfh15_spring_all_tes_pv_no.png')
evaluation.plot_residualload_grid_issues_subplot_overall_eva_4_plots(SFHscenario='B' ,eva1=eva['sB002010n8spring'], eva2=eva['sB003010n8spring'], eva3=eva['sB004010n8spring'], eva4=eva['sB005010n8spring'], save_fig_dir=save_fig_dir+ 'ResiLoad_res_sfh45_spring_all_tes_pv_no.png')
evaluation.plot_residualload_grid_issues_subplot_overall_eva_4_plots(SFHscenario='B' ,eva1=eva['sB006010n8spring'], eva2=eva['sB007010n8spring'], eva3=eva['sB008010n8spring'], eva4=eva['sB009010n8spring'], save_fig_dir=save_fig_dir+ 'LinChFID_res_sfh45_spring_all_tes_pv_no.png')
evaluation.plot_residualload_grid_issues_subplot_overall_eva_4_plots(SFHscenario='C' ,eva1=eva['sC002010n8spring'], eva2=eva['sC003010n8spring'], eva3=eva['sC004010n8spring'], eva4=eva['sC005010n8spring'], save_fig_dir=save_fig_dir+ 'ResiLoad_res_sfh100_spring_all_tes_pv_no.png')
evaluation.plot_residualload_grid_issues_subplot_overall_eva_4_plots(SFHscenario='C' ,eva1=eva['sC006010n8spring'], eva2=eva['sC007010n8spring'], eva3=eva['sC008010n8spring'], eva4=eva['sC009010n8spring'], save_fig_dir=save_fig_dir+ 'LinChFID_res_sfh100_spring_all_tes_pv_no.png')
'''
'''
eva = load_scenario_data(scenarios, grids=['n8'], seasons=['winter'])
evaluation.plot_residualload_grid_issues_subplot_overall_eva_4_plots(SFHscenario='A' ,eva1=eva['sA102010n8winter'], eva2=eva['sA103010n8winter'], eva3=eva['sA104010n8winter'], eva4=eva['sA105010n8winter'], save_fig_dir=save_fig_dir+ 'ResiLoad_res_sfh15_winter_all_tes_pv_large.png')
evaluation.plot_residualload_grid_issues_subplot_overall_eva_4_plots(SFHscenario='A' ,eva1=eva['sA106010n8winter'], eva2=eva['sA107010n8winter'], eva3=eva['sA108010n8winter'], eva4=eva['sA109010n8winter'], save_fig_dir=save_fig_dir+ 'LinChFID_res_sfh15_winter_all_tes_pv_large.png')
evaluation.plot_residualload_grid_issues_subplot_overall_eva_4_plots(SFHscenario='B' ,eva1=eva['sB102010n8winter'], eva2=eva['sB103010n8winter'], eva3=eva['sB104010n8winter'], eva4=eva['sB105010n8winter'], save_fig_dir=save_fig_dir+ 'ResiLoad_res_sfh45_winter_all_tes_pv_large.png')
evaluation.plot_residualload_grid_issues_subplot_overall_eva_4_plots(SFHscenario='B' ,eva1=eva['sB106010n8winter'], eva2=eva['sB107010n8winter'], eva3=eva['sB108010n8winter'], eva4=eva['sB109010n8winter'], save_fig_dir=save_fig_dir+ 'LinChFID_res_sfh45_winter_all_tes_pv_large.png')
evaluation.plot_residualload_grid_issues_subplot_overall_eva_4_plots(SFHscenario='C' ,eva1=eva['sC102010n8winter'], eva2=eva['sC103010n8winter'], eva3=eva['sC104010n8winter'], eva4=eva['sC105010n8winter'], save_fig_dir=save_fig_dir+ 'ResiLoad_res_sfh100_winter_all_tes_pv_large.png')
evaluation.plot_residualload_grid_issues_subplot_overall_eva_4_plots(SFHscenario='C' ,eva1=eva['sC106010n8winter'], eva2=eva['sC107010n8winter'], eva3=eva['sC108010n8winter'], eva4=eva['sC109010n8winter'], save_fig_dir=save_fig_dir+ 'LinChFID_res_sfh100_winter_all_tes_pv_large.png')

evaluation.plot_residualload_grid_issues_subplot_overall_eva_4_plots(SFHscenario='A' ,eva1=eva['sA302010n8winter'], eva2=eva['sA303010n8winter'], eva3=eva['sA304010n8winter'], eva4=eva['sA305010n8winter'], save_fig_dir=save_fig_dir+ 'ResiLoad_res_sfh15_winter_all_tes_pv_medium.png')
evaluation.plot_residualload_grid_issues_subplot_overall_eva_4_plots(SFHscenario='A' ,eva1=eva['sA306010n8winter'], eva2=eva['sA307010n8winter'], eva3=eva['sA308010n8winter'], eva4=eva['sA309010n8winter'], save_fig_dir=save_fig_dir+ 'LinChFID_res_sfh15_winter_all_tes_pv_medium.png')
evaluation.plot_residualload_grid_issues_subplot_overall_eva_4_plots(SFHscenario='B' ,eva1=eva['sB302010n8winter'], eva2=eva['sB303010n8winter'], eva3=eva['sB304010n8winter'], eva4=eva['sB305010n8winter'], save_fig_dir=save_fig_dir+ 'ResiLoad_res_sfh45_winter_all_tes_pv_medium.png')
evaluation.plot_residualload_grid_issues_subplot_overall_eva_4_plots(SFHscenario='B' ,eva1=eva['sB306010n8winter'], eva2=eva['sB307010n8winter'], eva3=eva['sB308010n8winter'], eva4=eva['sB309010n8winter'], save_fig_dir=save_fig_dir+ 'LinChFID_res_sfh45_winter_all_tes_pv_medium.png')
evaluation.plot_residualload_grid_issues_subplot_overall_eva_4_plots(SFHscenario='C' ,eva1=eva['sC302010n8winter'], eva2=eva['sC303010n8winter'], eva3=eva['sC304010n8winter'], eva4=eva['sC305010n8winter'], save_fig_dir=save_fig_dir+ 'ResiLoad_res_sfh100_winter_all_tes_pv_medium.png')
evaluation.plot_residualload_grid_issues_subplot_overall_eva_4_plots(SFHscenario='C' ,eva1=eva['sC306010n8winter'], eva2=eva['sC307010n8winter'], eva3=eva['sC308010n8winter'], eva4=eva['sC309010n8winter'], save_fig_dir=save_fig_dir+ 'LinChFID_res_sfh100_winter_all_tes_pv_medium.png')

evaluation.plot_residualload_grid_issues_subplot_overall_eva_4_plots(SFHscenario='A' ,eva1=eva['sA002010n8winter'], eva2=eva['sA003010n8winter'], eva3=eva['sA004010n8winter'], eva4=eva['sA005010n8winter'], save_fig_dir=save_fig_dir+ 'ResiLoad_res_sfh15_winter_all_tes_pv_no.png')
evaluation.plot_residualload_grid_issues_subplot_overall_eva_4_plots(SFHscenario='A' ,eva1=eva['sA006010n8winter'], eva2=eva['sA007010n8winter'], eva3=eva['sA008010n8winter'], eva4=eva['sA009010n8winter'], save_fig_dir=save_fig_dir+ 'LinChFID_res_sfh15_winter_all_tes_pv_no.png')
evaluation.plot_residualload_grid_issues_subplot_overall_eva_4_plots(SFHscenario='B' ,eva1=eva['sB002010n8winter'], eva2=eva['sB003010n8winter'], eva3=eva['sB004010n8winter'], eva4=eva['sB005010n8winter'], save_fig_dir=save_fig_dir+ 'ResiLoad_res_sfh45_winter_all_tes_pv_no.png')
evaluation.plot_residualload_grid_issues_subplot_overall_eva_4_plots(SFHscenario='B' ,eva1=eva['sB006010n8winter'], eva2=eva['sB007010n8winter'], eva3=eva['sB008010n8winter'], eva4=eva['sB009010n8winter'], save_fig_dir=save_fig_dir+ 'LinChFID_res_sfh45_winter_all_tes_pv_no.png')
evaluation.plot_residualload_grid_issues_subplot_overall_eva_4_plots(SFHscenario='C' ,eva1=eva['sC002010n8winter'], eva2=eva['sC003010n8winter'], eva3=eva['sC004010n8winter'], eva4=eva['sC005010n8winter'], save_fig_dir=save_fig_dir+ 'ResiLoad_res_sfh100_winter_all_tes_pv_no.png')
evaluation.plot_residualload_grid_issues_subplot_overall_eva_4_plots(SFHscenario='C' ,eva1=eva['sC006010n8winter'], eva2=eva['sC007010n8winter'], eva3=eva['sC008010n8winter'], eva4=eva['sC009010n8winter'], save_fig_dir=save_fig_dir+ 'LinChFID_res_sfh100_winter_all_tes_pv_no.png')
'''
'''
eva = load_scenario_data(scenarios, grids=['n8'], seasons=['autumn'])
evaluation.plot_residualload_grid_issues_subplot_overall_eva_4_plots(SFHscenario='A' ,eva1=eva['sA102010n8autumn'], eva2=eva['sA103010n8autumn'], eva3=eva['sA104010n8autumn'], eva4=eva['sA105010n8autumn'], save_fig_dir=save_fig_dir+ 'ResiLoad_res_sfh15_autumn_all_tes_pv_large.png')
evaluation.plot_residualload_grid_issues_subplot_overall_eva_4_plots(SFHscenario='A' ,eva1=eva['sA106010n8autumn'], eva2=eva['sA107010n8autumn'], eva3=eva['sA108010n8autumn'], eva4=eva['sA109010n8autumn'], save_fig_dir=save_fig_dir+ 'LinChFID_res_sfh15_autumn_all_tes_pv_large.png')
evaluation.plot_residualload_grid_issues_subplot_overall_eva_4_plots(SFHscenario='B' ,eva1=eva['sB102010n8autumn'], eva2=eva['sB103010n8autumn'], eva3=eva['sB104010n8autumn'], eva4=eva['sB105010n8autumn'], save_fig_dir=save_fig_dir+ 'ResiLoad_res_sfh45_autumn_all_tes_pv_large.png')
evaluation.plot_residualload_grid_issues_subplot_overall_eva_4_plots(SFHscenario='B' ,eva1=eva['sB106010n8autumn'], eva2=eva['sB107010n8autumn'], eva3=eva['sB108010n8autumn'], eva4=eva['sB109010n8autumn'], save_fig_dir=save_fig_dir+ 'LinChFID_res_sfh45_autumn_all_tes_pv_large.png')
evaluation.plot_residualload_grid_issues_subplot_overall_eva_4_plots(SFHscenario='C' ,eva1=eva['sC102010n8autumn'], eva2=eva['sC103010n8autumn'], eva3=eva['sC104010n8autumn'], eva4=eva['sC105010n8autumn'], save_fig_dir=save_fig_dir+ 'ResiLoad_res_sfh100_autumn_all_tes_pv_large.png')
evaluation.plot_residualload_grid_issues_subplot_overall_eva_4_plots(SFHscenario='C' ,eva1=eva['sC106010n8autumn'], eva2=eva['sC107010n8autumn'], eva3=eva['sC108010n8autumn'], eva4=eva['sC109010n8autumn'], save_fig_dir=save_fig_dir+ 'LinChFID_res_sfh100_autumn_all_tes_pv_large.png')

evaluation.plot_residualload_grid_issues_subplot_overall_eva_4_plots(SFHscenario='A' ,eva1=eva['sA302010n8autumn'], eva2=eva['sA303010n8autumn'], eva3=eva['sA304010n8autumn'], eva4=eva['sA305010n8autumn'], save_fig_dir=save_fig_dir+ 'ResiLoad_res_sfh15_autumn_all_tes_pv_medium.png')
evaluation.plot_residualload_grid_issues_subplot_overall_eva_4_plots(SFHscenario='A' ,eva1=eva['sA306010n8autumn'], eva2=eva['sA307010n8autumn'], eva3=eva['sA308010n8autumn'], eva4=eva['sA309010n8autumn'], save_fig_dir=save_fig_dir+ 'LinChFID_res_sfh15_autumn_all_tes_pv_medium.png')
evaluation.plot_residualload_grid_issues_subplot_overall_eva_4_plots(SFHscenario='B' ,eva1=eva['sB302010n8autumn'], eva2=eva['sB303010n8autumn'], eva3=eva['sB304010n8autumn'], eva4=eva['sB305010n8autumn'], save_fig_dir=save_fig_dir+ 'ResiLoad_res_sfh45_autumn_all_tes_pv_medium.png')
evaluation.plot_residualload_grid_issues_subplot_overall_eva_4_plots(SFHscenario='B' ,eva1=eva['sB306010n8autumn'], eva2=eva['sB307010n8autumn'], eva3=eva['sB308010n8autumn'], eva4=eva['sB309010n8autumn'], save_fig_dir=save_fig_dir+ 'LinChFID_res_sfh45_autumn_all_tes_pv_medium.png')
evaluation.plot_residualload_grid_issues_subplot_overall_eva_4_plots(SFHscenario='C' ,eva1=eva['sC302010n8autumn'], eva2=eva['sC303010n8autumn'], eva3=eva['sC304010n8autumn'], eva4=eva['sC305010n8autumn'], save_fig_dir=save_fig_dir+ 'ResiLoad_res_sfh100_autumn_all_tes_pv_medium.png')
evaluation.plot_residualload_grid_issues_subplot_overall_eva_4_plots(SFHscenario='C' ,eva1=eva['sC306010n8autumn'], eva2=eva['sC307010n8autumn'], eva3=eva['sC308010n8autumn'], eva4=eva['sC309010n8autumn'], save_fig_dir=save_fig_dir+ 'LinChFID_res_sfh100_autumn_all_tes_pv_medium.png')

evaluation.plot_residualload_grid_issues_subplot_overall_eva_4_plots(SFHscenario='A' ,eva1=eva['sA002010n8autumn'], eva2=eva['sA003010n8autumn'], eva3=eva['sA004010n8autumn'], eva4=eva['sA005010n8autumn'], save_fig_dir=save_fig_dir+ 'ResiLoad_res_sfh15_autumn_all_tes_pv_no.png')
evaluation.plot_residualload_grid_issues_subplot_overall_eva_4_plots(SFHscenario='A' ,eva1=eva['sA006010n8autumn'], eva2=eva['sA007010n8autumn'], eva3=eva['sA008010n8autumn'], eva4=eva['sA009010n8autumn'], save_fig_dir=save_fig_dir+ 'LinChFID_res_sfh15_autumn_all_tes_pv_no.png')
evaluation.plot_residualload_grid_issues_subplot_overall_eva_4_plots(SFHscenario='B' ,eva1=eva['sB002010n8autumn'], eva2=eva['sB003010n8autumn'], eva3=eva['sB004010n8autumn'], eva4=eva['sB005010n8autumn'], save_fig_dir=save_fig_dir+ 'ResiLoad_res_sfh45_autumn_all_tes_pv_no.png')
evaluation.plot_residualload_grid_issues_subplot_overall_eva_4_plots(SFHscenario='B' ,eva1=eva['sB006010n8autumn'], eva2=eva['sB007010n8autumn'], eva3=eva['sB008010n8autumn'], eva4=eva['sB009010n8autumn'], save_fig_dir=save_fig_dir+ 'LinChFID_res_sfh45_autumn_all_tes_pv_no.png')
evaluation.plot_residualload_grid_issues_subplot_overall_eva_4_plots(SFHscenario='C' ,eva1=eva['sC002010n8autumn'], eva2=eva['sC003010n8autumn'], eva3=eva['sC004010n8autumn'], eva4=eva['sC005010n8autumn'], save_fig_dir=save_fig_dir+ 'ResiLoad_res_sfh100_autumn_all_tes_pv_no.png')
evaluation.plot_residualload_grid_issues_subplot_overall_eva_4_plots(SFHscenario='C' ,eva1=eva['sC006010n8autumn'], eva2=eva['sC007010n8autumn'], eva3=eva['sC008010n8autumn'], eva4=eva['sC009010n8autumn'], save_fig_dir=save_fig_dir+ 'LinChFID_res_sfh100_autumn_all_tes_pv_no.png')
'''
'''
eva = load_scenario_data(scenarios, grids=['n8'], seasons=['summer'])
evaluation.plot_residualload_grid_issues_subplot_overall_eva_4_plots(SFHscenario='A' ,eva1=eva['sA102010n8summer'], eva2=eva['sA103010n8summer'], eva3=eva['sA104010n8summer'], eva4=eva['sA105010n8summer'], save_fig_dir=save_fig_dir+ 'ResiLoad_res_sfh15_summer_all_tes_pv_large.png')
evaluation.plot_residualload_grid_issues_subplot_overall_eva_4_plots(SFHscenario='A' ,eva1=eva['sA106010n8summer'], eva2=eva['sA107010n8summer'], eva3=eva['sA108010n8summer'], eva4=eva['sA109010n8summer'], save_fig_dir=save_fig_dir+ 'LinChFID_res_sfh15_summer_all_tes_pv_large.png')
evaluation.plot_residualload_grid_issues_subplot_overall_eva_4_plots(SFHscenario='B' ,eva1=eva['sB102010n8summer'], eva2=eva['sB103010n8summer'], eva3=eva['sB104010n8summer'], eva4=eva['sB105010n8summer'], save_fig_dir=save_fig_dir+ 'ResiLoad_res_sfh45_summer_all_tes_pv_large.png')
evaluation.plot_residualload_grid_issues_subplot_overall_eva_4_plots(SFHscenario='B' ,eva1=eva['sB106010n8summer'], eva2=eva['sB107010n8summer'], eva3=eva['sB108010n8summer'], eva4=eva['sB109010n8summer'], save_fig_dir=save_fig_dir+ 'LinChFID_res_sfh45_summer_all_tes_pv_large.png')
evaluation.plot_residualload_grid_issues_subplot_overall_eva_4_plots(SFHscenario='C' ,eva1=eva['sC102010n8summer'], eva2=eva['sC103010n8summer'], eva3=eva['sC104010n8summer'], eva4=eva['sC105010n8summer'], save_fig_dir=save_fig_dir+ 'ResiLoad_res_sfh100_summer_all_tes_pv_large.png')
evaluation.plot_residualload_grid_issues_subplot_overall_eva_4_plots(SFHscenario='C' ,eva1=eva['sC106010n8summer'], eva2=eva['sC107010n8summer'], eva3=eva['sC108010n8summer'], eva4=eva['sC109010n8summer'], save_fig_dir=save_fig_dir+ 'LinChFID_res_sfh100_summer_all_tes_pv_large.png')

evaluation.plot_residualload_grid_issues_subplot_overall_eva_4_plots(SFHscenario='A' ,eva1=eva['sA302010n8summer'], eva2=eva['sA303010n8summer'], eva3=eva['sA304010n8summer'], eva4=eva['sA305010n8summer'], save_fig_dir=save_fig_dir+ 'ResiLoad_res_sfh15_summer_all_tes_pv_medium.png')
evaluation.plot_residualload_grid_issues_subplot_overall_eva_4_plots(SFHscenario='A' ,eva1=eva['sA306010n8summer'], eva2=eva['sA307010n8summer'], eva3=eva['sA308010n8summer'], eva4=eva['sA309010n8summer'], save_fig_dir=save_fig_dir+ 'LinChFID_res_sfh15_summer_all_tes_pv_medium.png')
evaluation.plot_residualload_grid_issues_subplot_overall_eva_4_plots(SFHscenario='B' ,eva1=eva['sB302010n8summer'], eva2=eva['sB303010n8summer'], eva3=eva['sB304010n8summer'], eva4=eva['sB305010n8summer'], save_fig_dir=save_fig_dir+ 'ResiLoad_res_sfh45_summer_all_tes_pv_medium.png')
evaluation.plot_residualload_grid_issues_subplot_overall_eva_4_plots(SFHscenario='B' ,eva1=eva['sB306010n8summer'], eva2=eva['sB307010n8summer'], eva3=eva['sB308010n8summer'], eva4=eva['sB309010n8summer'], save_fig_dir=save_fig_dir+ 'LinChFID_res_sfh45_summer_all_tes_pv_medium.png')
evaluation.plot_residualload_grid_issues_subplot_overall_eva_4_plots(SFHscenario='C' ,eva1=eva['sC302010n8summer'], eva2=eva['sC303010n8summer'], eva3=eva['sC304010n8summer'], eva4=eva['sC305010n8summer'], save_fig_dir=save_fig_dir+ 'ResiLoad_res_sfh100_summer_all_tes_pv_medium.png')
evaluation.plot_residualload_grid_issues_subplot_overall_eva_4_plots(SFHscenario='C' ,eva1=eva['sC306010n8summer'], eva2=eva['sC307010n8summer'], eva3=eva['sC308010n8summer'], eva4=eva['sC309010n8summer'], save_fig_dir=save_fig_dir+ 'LinChFID_res_sfh100_summer_all_tes_pv_medium.png')

evaluation.plot_residualload_grid_issues_subplot_overall_eva_4_plots(SFHscenario='A' ,eva1=eva['sA002010n8summer'], eva2=eva['sA003010n8summer'], eva3=eva['sA004010n8summer'], eva4=eva['sA005010n8summer'], save_fig_dir=save_fig_dir+ 'ResiLoad_res_sfh15_summer_all_tes_pv_no.png')
evaluation.plot_residualload_grid_issues_subplot_overall_eva_4_plots(SFHscenario='A' ,eva1=eva['sA006010n8summer'], eva2=eva['sA007010n8summer'], eva3=eva['sA008010n8summer'], eva4=eva['sA009010n8summer'], save_fig_dir=save_fig_dir+ 'LinChFID_res_sfh15_summer_all_tes_pv_no.png')
evaluation.plot_residualload_grid_issues_subplot_overall_eva_4_plots(SFHscenario='B' ,eva1=eva['sB002010n8summer'], eva2=eva['sB003010n8summer'], eva3=eva['sB004010n8summer'], eva4=eva['sB005010n8summer'], save_fig_dir=save_fig_dir+ 'ResiLoad_res_sfh45_summer_all_tes_pv_no.png')
evaluation.plot_residualload_grid_issues_subplot_overall_eva_4_plots(SFHscenario='B' ,eva1=eva['sB006010n8summer'], eva2=eva['sB007010n8summer'], eva3=eva['sB008010n8summer'], eva4=eva['sB009010n8summer'], save_fig_dir=save_fig_dir+ 'LinChFID_res_sfh45_summer_all_tes_pv_no.png')
evaluation.plot_residualload_grid_issues_subplot_overall_eva_4_plots(SFHscenario='C' ,eva1=eva['sC002010n8summer'], eva2=eva['sC003010n8summer'], eva3=eva['sC004010n8summer'], eva4=eva['sC005010n8summer'], save_fig_dir=save_fig_dir+ 'ResiLoad_res_sfh100_summer_all_tes_pv_no.png')
evaluation.plot_residualload_grid_issues_subplot_overall_eva_4_plots(SFHscenario='C' ,eva1=eva['sC006010n8summer'], eva2=eva['sC007010n8summer'], eva3=eva['sC008010n8summer'], eva4=eva['sC009010n8summer'], save_fig_dir=save_fig_dir+ 'LinChFID_res_sfh100_summer_all_tes_pv_no.png')
'''

# --- Curtailment: Self-Sufficiancy and PV Consumption (Season - Grid) --- #
scenario = scenarios

#eva = load_scenario_data(scenario, seasons=['spring', 'autumn', 'summer', 'winter'])
#evaluationHP.plot_heatmap_self_consumption_tes_to_pv(eva, scenario, controlled='LinCh_FID', save_fig_dir=save_fig_dir + 'LinChFID_hmap_self_con_all_seasons_tes_to_pv.png')
#evaluationHP.plot_heatmap_self_sufficiency_tes_to_pv(eva, scenario, controlled='LinCh_FID', save_fig_dir=save_fig_dir + 'LinChFID_hmap_self_suff_all_seasons_tes_to_pv.png')
#evaluationHP.plot_heatmap_curtailed_load_tes_to_pv(eva, scenario, controlled='LinCh_FID', save_fig_dir=save_fig_dir +   'LinChFID_hmap_curtailed_load_all_seasons_tes_to_pv.png')
#evaluationHP.plot_heatmap_curtailed_pv_tes_to_pv(eva, scenario, controlled='LinCh_FID', save_fig_dir=save_fig_dir +     'LinChFID_hmap_curtailed_pv_all_seasons_tes_to_pv.png')
#evaluationHP.plot_heatmap_mean_trafo_load_tes_to_pv(eva, scenario, controlled='LinCh_FID', save_fig_dir= save_fig_dir + 'LinChFID_hmap_trafo_load_all_seasons_tes_to_pv.png')
#evaluationHP.plot_heatmap_max_line_load_tes_to_pv(eva, scenario, controlled='LinCh_FID', save_fig_dir=save_fig_dir + 'LinChFID_hmap_max_line_load_all_season_tes_to_pv.png')
#evaluationHP.plot_heatmap_min_voltage_tes_to_pv(eva, scenario, controlled='LinCh_FID', save_fig_dir=save_fig_dir + 'LinChFID_hmap_min_voltage_all_season_tes_to_pv.png')
#evaluationHP.plot_heatmap_max_voltage_tes_to_pv(eva, scenario, controlled='LinCh_FID', save_fig_dir=save_fig_dir + 'LinChFID_hmap_max_voltage_all_season_tes_to_pv.png')
#evaluationHP.plot_heatmap_sum_el_demand_hp_tes_to_pv(eva, scenario, controlled='LinCh_FID', save_fig_dir=save_fig_dir + 'LinChFID_hmap_sum_el_demand_hp_tes_to_pv.png')

#evaluationHP.plot_heatmap_self_consumption_tes_to_pv(eva, scenario, controlled='Resi_Load', save_fig_dir=save_fig_dir + 'Resiload_hmap_self_con_all_seasons_tes_to_pv.png')
#evaluationHP.plot_heatmap_self_sufficiency_tes_to_pv(eva, scenario, controlled='Resi_Load', save_fig_dir=save_fig_dir + 'Resiload_hmap_self_suff_all_seasons_tes_to_pv.png')
#evaluationHP.plot_heatmap_curtailed_load_tes_to_pv(eva, scenario, controlled='Resi_Load', save_fig_dir=save_fig_dir +   'Resiload_hmap_curtailed_load_all_seasons_tes_to_pv.png')
#evaluationHP.plot_heatmap_curtailed_pv_tes_to_pv(eva, scenario, controlled='Resi_Load', save_fig_dir=save_fig_dir +     'Resiload_hmap_curtailed_pv_all_seasons_tes_to_pv.png')
#evaluationHP.plot_heatmap_mean_trafo_load_tes_to_pv(eva, scenario, controlled='Resi_Load', save_fig_dir= save_fig_dir + 'Resiload_hmap_trafo_load_all_seasons_tes_to_pv.png')
#evaluationHP.plot_heatmap_max_line_load_tes_to_pv(eva, scenario, controlled='Resi_Load', save_fig_dir=save_fig_dir + 'Resiload_hmap_max_line_load_all_season_tes_to_pv.png')
#evaluationHP.plot_heatmap_min_voltage_tes_to_pv(eva, scenario, controlled='Resi_Load', save_fig_dir=save_fig_dir + 'Resiload_hmap_min_voltage_all_season_tes_to_pv.png')
#evaluationHP.plot_heatmap_max_voltage_tes_to_pv(eva, scenario, controlled='Resi_Load', save_fig_dir=save_fig_dir + 'Resiload_hmap_max_voltage_all_season_tes_to_pv.png')
#evaluationHP.plot_heatmap_sum_el_demand_hp_tes_to_pv(eva, scenario, controlled='Resi_Load', save_fig_dir=save_fig_dir + 'Resiload_hmap_sum_el_demand_hp_tes_to_pv.png')

#eva = load_scenario_data(scenario, seasons=['winter'])
#evaluationHP.plot_heatmap_self_consumption_tes_to_pv(eva, scenario, controlled='LinCh_FID', save_fig_dir=save_fig_dir + 'LinChFID_hmap_self_con_winter_tes_to_pv.png')
#evaluationHP.plot_heatmap_self_sufficiency_tes_to_pv(eva, scenario, controlled='LinCh_FID', save_fig_dir=save_fig_dir + 'LinChFID_hmap_self_suff_winter_tes_to_pv.png')
#evaluationHP.plot_heatmap_curtailed_pv_tes_to_pv(eva, scenario, controlled='LinCh_FID', save_fig_dir=save_fig_dir +     'LinChFID_hmap_curtailed_pv_winter_tes_to_pv.png')
#evaluationHP.plot_heatmap_curtailed_load_tes_to_pv(eva, scenario, controlled='LinCh_FID', save_fig_dir=save_fig_dir +   'LinChFID_hmap_curtailed_load_winter_tes_to_pv.png')
#evaluationHP.plot_heatmap_mean_trafo_load_tes_to_pv(eva, scenario, controlled='LinCh_FID', save_fig_dir= save_fig_dir + 'LinChFID_hmap_trafo_load_winter_tes_to_pv.png')
#evaluationHP.plot_heatmap_max_line_load_tes_to_pv(eva, scenario, controlled='LinCh_FID', save_fig_dir=save_fig_dir + 'LinChFID_hmap_max_line_load_winter_tes_to_pv.png')

#evaluationHP.plot_heatmap_self_consumption_tes_to_pv(eva, scenario, controlled='Resi_Load', save_fig_dir=save_fig_dir + 'Resiload_hmap_self_con_winter_tes_to_pv.png')
#evaluationHP.plot_heatmap_self_sufficiency_tes_to_pv(eva, scenario, controlled='Resi_Load', save_fig_dir=save_fig_dir + 'Resiload_hmap_self_suff_winter_tes_to_pv.png')
#evaluationHP.plot_heatmap_curtailed_pv_tes_to_pv(eva, scenario, controlled='Resi_Load', save_fig_dir=save_fig_dir +     'Resiload_hmap_curtailed_pv_winter_tes_to_pv.png')
#evaluationHP.plot_heatmap_curtailed_load_tes_to_pv(eva, scenario, controlled='Resi_Load', save_fig_dir=save_fig_dir +   'Resiload_hmap_curtailed_load_winter_tes_to_pv.png')
#evaluationHP.plot_heatmap_mean_trafo_load_tes_to_pv(eva, scenario, controlled='Resi_Load', save_fig_dir= save_fig_dir + 'Resiload_hmap_trafo_load_winter_tes_to_pv.png')
#evaluationHP.plot_heatmap_max_line_load_tes_to_pv(eva, scenario, controlled='Resi_Load', save_fig_dir=save_fig_dir + 'Resiload_hmap_max_line_load_winter_tes_to_pv.png')

#eva = load_scenario_data(scenario, seasons=['summer'])
#evaluationHP.plot_heatmap_self_consumption_tes_to_pv(eva, scenario, controlled='LinCh_FID', save_fig_dir=save_fig_dir + 'LinChFID_hmap_self_con_summer_tes_to_pv.png')
#evaluationHP.plot_heatmap_self_sufficiency_tes_to_pv(eva, scenario, controlled='LinCh_FID', save_fig_dir=save_fig_dir + 'LinChFID_hmap_self_suff_summer_tes_to_pv.png')
#evaluationHP.plot_heatmap_curtailed_pv_tes_to_pv(eva, scenario, controlled='LinCh_FID', save_fig_dir=save_fig_dir +     'LinChFID_hmap_curtailed_pv_summer_tes_to_pv.png')
#evaluationHP.plot_heatmap_mean_trafo_load_tes_to_pv(eva, scenario, controlled='LinCh_FID', save_fig_dir= save_fig_dir + 'LinChFID_hmap_trafo_load_summer_tes_to_pv.png')
#evaluationHP.plot_heatmap_max_line_load_tes_to_pv(eva, scenario, controlled='LinCh_FID', save_fig_dir=save_fig_dir + 'LinChFID_hmap_max_line_load_summer_tes_to_pv.png')

#evaluationHP.plot_heatmap_self_consumption_tes_to_pv(eva, scenario, controlled='Resi_Load', save_fig_dir=save_fig_dir + 'Resiload_hmap_self_con_summer_tes_to_pv.png')
#evaluationHP.plot_heatmap_self_sufficiency_tes_to_pv(eva, scenario, controlled='Resi_Load', save_fig_dir=save_fig_dir + 'Resiload_hmap_self_suff_summer_tes_to_pv.png')
#evaluationHP.plot_heatmap_curtailed_pv_tes_to_pv(eva, scenario, controlled='Resi_Load', save_fig_dir=save_fig_dir +     'Resiload_hmap_curtailed_pv_summer_tes_to_pv.png')
#evaluationHP.plot_heatmap_mean_trafo_load_tes_to_pv(eva, scenario, controlled='Resi_Load', save_fig_dir= save_fig_dir + 'Resiload_hmap_trafo_load_summer_tes_to_pv.png')
#evaluationHP.plot_heatmap_max_line_load_tes_to_pv(eva, scenario, controlled='Resi_Load', save_fig_dir=save_fig_dir + 'Resiload_hmap_max_line_load_summer_tes_to_pv.png')


#eva = load_scenario_data(scenario, seasons=['spring'])
#evaluationHP.plot_heatmap_self_sufficiency_tes_to_pv(eva, scenario, controlled='LinCh_FID', save_fig_dir=save_fig_dir + 'LinChFID_hmap_self_suff_spring_tes_to_pv.png')
#evaluationHP.plot_heatmap_curtailed_pv_tes_to_pv(eva, scenario, controlled='LinCh_FID', save_fig_dir=save_fig_dir +     'LinChFID_hmap_curtailed_pv_spring_tes_to_pv.png')
#evaluationHP.plot_heatmap_self_sufficiency_tes_to_pv(eva, scenario, controlled='Resi_Load', save_fig_dir=save_fig_dir + 'Resiload_hmap_self_suff_spring_tes_to_pv.png')
#evaluationHP.plot_heatmap_curtailed_pv_tes_to_pv(eva, scenario, controlled='Resi_Load', save_fig_dir=save_fig_dir +     'Resiload_hmap_curtailed_pv_spring_tes_to_pv.png')

#eva = load_scenario_data(scenario, seasons=['spring', 'autumn', 'winter'])
#evaluationHP.plot_heatmap_self_sufficiency_tes_to_pv(eva, scenario, controlled='LinCh_FID', save_fig_dir=save_fig_dir + 'LinChFID_hmap_self_suff_heat_period_tes_to_pv.png')
#evaluationHP.plot_heatmap_curtailed_pv_tes_to_pv(eva, scenario, controlled='LinCh_FID', save_fig_dir=save_fig_dir +     'LinChFID_hmap_curtailed_pv_heat_period_tes_to_pv.png')
#evaluationHP.plot_heatmap_self_sufficiency_tes_to_pv(eva, scenario, controlled='Resi_Load', save_fig_dir=save_fig_dir + 'Resiload_hmap_self_suff_heat_period_tes_to_pv.png')
#evaluationHP.plot_heatmap_curtailed_pv_tes_to_pv(eva, scenario, controlled='Resi_Load', save_fig_dir=save_fig_dir +     'Resiload_hmap_curtailed_pv_heat_period_tes_to_pv.png')
