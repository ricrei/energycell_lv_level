import os
import csv
import time
import numpy as np
import pandas as pd
import pandapower as pp
import pandapower.networks as pn
import pandapower.toolbox as tb
import simbench as sb
import tools.progress as prog
import tools.tools as tt

import bz2
import _pickle as cPickle


class OutputDataHandler():

  def __init__(self):
    pass

  #########################
  ### create output_dir ###
  #########################
  def create_output_dir(self, net_name, scenario, time_scope):
        self.output_dir = os.path.join("./", "output-files/"+str(scenario)+"/"+str(net_name)+"/"+time_scope['start_time'][0:10]+"_"+time_scope['end_time'][0:10]+"_"+time_scope['t_freq']+"/")
        # Create output directory
        if os.path.isdir(self.output_dir):
          print("Output directory: " + str(self.output_dir))
        else:
          try:
            os.makedirs(self.output_dir)
          except OSError:
            print("Error: Creation of output directory %s failed" % self.output_dir)
          else:
            print("Create outout directory %s" % self.output_dir)
