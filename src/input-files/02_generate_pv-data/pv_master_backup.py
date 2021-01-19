import pandas as pd
import tools
import matplotlib.pyplot as plt

# define timezone
tz = 'Europe/Berlin'

# Date and Time range should match with the weather data timestemp
times = pd.date_range(start='2017-01-01 00:01:00', end='2018', freq='1min', tz=tz)

# latitude, longitude, name, altitude, timezone
coordinates = {'latitude': 52.5123, 'longitude': 13.3280, 'altitude': 56, 'timezone': tz}

# define PV-System
module, inverter, temperature_model_parameters = tools.define_pv_system()
system = {'module': module, 'inverter': inverter, \
		  'surface_azimuth': [90,180,270], 'surface_tilt': 30, \
		  'orientation': ['east','south','west']}

# specify constant ambient air temp and wind for simplicity ; temp_air = 20
wind_speed = 1  # NOTC

# calculate position of the sun
solpos = tools.get_position_off_the_sun(coordinates, times)

ac = pd.DataFrame(columns=system['orientation'])

for i,j in zip(system['surface_azimuth'],system['orientation']):
    sys = system
    sys['surface_azimuth'] = i
    # calculate i_glob_tilt, i_dir_tilt, i_diff_tilt
    i_glob_tilt, i_dir_tilt, i_diff_tilt, t_a = tools.calculate_i_glob_tilt(sys, solpos, times, print_info=False)

    # calculate AC-Power in kW normalized to 1kWp
    ac[j] = tools.get_ac_power(solpos, coordinates, sys, i_glob_tilt, i_dir_tilt, i_diff_tilt, t_a, wind_speed, temperature_model_parameters)

print(ac.round(4))
ac.to_csv('pv_ac_power.csv', mode='w', index=True, index_label='TIMESTAMP', header=system['orientation'])
#ac.plot()
#plt.show()
