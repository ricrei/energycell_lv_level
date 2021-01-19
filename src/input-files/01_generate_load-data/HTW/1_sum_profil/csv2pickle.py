import pandas as pd
import bz2
#import pickle
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


p0 = pd.read_csv("input/p0.csv")
q0 = pd.read_csv("input/q0.csv")

compress_pickle("input/p0.pbz2", p0)
compress_pickle("input/q0.pbz2", q0)
