import os

directory = str(os.getcwd()) + '/output-files'

seasons = [
'2017-10-20_2017-10-27_1T',
'2017-03-05_2017-03-12_1T',
'2017-05-27_2017-06-03_1T',
'2017-01-03_2017-01-10_1T',
'2017-01-01_2018-01-01_1H',
]

def walk_trough_dir(directory):
  print(directory)
  dir_list = os.listdir(directory)
  for d in dir_list:
    if os.path.isdir(directory + '/' + d):
      walk_trough_dir(directory + '/' + d)

def walk_trough_dir_2(directory):
    for (root,dirs,files) in os.walk(directory, topdown=True):
       if root[-20:] not in ['000_evaluation_dicts']:
        if root[-24:] not in seasons:
         if files != []:
          print (root)
          #print (dirs)
          #print (files)
          #print ('--------------------------------')

walk_trough_dir_2(directory)
