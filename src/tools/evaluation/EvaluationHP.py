import sys
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import matplotlib as mpl
import numpy as np
import pandapower.plotting.plotly as ppply
import seaborn as sns
from datetime import datetime, timedelta

# Handle date time conversions between pandas and matplotlib
from pandas.plotting import register_matplotlib_converters
register_matplotlib_converters()

SMALL_SIZE = 8
MEDIUM_SIZE = 10
BIGGER_SIZE = 12

plt.rc('font', size=MEDIUM_SIZE)          # controls default text sizes
plt.rc('axes', titlesize=MEDIUM_SIZE)     # fontsize of the axes title
plt.rc('axes', labelsize=MEDIUM_SIZE)    # fontsize of the x and y labels
plt.rc('xtick', labelsize=MEDIUM_SIZE)    # fontsize of the tick labels
plt.rc('ytick', labelsize=MEDIUM_SIZE)    # fontsize of the tick labels
plt.rc('legend', fontsize=MEDIUM_SIZE)    # legend fontsize
plt.rc('figure', titlesize=BIGGER_SIZE)  # fontsize of the figure title

# Latex font
mpl.rcParams['mathtext.fontset'] = 'stix'
mpl.rcParams['font.family'] = 'STIXGeneral'

fig_x, fig_y = 5., 2.

image_format = 'png'
dpi = 500

lan = 'DE' # 'EN', 'DE'

if lan == 'DE':
  y_ticklabels = ['Land- \nnetz 1', 'Land- \nnetz 2', 'Land- \nnetz 3', 'Vorstadt-\nnetz 1  ', 'Vorstadt-\nnetz 2  ']
elif lan == 'EN':
  #y_ticklabels = ['Grid  \nRural 1', 'Grid  \nRural 2', 'Grid  \nRural 3', 'Grid    \nSuburb 1', 'Grid    \nSuburb 2']
  y_ticklabels = ['Rural 1', 'Rural 2', 'Rural 3', 'Suburb 1', 'Suburb 2']

### Helper Methods ###
def shorted_data(data, t_freq):
    data_shorted = data.resample(t_freq).mean()
    data_shorted = data_shorted.round(4)
    data_shorted.index = pd.DatetimeIndex(data_shorted.index, tz=None, ambiguous='infer')

    return data_shorted

### Calculate Output Data ###

def calculate_outputdata(eva , scenarios, grid, save_fig_dir=None):

  for index in eva:
   if grid in index:
    if 'spring' in index:
      power_spring = eva[index]['power']
      curtailed_power_spring = eva[index]['curtailed_power']
      power_spring['load_sum'] = power_spring.load + power_spring.hp + power_spring.ev + curtailed_power_spring.load
      power_spring['pv'] += curtailed_power_spring.pv
    if 'summer' in index:
      power_summer = eva[index]['power']
      curtailed_power_summer = eva[index]['curtailed_power']
      power_summer['load_sum'] = power_summer.load + power_summer.hp + power_summer.ev + curtailed_power_summer.load
      power_summer['pv'] += curtailed_power_summer.pv
    if 'autumn' in index:
      power_autumn = eva[index]['power']
      curtailed_power_autumn = eva[index]['curtailed_power']
      power_autumn['load_sum'] = power_autumn.load + power_autumn.hp + power_autumn.ev + curtailed_power_autumn.load
      power_autumn['pv'] += curtailed_power_autumn.pv
    if 'winter' in index:
      power_winter = eva[index]['power']
      curtailed_power_winter = eva[index]['curtailed_power']
      power_winter['load_sum'] = power_winter.load + power_winter.hp + power_winter.ev + curtailed_power_winter.load
      power_winter['pv'] += curtailed_power_winter.pv

  power = (power_spring.reset_index(drop=True) + power_summer.reset_index(drop=True) + power_autumn.reset_index(drop=True) + power_winter.reset_index(drop=True)).sum()/60
  power['load_sum'] = power.load + power.hp + power.ev
  print(' ')
  print('Grid:       ' + str(grid))
  print('PV Power:   ' + str(power.pv))
  print('Load Power: ' + str(power.load_sum))
  print('PV/Load')
  print(' year     : ' + str(power.pv/power.load_sum))
  print(' summer   : ' + str(power_summer.sum().pv/power_summer.sum().load_sum))
  print(' winter   : ' + str(power_winter.sum().pv/power_winter.sum().load_sum))

def plot_heatmap_self_consumption_tes_to_pv(eva, scenario, controlled, save_fig_dir=None):
  pvs = ['PV_kein', 'PV_mittel', 'PV_groß']
  tes = ['noBC+TES1', 'noBC+TES2', 'BC+TES1', 'BC+TES2']
  
  interp_sfh = {'A' : 'SFH15', 'B' : 'SFH45', 'C' : 'SFH100'}
  interp_pv  = {'0' : pvs[0], \
                '3' : pvs[1], \
                '1' : pvs[2]}
  
  if(controlled is 'Resi_Load'):
    interp_tes = {'2' : tes[0], \
                  '3' : tes[1], \
                  '4' : tes[2], \
                  '5' : tes[3]}
  
  if(controlled is 'LinCh_FID'):
    interp_tes = {'6' : tes[0], \
                  '7' : tes[1], \
                  '8' : tes[2], \
                  '9' : tes[3]}
  
  df_sfh15 = pd.DataFrame(index=[pvs], columns=tes).fillna(0)
  df_sfh45 = pd.DataFrame(index=[pvs], columns=tes).fillna(0)
  df_sfh100 = pd.DataFrame(index=[pvs], columns=tes).fillna(0)
  
  #############################
  ### Define dict SFHs names ###
  df_sfhs = {'SFH15'  : df_sfh15  ,  \
             'SFH45'  : df_sfh45  ,  \
             'SFH100' : df_sfh100 
             }
  ############################

  conclude_seasons = {}
  ## conclude all relevant values of all seasons to one df in one dict
  for index_eva in eva:
    if eva[index_eva]['scenario'] not in conclude_seasons :
      #if first iteration create dataframe
      conclude_seasons[eva[index_eva]['scenario']] = \
        pd.DataFrame({'pv_gen' : eva[index_eva]['power']['pv'] , \
                      'curt_pv' : eva[index_eva]['curtailed_power']['pv'] , \
                      'trafo_p' : eva[index_eva]['trafo_p']['0'] })
    else :
      #else append the data to dataframe
      conclude_seasons[eva[index_eva]['scenario']] = \
        conclude_seasons[eva[index_eva]['scenario']].append(pd.DataFrame({ \
                      'pv_gen' : eva[index_eva]['power']['pv'] ,\
                      'curt_pv' : eva[index_eva]['curtailed_power']['pv'] ,\
                      'trafo_p' : eva[index_eva]['trafo_p']['0'] }) )

  ## calculate and create tables for heatmap
  for index_eva in eva:
    ##calculate self_suff
    sum_curt_pv = conclude_seasons[eva[index_eva]['scenario']]['curt_pv'].sum()
    sum_pv_gen = conclude_seasons[eva[index_eva]['scenario']]['pv_gen'].sum()
    resi_trafo = -1 * conclude_seasons[eva[index_eva]['scenario']]['trafo_p']
    resi_trafo_pos = resi_trafo[resi_trafo > 0]
    
    if sum_pv_gen > 0 :
      self_con = ((sum_pv_gen + sum_curt_pv - resi_trafo_pos.sum() - sum_curt_pv) / (sum_pv_gen + sum_curt_pv)) * 100
      #self_con = ((sum_pv_gen - resi_trafo_pos.sum()) / (sum_pv_gen)) * 100
    else : 
      self_con = 0
    if self_con < 0 :
      self_con = 0
    
    ## fill table of correct building-type
    # iterate through rows (index_pv) in final table
    for index_pv in interp_pv:
      # iterate through columns (index_tes) in final table
      for index_tes in interp_tes:
        #avoid access to tes which are not in the focus of "controlled" (Resi_Load or LinCh_FID)
        if index_tes in eva[index_eva]['scenario'][3]:
          df_sfhs[interp_sfh[eva[index_eva]['scenario'][0]]].at[interp_pv[str(eva[index_eva]['scenario'][1])] \
                             , interp_tes[str(eva[index_eva]['scenario'][3])]] = self_con

  vmax = 100
  vmin = 0
  
  if lan == 'EN':
    x_ticklabels = tes
  elif lan == 'DE':
      x_ticklabels = tes

  fig, axes = plt.subplots(3, 1, figsize=(4.3, 4))
  sns.heatmap(data=df_sfh15, vmax = vmax, vmin = vmin, cmap="rocket_r", annot=True, square=False, fmt=".0f", ax=axes[0], cbar=False, linewidth=.5)
  sns.heatmap(data=df_sfh45, vmax = vmax, vmin = vmin, cmap="rocket_r", annot=True, square=False, fmt=".0f", ax=axes[1], cbar=False, linewidth=.5)
  sns.heatmap(data=df_sfh100, vmax = vmax, vmin = vmin, cmap="rocket_r", annot=True, square=False, fmt=".0f", ax=axes[2], cbar=False, linewidth=.5)
  fig.suptitle(controlled + ' - Eigenverbrauchsgrad in %')
  #axes[0].set_title('Eigenverbrauchsgrad SFH15 in %')
  axes[0].set(ylabel='SFH15', xlabel='')
  #axes[1].set_title('Eigenverbrauchsgrad SFH45  in %')
  axes[1].set(ylabel='SFH45', xlabel='')
  #axes[2].set_title('Eigenverbrauchsgrad SFH100 in %')
  axes[2].set(ylabel='SFH100', xlabel='')
  fig.tight_layout()
  
  if save_fig_dir is not None:
     plt.savefig(save_fig_dir, bbox_inches='tight', dpi=dpi)

def plot_heatmap_self_sufficiency_tes_to_pv(eva, scenario, controlled, save_fig_dir=None):
  pvs = ['PV_kein', 'PV_mittel', 'PV_groß']
  tes = ['noBC+TES1', 'noBC+TES2', 'BC+TES1', 'BC+TES2']
  
  interp_sfh = {'A' : 'SFH15', 'B' : 'SFH45', 'C' : 'SFH100'}
  interp_pv  = {'0' : pvs[0], \
                '3' : pvs[1], \
                '1' : pvs[2]}

  if(controlled is 'Resi_Load'):
    interp_tes = {'2' : tes[0], \
                  '3' : tes[1], \
                  '4' : tes[2], \
                  '5' : tes[3]}
  
  if(controlled is 'LinCh_FID'):
    interp_tes = {'6' : tes[0], \
                  '7' : tes[1], \
                  '8' : tes[2], \
                  '9' : tes[3]}
  
  df_sfh15 = pd.DataFrame(index=[pvs], columns=tes).fillna(0)
  df_sfh45 = pd.DataFrame(index=[pvs], columns=tes).fillna(0)
  df_sfh100 = pd.DataFrame(index=[pvs], columns=tes).fillna(0)

  ## Define dict SFHs names ###
  df_sfhs = {'SFH15'  : df_sfh15  ,  \
             'SFH45'  : df_sfh45 ,   \
             'SFH100' : df_sfh100 
             }
  
  conclude_seasons = {}
  ## conclude all relevant values of all seasons to one df in one dict
  for index_eva in eva:
    if eva[index_eva]['scenario'] not in conclude_seasons :
      #if first iteration create dataframe
      conclude_seasons[eva[index_eva]['scenario']] = \
        pd.DataFrame({'hh_load' : eva[index_eva]['power']['load'] ,\
                      'hp_load' : eva[index_eva]['power']['hp'] ,\
                      'ev_load' : eva[index_eva]['power']['ev'] , \
                      'losses' : eva[index_eva]['losses']['trafo'] , \
                      'trafo_p' : eva[index_eva]['trafo_p']['0'] })
    else :
      #else append the data to dataframe
      conclude_seasons[eva[index_eva]['scenario']] = \
        conclude_seasons[eva[index_eva]['scenario']].append(pd.DataFrame({ \
                      'hh_load' : eva[index_eva]['power']['load'] ,\
                      'hp_load' : eva[index_eva]['power']['hp'] ,\
                      'ev_load' : eva[index_eva]['power']['ev'] , \
                      'losses' : eva[index_eva]['losses']['trafo'] , \
                      'trafo_p' : eva[index_eva]['trafo_p']['0'] }) )

  ## calculate and create tables for heatmap
  for index_eva in eva:
    ##calculate self_suff
    sum_losses = conclude_seasons[eva[index_eva]['scenario']]['losses'].sum()
    sum_load = conclude_seasons[eva[index_eva]['scenario']]['hh_load'].sum() \
              + conclude_seasons[eva[index_eva]['scenario']]['hp_load'].sum() \
              + conclude_seasons[eva[index_eva]['scenario']]['ev_load'].sum()
    resi_trafo = -1 * conclude_seasons[eva[index_eva]['scenario']]['trafo_p']
    resi_trafo_neg = resi_trafo[resi_trafo < 0]

    self_suff = ((sum_load + sum_losses + resi_trafo_neg.sum()) / (sum_load + sum_losses)) * 100

    ## fill table of correct building-type
    # iterate through rows (index_pv) in final table
    for index_pv in interp_pv:
      # iterate through columns (index_tes) in final table
      for index_tes in interp_tes:
        #avoid access to tes which are not in the focus of "controlled" (Resi_Load or LinCh_FID)
        if index_tes in eva[index_eva]['scenario'][3]:
          #avoid slightly negative values due to inaccuracies
          if self_suff > 0 : 
            df_sfhs[interp_sfh[eva[index_eva]['scenario'][0]]].at[interp_pv[str(eva[index_eva]['scenario'][1])] \
                               , interp_tes[str(eva[index_eva]['scenario'][3])]] = self_suff
          else :
            df_sfhs[interp_sfh[eva[index_eva]['scenario'][0]]].at[interp_pv[str(eva[index_eva]['scenario'][1])] \
                               , interp_tes[str(eva[index_eva]['scenario'][3])]] = 0
  vmax = 100
  vmin = 0
  
  if lan == 'EN':
    x_ticklabels = tes
  elif lan == 'DE':
      x_ticklabels = tes

  fig, axes = plt.subplots(3, 1, figsize=(4.3, 4))
  sns.heatmap(data=df_sfh15, vmax = vmax, vmin = vmin, cmap="rocket_r", annot=True, square=False, fmt=".0f", ax=axes[0], cbar=False, linewidth=.5)
  sns.heatmap(data=df_sfh45, vmax = vmax, vmin = vmin, cmap="rocket_r", annot=True, square=False, fmt=".0f", ax=axes[1], cbar=False, linewidth=.5)
  sns.heatmap(data=df_sfh100, vmax = vmax, vmin = vmin, cmap="rocket_r", annot=True, square=False, fmt=".0f", ax=axes[2], cbar=False, linewidth=.5)
  fig.suptitle(controlled + ' Autarkiegrad in %')
  #axes[0].set_title('Autarkiegrad SFH15 in %')
  axes[0].set(ylabel='SFH15', xlabel='')
  #axes[1].set_title('Autarkiegrad SFH45  in %')
  axes[1].set(ylabel='SFH45', xlabel='')
  #axes[2].set_title('Autarkiegrad SFH100 in %')
  axes[2].set(ylabel='SFH100', xlabel='')
  fig.tight_layout()
  
  if save_fig_dir is not None:
     plt.savefig(save_fig_dir, bbox_inches='tight', dpi=dpi)

def plot_heatmap_curtailed_pv_tes_to_pv(eva, scenario, controlled, save_fig_dir=None):
  pvs = ['PV_kein', 'PV_mittel', 'PV_groß']
  tes = ['noBC+TES1', 'noBC+TES2', 'BC+TES1', 'BC+TES2']
  
  interp_sfh = {'A' : 'SFH15', 'B' : 'SFH45', 'C' : 'SFH100'}
  interp_pv  = {'0' : pvs[0], \
                '3' : pvs[1], \
                '1' : pvs[2]}
    
  if(controlled is 'Resi_Load'):
    interp_tes = {'2' : tes[0], \
                  '3' : tes[1], \
                  '4' : tes[2], \
                  '5' : tes[3]}
  
  if(controlled is 'LinCh_FID'):
    interp_tes = {'6' : tes[0], \
                  '7' : tes[1], \
                  '8' : tes[2], \
                  '9' : tes[3]}
        
  df_sfh15 = pd.DataFrame(index=[pvs], columns=tes).fillna(0)
  df_sfh45 = pd.DataFrame(index=[pvs], columns=tes).fillna(0)
  df_sfh100 = pd.DataFrame(index=[pvs], columns=tes).fillna(0)

  ## Define dict SFHs names ###
  df_sfhs = {'SFH15'  : df_sfh15  ,  \
             'SFH45'  : df_sfh45 ,   \
             'SFH100' : df_sfh100 
             }
  
  conclude_seasons = {}
  ## conclude all relevant values of all seasons to one df in one dict
  for index_eva in eva:
    if eva[index_eva]['scenario'] not in conclude_seasons :
      conclude_seasons[eva[index_eva]['scenario']] = \
        pd.DataFrame({'load' : eva[index_eva]['curtailed_power']['load'] ,\
                      'pv_curt' : eva[index_eva]['curtailed_power']['pv'] , \
                      'pv_gen' : eva[index_eva]['power']['pv']  })
    else :
      conclude_seasons[eva[index_eva]['scenario']] = \
        conclude_seasons[eva[index_eva]['scenario']].append(pd.DataFrame({ \
                      'load' : eva[index_eva]['curtailed_power']['load'], \
                      'pv_curt' : eva[index_eva]['curtailed_power']['pv'] , \
                      'pv_gen' : eva[index_eva]['power']['pv'] }) )
 
  ## fill tables for heatmap
  for index_eva in eva:
    pv_gen_sum = conclude_seasons[eva[index_eva]['scenario']]['pv_gen'].sum()
    pv_curt_sum = conclude_seasons[eva[index_eva]['scenario']]['pv_curt'].sum()
    
    if pv_gen_sum > 0 :
      curtail_pv = pv_curt_sum / (pv_curt_sum + pv_gen_sum) * 100
    else :
      curtail_pv = 0
    
    ## fill table of correct building-type
    # iterate through rows (index_pv) in final table
    for index_pv in interp_pv:
      # iterate through columns (index_tes) in final table
      for index_tes in interp_tes:
        #avoid access to tes which are not in the focus of "controlled" (Resi_Load or LinCh_FID)
        if index_tes in eva[index_eva]['scenario'][3]:
          df_sfhs[interp_sfh[eva[index_eva]['scenario'][0]]].at[interp_pv[str(eva[index_eva]['scenario'][1])] \
                               , interp_tes[str(eva[index_eva]['scenario'][3])]] = curtail_pv

  vmax = 100
  vmin = 0
  
  if lan == 'EN':
    x_ticklabels = tes
  elif lan == 'DE':
      x_ticklabels = tes

  fig, axes = plt.subplots(3, 1, figsize=(4.3, 4))
  sns.heatmap(data=df_sfh15, vmax = vmax, vmin = vmin, cmap="rocket_r", annot=True, square=False, fmt=".0f", ax=axes[0], cbar=False, linewidth=.5)
  sns.heatmap(data=df_sfh45, vmax = vmax, vmin = vmin, cmap="rocket_r", annot=True, square=False, fmt=".0f", ax=axes[1], cbar=False, linewidth=.5)
  sns.heatmap(data=df_sfh100, vmax = vmax, vmin = vmin, cmap="rocket_r", annot=True, square=False, fmt=".0f", ax=axes[2], cbar=False, linewidth=.5)
  fig.suptitle(controlled + ' abgeregelte PV-Erzeugung in %')
  #axes[0].set_title('Abgeregelte PV SFH15 in %')
  axes[0].set(ylabel='SFH15', xlabel='')
  #axes[1].set_title('Abgeregelte PV SFH45 in %')
  axes[1].set(ylabel='SFH45', xlabel='')
  #axes[2].set_title('Abgeregelte PV SFH100 in %')
  axes[2].set(ylabel='SFH100', xlabel='')
  fig.tight_layout()
  
  if save_fig_dir is not None:
     plt.savefig(save_fig_dir, bbox_inches='tight', dpi=dpi)

def plot_heatmap_curtailed_load_tes_to_pv(eva, scenario, controlled, save_fig_dir=None):
  pvs = ['PV_kein', 'PV_mittel', 'PV_groß']
  tes = ['noBC+TES1', 'noBC+TES2', 'BC+TES1', 'BC+TES2']
  
  interp_sfh = {'A' : 'SFH15', 'B' : 'SFH45', 'C' : 'SFH100'}
  interp_pv  = {'0' : pvs[0], \
                '3' : pvs[1], \
                '1' : pvs[2]}

  if(controlled is 'Resi_Load'):
    interp_tes = {'2' : tes[0], \
                  '3' : tes[1], \
                  '4' : tes[2], \
                  '5' : tes[3]}
  
  if(controlled is 'LinCh_FID'):
    interp_tes = {'6' : tes[0], \
                  '7' : tes[1], \
                  '8' : tes[2], \
                  '9' : tes[3]}
        
  df_sfh15 = pd.DataFrame(index=[pvs], columns=tes).fillna(0)
  df_sfh45 = pd.DataFrame(index=[pvs], columns=tes).fillna(0)
  df_sfh100 = pd.DataFrame(index=[pvs], columns=tes).fillna(0)

  ## Define dict SFHs names ###
  df_sfhs = {'SFH15'  : df_sfh15  ,  \
             'SFH45'  : df_sfh45 ,   \
             'SFH100' : df_sfh100 
             }

  conclude_seasons = {}
  ## conclude all relevant values of all seasons to one df in one dict
  for index_eva in eva:
    if eva[index_eva]['scenario'] not in conclude_seasons :
      #if first iteration create dataframe
      conclude_seasons[eva[index_eva]['scenario']] = \
        pd.DataFrame({'hh_load' : eva[index_eva]['power']['load'] ,\
                      'hp_load' : eva[index_eva]['power']['hp'] ,\
                      'ev_load' : eva[index_eva]['power']['ev'] , \
                      'load_curt' : eva[index_eva]['curtailed_power']['load'] })
    else :
      #else append the data to dataframe
      conclude_seasons[eva[index_eva]['scenario']] = \
        conclude_seasons[eva[index_eva]['scenario']].append(pd.DataFrame({ \
                      'hh_load' : eva[index_eva]['power']['load'] ,\
                      'hp_load' : eva[index_eva]['power']['hp'] ,\
                      'ev_load' : eva[index_eva]['power']['ev'] , \
                      'load_curt' : eva[index_eva]['curtailed_power']['load'] }) )

  ## calculate and create tables for heatmap
  for index_eva in eva:
    ##calculate self_suff
    sum_load = conclude_seasons[eva[index_eva]['scenario']]['hh_load'].sum() \
              + conclude_seasons[eva[index_eva]['scenario']]['hp_load'].sum() \
              + conclude_seasons[eva[index_eva]['scenario']]['ev_load'].sum()
    load_curt_sum = conclude_seasons[eva[index_eva]['scenario']]['load_curt'].sum()
    
    curt_load = load_curt_sum / (sum_load + load_curt_sum) * 100
    
    ## fill table of correct building-type
    # iterate through rows (index_pv) in final table
    for index_pv in interp_pv:
      # iterate through columns (index_tes) in final table
      for index_tes in interp_tes:
        if index_tes in eva[index_eva]['scenario'][3]:
          #avoid slightly negative values due to inaccuracies
          if curt_load > 0 : 
            df_sfhs[interp_sfh[eva[index_eva]['scenario'][0]]].at[interp_pv[str(eva[index_eva]['scenario'][1])] \
                               , interp_tes[str(eva[index_eva]['scenario'][3])]] = curt_load
          else :
            df_sfhs[interp_sfh[eva[index_eva]['scenario'][0]]].at[interp_pv[str(eva[index_eva]['scenario'][1])] \
                               , interp_tes[str(eva[index_eva]['scenario'][3])]] = 0
            
  vmax = 100
  vmin = 0
  
  if lan == 'EN':
    x_ticklabels = tes
  elif lan == 'DE':
      x_ticklabels = tes

  fig, axes = plt.subplots(3, 1, figsize=(4.3, 4))
  sns.heatmap(data=df_sfh15, vmax = vmax, vmin = vmin, cmap="rocket_r", annot=True, square=False, fmt=".1f", ax=axes[0], cbar=False, linewidth=.5)
  sns.heatmap(data=df_sfh45, vmax = vmax, vmin = vmin, cmap="rocket_r", annot=True, square=False, fmt=".1f", ax=axes[1], cbar=False, linewidth=.5)
  sns.heatmap(data=df_sfh100, vmax = vmax, vmin = vmin, cmap="rocket_r", annot=True, square=False, fmt=".1f", ax=axes[2], cbar=False, linewidth=.5)
  fig.suptitle(controlled + ' abgeregelte Last in %')
  axes[0].set(ylabel='SFH15', xlabel='')
  #axes[1].set_title('Abgeregelte Last SFH45 in %')
  axes[1].set(ylabel='SFH45', xlabel='')
  #axes[2].set_title('Abgeregelte Last SFH100 in %')
  axes[2].set(ylabel='SFH100', xlabel='')
  fig.tight_layout()
  
  if save_fig_dir is not None:
     plt.savefig(save_fig_dir, bbox_inches='tight', dpi=dpi)

def plot_heatmap_mean_trafo_load_tes_to_pv(eva, scenario, controlled, save_fig_dir=None):
  pvs = ['PV_kein', 'PV_mittel', 'PV_groß']
  tes = ['noBC+TES1', 'noBC+TES2', 'BC+TES1', 'BC+TES2']
  
  interp_sfh = {'A' : 'SFH15', 'B' : 'SFH45', 'C' : 'SFH100'}
  interp_pv  = {'0' : pvs[0], \
                '3' : pvs[1], \
                '1' : pvs[2]}
    
  if(controlled is 'Resi_Load'):
    interp_tes = {'2' : tes[0], \
                  '3' : tes[1], \
                  '4' : tes[2], \
                  '5' : tes[3]}
  
  if(controlled is 'LinCh_FID'):
    interp_tes = {'6' : tes[0], \
                  '7' : tes[1], \
                  '8' : tes[2], \
                  '9' : tes[3]}
  
  evaluation_criteria = 'tl'     #trafo_load
  
  df_sfh15 = pd.DataFrame(index=[pvs], columns=tes).fillna(0)
  df_sfh45 = pd.DataFrame(index=[pvs], columns=tes).fillna(0)
  df_sfh100 = pd.DataFrame(index=[pvs], columns=tes).fillna(0)

  ## Define dict SFHs names ###
  df_sfhs = {'SFH15'  : df_sfh15  ,  \
             'SFH45'  : df_sfh45 ,   \
             'SFH100' : df_sfh100 
             }
  
  conclude_seasons = {}
  ## conclude all relevant values of all seasons to one df
  for index_eva in eva:
    if eva[index_eva]['scenario'] not in conclude_seasons :
      conclude_seasons[eva[index_eva]['scenario']] = \
        eva[index_eva][evaluation_criteria]['0']
    else :
      conclude_seasons[eva[index_eva]['scenario']] = \
        conclude_seasons[eva[index_eva]['scenario']].append(eva[index_eva][evaluation_criteria]['0'])
  
  ## fill tables for heatmap
  for index_eva in eva:
    for index_pv in interp_pv:
      for index_tes in interp_tes:
        if index_tes in eva[index_eva]['scenario'][3]:
          if 'A' in eva[index_eva]['scenario']:
            df_sfh15.at[interp_pv[str(eva[index_eva]['scenario'][1])] \
                         , interp_tes[str(eva[index_eva]['scenario'][3])]] \
                          = conclude_seasons[eva[index_eva]['scenario']].mean()
          
          if 'B' in eva[index_eva]['scenario']:
            df_sfh45.at[interp_pv[str(eva[index_eva]['scenario'][1])] \
                         , interp_tes[str(eva[index_eva]['scenario'][3])]] \
                          = conclude_seasons[eva[index_eva]['scenario']].mean()
          
          if 'C' in eva[index_eva]['scenario']:
            df_sfh100.at[interp_pv[str(eva[index_eva]['scenario'][1])] \
                         , interp_tes[str(eva[index_eva]['scenario'][3])]] \
                          = conclude_seasons[eva[index_eva]['scenario']].mean()
  
  vmax = 100
  vmin = 0
  
  if lan == 'EN':
    x_ticklabels = tes
  elif lan == 'DE':
      x_ticklabels = tes
  
  fig, axes = plt.subplots(3, 1, figsize=(4.3, 4))
  sns.heatmap(data=df_sfh15, vmax = vmax, vmin = vmin, cmap="rocket_r", annot=True, square=False, fmt=".0f", ax=axes[0], cbar=False, linewidth=.5)
  sns.heatmap(data=df_sfh45, vmax = vmax, vmin = vmin, cmap="rocket_r", annot=True, square=False, fmt=".0f", ax=axes[1], cbar=False, linewidth=.5)
  sns.heatmap(data=df_sfh100, vmax = vmax, vmin = vmin, cmap="rocket_r", annot=True, square=False, fmt=".0f", ax=axes[2], cbar=False, linewidth=.5)
  fig.suptitle(controlled + ' mittlere Trafo_Last in %')
  #axes[0].set_title('mittlere Trafo_Last SFH15 in %')
  axes[0].set(ylabel='SFH15', xlabel='')
  #axes[1].set_title('mittlere Trafo_Last SFH45 in %')
  axes[1].set(ylabel='SFH45', xlabel='')
  #axes[2].set_title('mittlere Trafo_Last SFH100 in %')
  axes[2].set(ylabel='SFH100', xlabel='')
  fig.tight_layout()
  
  if save_fig_dir is not None:
     plt.savefig(save_fig_dir, bbox_inches='tight', dpi=dpi)
        
def plot_heatmap_min_voltage_tes_to_pv(eva, scenario, controlled, save_fig_dir=None):
  
  pvs = ['PV_kein', 'PV_mittel', 'PV_groß']
  tes = ['noBC+TES1', 'noBC+TES2', 'BC+TES1', 'BC+TES2']
  
  interp_sfh = {'A' : 'SFH15', 'B' : 'SFH45', 'C' : 'SFH100'}
  interp_pv  = {'0' : pvs[0], \
                '3' : pvs[1], \
                '1' : pvs[2]}
  
  if(controlled is 'Resi_Load'):
    interp_tes = {'2' : tes[0], \
                  '3' : tes[1], \
                  '4' : tes[2], \
                  '5' : tes[3]}
  
  if(controlled is 'LinCh_FID'):
    interp_tes = {'6' : tes[0], \
                  '7' : tes[1], \
                  '8' : tes[2], \
                  '9' : tes[3]}
  
  evaluation_criteria = 'v'     #trafo_load
  
  df_sfh15 = pd.DataFrame(index=[pvs], columns=tes).fillna(0)
  df_sfh45 = pd.DataFrame(index=[pvs], columns=tes).fillna(0)
  df_sfh100 = pd.DataFrame(index=[pvs], columns=tes).fillna(0)

  ## Define dict SFHs names ###
  df_sfhs = {'SFH15'  : df_sfh15  ,  \
             'SFH45'  : df_sfh45 ,   \
             'SFH100' : df_sfh100 
             }
  
  conclude_seasons = {}
  ## conclude all relevant values of all seasons to one df
  for index_eva in eva:
    if eva[index_eva]['scenario'] not in conclude_seasons :
      conclude_seasons[eva[index_eva]['scenario']] = \
        eva[index_eva][evaluation_criteria]
    else :
      conclude_seasons[eva[index_eva]['scenario']] = \
        conclude_seasons[eva[index_eva]['scenario']].append(eva[index_eva][evaluation_criteria])
  
  ## fill tables for heatmap
  for index_eva in eva:
    for index_pv in interp_pv:
      for index_tes in interp_tes:
        if index_tes in eva[index_eva]['scenario'][3]:
          if 'A' in eva[index_eva]['scenario']:
            df_sfh15.at[interp_pv[str(eva[index_eva]['scenario'][1])] \
                         , interp_tes[str(eva[index_eva]['scenario'][3])]] \
                          = conclude_seasons[eva[index_eva]['scenario']].min().min()
          
          if 'B' in eva[index_eva]['scenario']:
            df_sfh45.at[interp_pv[str(eva[index_eva]['scenario'][1])] \
                         , interp_tes[str(eva[index_eva]['scenario'][3])]] \
                          = conclude_seasons[eva[index_eva]['scenario']].min().min()
          
          if 'C' in eva[index_eva]['scenario']:
            df_sfh100.at[interp_pv[str(eva[index_eva]['scenario'][1])] \
                         , interp_tes[str(eva[index_eva]['scenario'][3])]] \
                          = conclude_seasons[eva[index_eva]['scenario']].min().min()
  
  vmax = 1.1
  vmin = 0.9
  
  if lan == 'EN':
    x_ticklabels = tes
  elif lan == 'DE':
      x_ticklabels = tes
  
  fig, axes = plt.subplots(3, 1, figsize=(4.3, 4))
  sns.heatmap(data=df_sfh15, vmax = vmax, vmin = vmin, cmap="rocket_r", annot=True, square=False, fmt=".2f", ax=axes[0], cbar=False, linewidth=.5)
  sns.heatmap(data=df_sfh45, vmax = vmax, vmin = vmin, cmap="rocket_r", annot=True, square=False, fmt=".2f", ax=axes[1], cbar=False, linewidth=.5)
  sns.heatmap(data=df_sfh100, vmax = vmax, vmin = vmin, cmap="rocket_r", annot=True, square=False, fmt=".2f", ax=axes[2], cbar=False, linewidth=.5)
  fig.suptitle(controlled + ' min. Leitungsspannung in p.u.')
  #axes[0].set_title('min Leitungsspannung SFH15 in p.u.')
  axes[0].set(ylabel='SFH15', xlabel='')
  #axes[1].set_title('min Leitungsspannung SFH45 in p.u.')
  axes[1].set(ylabel='SFH45', xlabel='')
  #axes[2].set_title('min Leitungsspannung SFH100 in p.u.')
  axes[2].set(ylabel='SFH100', xlabel='')
  fig.tight_layout()
  
  if save_fig_dir is not None:
     plt.savefig(save_fig_dir, bbox_inches='tight', dpi=dpi)

def plot_heatmap_max_voltage_tes_to_pv(eva, scenario, controlled, save_fig_dir=None):
  
  pvs = ['PV_kein', 'PV_mittel', 'PV_groß']
  tes = ['noBC+TES1', 'noBC+TES2', 'BC+TES1', 'BC+TES2']
  
  interp_sfh = {'A' : 'SFH15', 'B' : 'SFH45', 'C' : 'SFH100'}
  interp_pv  = {'0' : pvs[0], \
                '3' : pvs[1], \
                '1' : pvs[2]}
  
  if(controlled is 'Resi_Load'):
    interp_tes = {'2' : tes[0], \
                  '3' : tes[1], \
                  '4' : tes[2], \
                  '5' : tes[3]}
  
  if(controlled is 'LinCh_FID'):
    interp_tes = {'6' : tes[0], \
                  '7' : tes[1], \
                  '8' : tes[2], \
                  '9' : tes[3]}
  
  evaluation_criteria = 'v'     #trafo_load
  
  df_sfh15 = pd.DataFrame(index=[pvs], columns=tes).fillna(0)
  df_sfh45 = pd.DataFrame(index=[pvs], columns=tes).fillna(0)
  df_sfh100 = pd.DataFrame(index=[pvs], columns=tes).fillna(0)

  ## Define dict SFHs names ###
  df_sfhs = {'SFH15'  : df_sfh15  ,  \
             'SFH45'  : df_sfh45 ,   \
             'SFH100' : df_sfh100 
             }
  
  conclude_seasons = {}
  ## conclude all relevant values of all seasons to one df
  for index_eva in eva:
    if eva[index_eva]['scenario'] not in conclude_seasons :
      conclude_seasons[eva[index_eva]['scenario']] = \
        eva[index_eva][evaluation_criteria]
    else :
      conclude_seasons[eva[index_eva]['scenario']] = \
        conclude_seasons[eva[index_eva]['scenario']].append(eva[index_eva][evaluation_criteria])
  
  ## fill tables for heatmap
  for index_eva in eva:
    for index_pv in interp_pv:
      for index_tes in interp_tes:
        if index_tes in eva[index_eva]['scenario'][3]:
          if 'A' in eva[index_eva]['scenario']:
            df_sfh15.at[interp_pv[str(eva[index_eva]['scenario'][1])] \
                         , interp_tes[str(eva[index_eva]['scenario'][3])]] \
                          = conclude_seasons[eva[index_eva]['scenario']].max().max()
          
          if 'B' in eva[index_eva]['scenario']:
            df_sfh45.at[interp_pv[str(eva[index_eva]['scenario'][1])] \
                         , interp_tes[str(eva[index_eva]['scenario'][3])]] \
                          = conclude_seasons[eva[index_eva]['scenario']].max().max()
          
          if 'C' in eva[index_eva]['scenario']:
            df_sfh100.at[interp_pv[str(eva[index_eva]['scenario'][1])] \
                         , interp_tes[str(eva[index_eva]['scenario'][3])]] \
                          = conclude_seasons[eva[index_eva]['scenario']].max().max()
  
  vmax = 1.1
  vmin = 0.9
  
  if lan == 'EN':
    x_ticklabels = tes
  elif lan == 'DE':
      x_ticklabels = tes
  
  fig, axes = plt.subplots(3, 1, figsize=(4.3, 4))
  sns.heatmap(data=df_sfh15, vmax = vmax, vmin = vmin, cmap="rocket_r", annot=True, square=False, fmt=".2f", ax=axes[0], cbar=False, linewidth=.5)
  sns.heatmap(data=df_sfh45, vmax = vmax, vmin = vmin, cmap="rocket_r", annot=True, square=False, fmt=".2f", ax=axes[1], cbar=False, linewidth=.5)
  sns.heatmap(data=df_sfh100, vmax = vmax, vmin = vmin, cmap="rocket_r", annot=True, square=False, fmt=".2f", ax=axes[2], cbar=False, linewidth=.5)
  fig.suptitle(controlled + ' max. Leitungsspannung in p.u.')
  #axes[0].set_title('max Leitungsspannung SFH15 in p.u.')
  axes[0].set(ylabel='SFH15', xlabel='')
  #axes[1].set_title('max Leitungsspannung SFH45 in p.u.')
  axes[1].set(ylabel='SFH45', xlabel='')
  #axes[2].set_title('max Leitungsspannung SFH100 in p.u.')
  axes[2].set(ylabel='SFH100', xlabel='')
  fig.tight_layout()
  
  if save_fig_dir is not None:
     plt.savefig(save_fig_dir, bbox_inches='tight', dpi=dpi)

def plot_heatmap_max_line_load_tes_to_pv(eva, scenario, controlled, save_fig_dir=None):
  
  pvs = ['PV_kein', 'PV_mittel', 'PV_groß']
  tes = ['noBC+TES1', 'noBC+TES2', 'BC+TES1', 'BC+TES2']
  
  interp_sfh = {'A' : 'SFH15', 'B' : 'SFH45', 'C' : 'SFH100'}
  interp_pv  = {'0' : pvs[0], \
                '3' : pvs[1], \
                '1' : pvs[2]}
  
  if(controlled is 'Resi_Load'):
    interp_tes = {'2' : tes[0], \
                  '3' : tes[1], \
                  '4' : tes[2], \
                  '5' : tes[3]}
  
  if(controlled is 'LinCh_FID'):
    interp_tes = {'6' : tes[0], \
                  '7' : tes[1], \
                  '8' : tes[2], \
                  '9' : tes[3]}
    
  evaluation_criteria = 'll'     #trafo_load
  
  df_sfh15 = pd.DataFrame(index=[pvs], columns=tes).fillna(0)
  df_sfh45 = pd.DataFrame(index=[pvs], columns=tes).fillna(0)
  df_sfh100 = pd.DataFrame(index=[pvs], columns=tes).fillna(0)

  ## Define dict SFHs names ###
  df_sfhs = {'SFH15'  : df_sfh15  ,  \
             'SFH45'  : df_sfh45 ,   \
             'SFH100' : df_sfh100 
             }
  
  conclude_seasons = {}
  ## conclude all relevant values of all seasons to one df
  for index_eva in eva:
    if eva[index_eva]['scenario'] not in conclude_seasons :
      conclude_seasons[eva[index_eva]['scenario']] = \
        eva[index_eva][evaluation_criteria]
    else :
      conclude_seasons[eva[index_eva]['scenario']] = \
        conclude_seasons[eva[index_eva]['scenario']].append(eva[index_eva][evaluation_criteria])
  
  ## fill tables for heatmap
  for index_eva in eva:
    for index_pv in interp_pv:
      for index_tes in interp_tes:
        if index_tes in eva[index_eva]['scenario'][3]:
          if 'A' in eva[index_eva]['scenario']:
            df_sfh15.at[interp_pv[str(eva[index_eva]['scenario'][1])] \
                         , interp_tes[str(eva[index_eva]['scenario'][3])]] \
                          = conclude_seasons[eva[index_eva]['scenario']].max().max()
          
          if 'B' in eva[index_eva]['scenario']:
            df_sfh45.at[interp_pv[str(eva[index_eva]['scenario'][1])] \
                         , interp_tes[str(eva[index_eva]['scenario'][3])]] \
                          = conclude_seasons[eva[index_eva]['scenario']].max().max()
            
          
          if 'C' in eva[index_eva]['scenario']:
            df_sfh100.at[interp_pv[str(eva[index_eva]['scenario'][1])] \
                         , interp_tes[str(eva[index_eva]['scenario'][3])]] \
                          = conclude_seasons[eva[index_eva]['scenario']].max().max()

  vmax = 100
  vmin = 0
  
  if lan == 'EN':
    x_ticklabels = tes
  elif lan == 'DE':
      x_ticklabels = tes
  
  fig, axes = plt.subplots(3, 1, figsize=(4.3, 4))
  sns.heatmap(data=df_sfh15, vmax = vmax, vmin = vmin, cmap="rocket_r", annot=True, square=False, fmt=".0f", ax=axes[0], cbar=False, linewidth=.5)
  sns.heatmap(data=df_sfh45, vmax = vmax, vmin = vmin, cmap="rocket_r", annot=True, square=False, fmt=".0f", ax=axes[1], cbar=False, linewidth=.5)
  sns.heatmap(data=df_sfh100, vmax = vmax, vmin = vmin, cmap="rocket_r", annot=True, square=False, fmt=".0f", ax=axes[2], cbar=False, linewidth=.5)
  fig.suptitle(controlled + ' max. Leitungsbelastung in %')
  #axes[0].set_title('max. Leitungsbelastung SFH15 in %')
  axes[0].set(ylabel='SFH15', xlabel='')
  #axes[1].set_title('max. Leitungsbelastung SFH45 in %')
  axes[1].set(ylabel='SFH45', xlabel='')
  #axes[2].set_title('max. Leitungsbelastung SFH100 in %')
  axes[2].set(ylabel='SFH100', xlabel='')
  fig.tight_layout()
  
  if save_fig_dir is not None:
     plt.savefig(save_fig_dir, bbox_inches='tight', dpi=dpi)


def plot_heatmap_sum_el_demand_hp_tes_to_pv(eva, scenario, controlled, save_fig_dir=None):
  
  pvs = ['PV_kein', 'PV_mittel', 'PV_groß']
  tes = ['noBC+TES1', 'noBC+TES2', 'BC+TES1', 'BC+TES2']
  
  interp_sfh = {'A' : 'SFH15', 'B' : 'SFH45', 'C' : 'SFH100'}
  interp_pv  = {'0' : pvs[0], \
                '3' : pvs[1], \
                '1' : pvs[2]}
  
  if(controlled is 'Resi_Load'):
    interp_tes = {'2' : tes[0], \
                  '3' : tes[1], \
                  '4' : tes[2], \
                  '5' : tes[3]}
  
  if(controlled is 'LinCh_FID'):
    interp_tes = {'6' : tes[0], \
                  '7' : tes[1], \
                  '8' : tes[2], \
                  '9' : tes[3]}
    
  evaluation_criteria = 'll'     #trafo_load
  
  df_sfh15 = pd.DataFrame(index=[pvs], columns=tes).fillna(0)
  df_sfh45 = pd.DataFrame(index=[pvs], columns=tes).fillna(0)
  df_sfh100 = pd.DataFrame(index=[pvs], columns=tes).fillna(0)

  ## Define dict SFHs names ###
  df_sfhs = {'SFH15'  : df_sfh15  ,  \
             'SFH45'  : df_sfh45 ,   \
             'SFH100' : df_sfh100 
             }

  conclude_seasons = {}
  ## conclude all relevant values of all seasons to one df
  for index_eva in eva:
    if eva[index_eva]['scenario'] not in conclude_seasons :
      conclude_seasons[eva[index_eva]['scenario']] = \
        eva[index_eva]['power']['hp']
    else :
      conclude_seasons[eva[index_eva]['scenario']] = \
        conclude_seasons[eva[index_eva]['scenario']].append(eva[index_eva]['power']['hp'])
  
  ## fill tables for heatmap
  for index_eva in eva:
    for index_pv in interp_pv:
      for index_tes in interp_tes:
        if index_tes in eva[index_eva]['scenario'][3]:
          if 'A' in eva[index_eva]['scenario']:
            df_sfh15.at[interp_pv[str(eva[index_eva]['scenario'][1])] \
                         , interp_tes[str(eva[index_eva]['scenario'][3])]] \
                          = conclude_seasons[eva[index_eva]['scenario']].sum()
          
          if 'B' in eva[index_eva]['scenario']:
            df_sfh45.at[interp_pv[str(eva[index_eva]['scenario'][1])] \
                         , interp_tes[str(eva[index_eva]['scenario'][3])]] \
                          = conclude_seasons[eva[index_eva]['scenario']].sum()
            
          
          if 'C' in eva[index_eva]['scenario']:
            df_sfh100.at[interp_pv[str(eva[index_eva]['scenario'][1])] \
                         , interp_tes[str(eva[index_eva]['scenario'][3])]] \
                          = conclude_seasons[eva[index_eva]['scenario']].sum()

  vmax = 100
  vmin = 0
  
  if lan == 'EN':
    x_ticklabels = tes
  elif lan == 'DE':
      x_ticklabels = tes
  
  fig, axes = plt.subplots(3, 1, figsize=(4.3, 4))
  sns.heatmap(data=df_sfh15, vmax = vmax, vmin = vmin, cmap="rocket_r", annot=True, square=False, fmt=".0f", ax=axes[0], cbar=False, linewidth=.5)
  sns.heatmap(data=df_sfh45, vmax = vmax, vmin = vmin, cmap="rocket_r", annot=True, square=False, fmt=".0f", ax=axes[1], cbar=False, linewidth=.5)
  sns.heatmap(data=df_sfh100, vmax = vmax, vmin = vmin, cmap="rocket_r", annot=True, square=False, fmt=".0f", ax=axes[2], cbar=False, linewidth=.5)
  fig.suptitle(controlled + ' Summe el. Bezug Wärmepumpe')
  #axes[0].set_title('max. Leitungsbelastung SFH15 in %')
  axes[0].set(ylabel='SFH15', xlabel='')
  #axes[1].set_title('max. Leitungsbelastung SFH45 in %')
  axes[1].set(ylabel='SFH45', xlabel='')
  #axes[2].set_title('max. Leitungsbelastung SFH100 in %')
  axes[2].set(ylabel='SFH100', xlabel='')
  fig.tight_layout()
  
  if save_fig_dir is not None:
     plt.savefig(save_fig_dir, bbox_inches='tight', dpi=dpi)





