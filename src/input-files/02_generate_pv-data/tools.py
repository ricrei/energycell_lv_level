import pandas as pd
import pvlib
import bz2
import pickle
import _pickle as cPickle

def read_weather_data(file_name, error_replacement_value, times):
    data = pd.read_csv(file_name, header=16, low_memory=False)
    data = data.drop([0, 1]).reset_index().drop(columns='index')
    #data['TIMESTAMP'] = pd.to_datetime(data['TIMESTAMP'], format="%Y-%m-%d %H:%M:%S")
    data['timestamp'] = times
    col_name = list(data)
    data[col_name[1]] = pd.to_numeric(data[col_name[1]])
    data.loc[data[col_name[1]] == -999.000, col_name[1]] = error_replacement_value
    data = data.set_index('timestamp')
    return data

# Pickle a file and then compress it into a file with extension 
def compress_pickle(title, data):
    with bz2.BZ2File(title + '.pbz2', 'w') as f: 
     cPickle.dump(data, f)

def get_position_off_the_sun(coordinates, naive_times):
    # calculate position of the sun
    #times = naive_times.tz_localize(coordinates['timezone'])
    #print(times)
    solpos = pvlib.solarposition.get_solarposition(naive_times, coordinates['latitude'], coordinates['longitude'])

    return solpos


def print_i_info(system, i_dir_hor, i_diff_hor, i_dir_tilt, i_diff_tilt, i_glob_hor, i_glob_tilt):
    print('')
    print('Surface Azimuth: ' + str(system['surface_azimuth']) + '°')
    print('Surface Tilt: ' + str(system['surface_tilt']) + '°')
    print('')
    print('dir_hor: ' + str(i_dir_hor.rsdsdir.sum() / 60) + ' W/m^2')
    print('dir_tilt: ' + str(i_dir_tilt.dir_tilt.sum() / 60) + ' W/m^2')
    print('')
    print('diff_hor: ' + str(i_diff_hor.rsdsdiff.sum() / 60) + ' W/m^2')
    print('diff_tilt: ' + str(i_diff_tilt.diff_tilt.sum() / 60) + ' W/m^2')
    print('')
    print('glob_hor: ' + str(i_glob_hor.rsds.sum() / 60) + ' W/m^2')
    print('glob_tilt: ' + str(i_glob_tilt.glob_tilt.sum() / 60) + ' W/m^2')
    print('')


def calculate_i_glob_tilt(system, solpos, times, print_info):
    # read global irradiation, diffus irradiation, ambient temperature all in horizontal surface
    i_glob_hor = read_weather_data(
        'Wetterdaten_TUB_2017/UCON_TUB_Main_Building_minute_lev2_rsds_56.00m_20170101-20180101.csv', 0, times)
    i_diff_hor = read_weather_data(
        'Wetterdaten_TUB_2017/UCON_TUB_Main_Building_minute_lev2_rsdsdiff_56.00m_20170101-20180101.csv', 0, times)
    t_a = read_weather_data('Wetterdaten_TUB_2017/UCON_TUB_Main_Building_minute_lev2_ta_56.00m_20170101-20180101.csv',
                            20, times)

    # if i_glob_hor < i_diff_hor than i_diff_hor = i_glob_hor
    i_diff_hor.loc[i_glob_hor['rsds'] < i_diff_hor['rsdsdiff'], 'rsdsdiff'] = i_glob_hor['rsds']

    # i_dir = i_glob - i_diff
    i_dir_hor = pd.DataFrame({'rsdsdir': i_glob_hor['rsds'] - i_diff_hor['rsdsdiff']})

    # calculate the direct irradiation on tilt surface
    ratio = pvlib.irradiance.poa_horizontal_ratio(system['surface_tilt'], system['surface_azimuth'],
                                                  solpos['apparent_zenith'], solpos['azimuth'])

    # TO BE CHECKED
    # small angles and small measuring errors in irradiation lead to huge errors
    i_dir_hor.loc[solpos['apparent_zenith'] >= 86.0, 'rsdsdir'] = 0
    ratio.loc[ratio < 0] = 0  # Irradiation from behind the tilt surface should be ignored
    ratio.loc[ratio > 3] = 3  # Angles in morning and evening hours lead to huge ratios

    # todo: i_dir_tilt exceed for small angles
    # calculate irradiation on tilt surface
    i_dir_tilt = i_dir_hor.rsdsdir * ratio

    # todo: kluchermodel doesn't fit for surface_tilt = 0°
    # calculate i_diff on tilted surface with kluchermodel
    i_diff_tilt = pvlib.irradiance.klucher(system['surface_tilt'], system['surface_azimuth'], i_diff_hor['rsdsdiff'],
                                           i_glob_hor['rsds'], solpos['apparent_zenith'], solpos['azimuth'])

    i_glob_tilt = pd.DataFrame({'glob_tilt': i_dir_tilt + i_diff_tilt})
    i_dir_tilt = pd.DataFrame({'dir_tilt': i_dir_tilt})
    i_diff_tilt = pd.DataFrame({'diff_tilt': i_diff_tilt})
    t_a = pd.DataFrame({'ta': t_a.ta})

    if print_info:
        print_i_info(system, i_dir_hor, i_diff_hor, i_dir_tilt, i_diff_tilt, i_glob_hor, i_glob_tilt)

    return i_glob_tilt, i_dir_tilt, i_diff_tilt, t_a


def define_pv_system():  # todo: use latest modules
    # get the module and inverter specifications from SAM
    sandia_modules = pvlib.pvsystem.retrieve_sam('SandiaMod')
    # sandia_modules = pvlib.pvsystem.retrieve_sam('CECMod', path='CECModulesQCells.csv')
    sapm_inverters = pvlib.pvsystem.retrieve_sam('cecinverter')
    module = sandia_modules['Canadian_Solar_CS5P_220M___2009_']
    # module = sandia_modules['Hanwha_Q_CELLS_Q.PEAK_G4.1/SC_300']
    inverter = sapm_inverters['ABB__MICRO_0_25_I_OUTD_US_208__208V_']
    temperature_model_parameters = pvlib.temperature.TEMPERATURE_MODEL_PARAMETERS['sapm'][
        'insulated_back_glass_polymer']
    return module, inverter, temperature_model_parameters


def get_ac_power(solpos, coordinates, system, i_glob_tilt, i_dir_tilt, i_diff_tilt, t_a, wind_speed,
                 temperature_model_parameters):
    airmass = pvlib.atmosphere.get_relative_airmass(solpos['apparent_zenith'])
    pressure = pvlib.atmosphere.alt2pres(coordinates['altitude'])
    am_abs = pvlib.atmosphere.get_absolute_airmass(airmass, pressure)
    # calculate the angle of irradiation between position of the sun and tilte surface
    aoi = pvlib.irradiance.aoi(system['surface_tilt'], system['surface_azimuth'], solpos['apparent_zenith'],
                               solpos['azimuth'])
    effective_irradiance = pvlib.pvsystem.sapm_effective_irradiance(i_dir_tilt.dir_tilt, i_diff_tilt.diff_tilt, am_abs,
                                                                    aoi, system['module'])
    tcell = pvlib.temperature.sapm_cell(i_glob_tilt.glob_tilt, t_a.ta, wind_speed, **temperature_model_parameters)

    dc = pvlib.pvsystem.sapm(effective_irradiance, tcell, system['module'])
    ac = pvlib.pvsystem.snlinverter(dc['v_mp'], dc['p_mp'], system['inverter'])
    ac.loc[ac<0] = 0
    ac = ac/(system['module']['Impo']*system['module']['Vmpo'])
    #ac = round(ac, 4)

    return ac
