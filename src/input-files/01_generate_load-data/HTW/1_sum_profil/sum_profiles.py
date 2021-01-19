import os
import numpy as np
import pandas as pd
import tempfile

def read_data(times):
    # read all profils
    p1 = pd.read_csv("../0_Data/PL1.csv", header=None)
    p2 = pd.read_csv("../0_Data/PL2.csv", header=None)
    p3 = pd.read_csv("../0_Data/PL3.csv", header=None)
    q1 = pd.read_csv("../0_Data/QL1.csv", header=None)
    q2 = pd.read_csv("../0_Data/QL2.csv", header=None)
    q3 = pd.read_csv("../0_Data/QL3.csv", header=None)
    # create new DataFrames
    p0 = pd.DataFrame()
    p0['TIMESTAMP'] = times
    q0 = pd.DataFrame()
    q0['TIMESTAMP'] = times

    # sum all phases of all profiles.
    # P0 contains the whole profile(P1+P2+P3) of each of the 74 households
    # P0_norm contains the normalized profile of the sum of all profiles
    for i in range(0, 74):
        p0[i] = p1[i] + p2[i] + p3[i]
        q0[i] = q1[i] + q2[i] + q3[i]
    p0 = p0.set_index('TIMESTAMP')
    q0 = q0.set_index('TIMESTAMP')
    return p0, q0


def normalize(p0, q0):
    p0['norm'] = 0
    q0['norm'] = 0

    for i in range(0, 74):
        p0['norm'] += p0[i]
        q0['norm'] += q0[i]

    e = p0['norm'].sum() / (60 * 1000 * 1000)
    # normalization to 1000 kWh/year
    p0['norm'] = p0['norm'] / e
    q0['norm'] = q0['norm'] / e  # normalized to P0!

    return p0['norm'], q0['norm']


# Date and Time range should match with the weather data timestemp
naive_times = pd.date_range(start='2017-01-01 00:01:00', end='2018', freq='1min')

# call read_data
p0, q0 = read_data(naive_times)
# p0_norm, q0_norm = normalize(p0, q0)

#del p0['norm']
#del q0['norm']


# export all data to csv-files
p0.to_csv("p0.csv", header = True, mode='w', index=True, index_label='TIMESTAMP',)
# p0_norm.to_csv("p0_norm.csv", index=False, header = True)
q0.to_csv("q0.csv", header = True, mode='w', index=True, index_label='TIMESTAMP',)
# q0_norm.to_csv("q0_norm.csv", index=False, header = True)
