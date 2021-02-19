import bz2
import pickle
import _pickle as cPickle
import pandas as pd


#####################################################################
### Pickle a file and then compress it into a file with extension ###
#####################################################################
def compress_pickle(title, data):
     with bz2.BZ2File(title + '.pbz2', 'w') as f: 
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

#####################                
### Read csv-file ###
#####################
def read_data(file):
     data = pd.read_csv(file, low_memory=False)
     data['timestamp'] = pd.to_datetime(data['timestamp'], utc=True)
     data = data.set_index('timestamp')
     data.index = data.index.tz_convert('Europe/Berlin')
     #data = data.drop(['timestamp'], axis=1)
     return data

####################################################
### convert csv file into compressed pickle file ###
####################################################
def csv_2_pickle(file):
      df = read_data(file)
      print(df)
      file = file[0:-4]
      compress_pickle(file, df)


file_csv = 'input-files/04_ev_load.csv'
file_pbz2 = 'input-files/04_ev_load.pbz2'
csv_2_pickle(file_csv)

df = decompress_pickle(file_pbz2)
print(df)
print(type(df.columns))

# compare datasets
df = decompress_pickle(file_pbz2)
file_pbz2_old = 'input-files/04_ev_load.pbz2'
df_old = decompress_pickle(file_pbz2_old)
print(df_old)
print(type(df_old.columns))
print(type(df.index))
print(type(df_old.index))
print(df.equals(df_old))
