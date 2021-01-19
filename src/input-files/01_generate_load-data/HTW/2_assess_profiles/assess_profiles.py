import os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import bz2
import pickle
import _pickle as cPickle

#####################################################################
### Pickle a file and then compress it into a file with extension ###
#####################################################################
def compress_pickle(title, data):
     with bz2.BZ2File(title, 'w') as f: 
      cPickle.dump(data, f)
     f.close()

#######################################
### Load any compressed pickle file ###
#######################################
def decompress_pickle(file):
     f = bz2.BZ2File(file, 'rb')
     data = cPickle.load(f)
     f.close()
     return data


times = pd.date_range(start='2017-01-01 00:01:00', end='2018', freq='1T', tz='Europe/Berlin')

def read_data():
    # read all profils
    p0 = pd.read_csv("../1_sum_profil/input/p0.csv")
    q0 = pd.read_csv("../1_sum_profil/input/q0.csv")

    p0 = p0.set_index('TIMESTAMP')
    q0 = q0.set_index('TIMESTAMP')

    # convert into kW
    p0 = p0/1000
    q0 = q0/1000

    return p0, q0

# Date and Time range should match with the weather data timestemp
#naive_times = pd.date_range(start='2017-01-01 00:01:00', end='2018', freq='1min')

# call read_data
#p0, q0 = read_data()
p0 = decompress_pickle("../1_sum_profil/input/p0.pbz2")
q0 = decompress_pickle("../1_sum_profil/input/q0.pbz2")

p0 = p0.set_index(pd.to_datetime(p0['TIMESTAMP']))
q0 = q0.set_index(pd.to_datetime(q0['TIMESTAMP']))

p0 = p0.drop('TIMESTAMP',axis=1)
q0 = q0.drop('TIMESTAMP',axis=1)

p0.index.name = 'timestamp'
q0.index.name = 'timestamp'

print(p0)

# convert into kW
p0 = p0/1000
q0 = q0/1000

p0_peak = p0.max()
p0_energy = p0.sum()/60

p0_std = p0.std()

p0np = np.array(p0)
p0_33 = np.percentile(p0_energy, 33)
p0_66 = np.percentile(p0_energy, 66)
p = pd.DataFrame()
p['33'] = (p0_energy <= p0_33)
p['66'] = (p0_energy > p0_33) & (p0_energy <= p0_66)
p['100'] = (p0_energy > p0_66)

print(p)

p_low = np.array([])
p_mid = np.array([])
p_high = np.array([])

for i in range(0,74):
    if p['33'][i] == True:
        p_low = np.append(p_low,[i])
    if p['66'][i] == True:
        p_mid = np.append(p_mid, [i])
    if p['100'][i] == True:
        p_high = np.append(p_high, [i])

print(len(p_low), len(p_mid), len(p_high))

p0_sorted = pd.DataFrame()
q0_sorted = pd.DataFrame()

for i in range(0,74):
    if i%3 == 0:
        p0_sorted[str(i)] = p0[str(int(p_low[int(i / 3)]))]
        q0_sorted[str(i)] = q0[str(int(p_low[int(i / 3)]))]
    if i%3 == 1:
        if i == 73:
            p0_sorted[str(i)] = p0[str(int(p_mid[1]))]
            q0_sorted[str(i)] = q0[str(int(p_mid[1]))]
        else:
            p0_sorted[str(i)] = p0[str(int(p_mid[int((i - 1) / 3)]))]
            q0_sorted[str(i)] = q0[str(int(p_mid[int((i - 1) / 3)]))]
    if i%3 == 2:
        p0_sorted[str(i)] = p0[str(int(p_high[int((i - 2) / 3)]))]
        q0_sorted[str(i)] = q0[str(int(p_high[int((i - 2) / 3)]))]


print(p0_sorted.sum().head(13)/60)

p0_sorted.index = times
q0_sorted.index = times

p0_sorted.index.name = 'timestamp'
q0_sorted.index.name = 'timestamp'

p0_sorted.columns = 'p'+p0_sorted.columns
q0_sorted.columns = 'q'+q0_sorted.columns

print(p0_sorted)
p0_sorted = p0_sorted.round(2)
q0_sorted = q0_sorted.round(2)
print(p0_sorted)

compress_pickle('01_p0_load.pbz2', p0_sorted)
compress_pickle('01_q0_load.pbz2', q0_sorted)

#p0_sorted.to_csv('load_p_sorted.csv', mode='w', index=True, index_label='TIMESTAMP')
#q0_sorted.to_csv('load_q_sorted.csv', mode='w', index=True, index_label='TIMESTAMP')
#plt.boxplot(p0np)
#plt.plot(p0_std, p0_energy, 'ro')
#plt.xlabel('p0 std')
#plt.ylabel('p0 consumption')
#plt.boxplot(p0_energy)
#plt.show()



# export all data to csv-files
#p0.to_csv("p0.csv", header = True, mode='w', index=True, index_label='TIMESTAMP',)
# p0_norm.to_csv("p0_norm.csv", index=False, header = True)
#q0.to_csv("q0.csv", header = True, mode='w', index=True, index_label='TIMESTAMP',)
# q0_norm.to_csv("q0_norm.csv", index=False, header = True)
