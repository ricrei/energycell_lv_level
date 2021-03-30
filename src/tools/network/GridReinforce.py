import pandapower as pp
import pandapower.networks as pn
import simbench as sb

class GridReinforce:

  def __init__(self, grid, output_dir_worst_case):
    self.grid = grid
    self.output_dir_worst_case = output_dir_worst_case
    

  def run_worst_case(self):
    pass
