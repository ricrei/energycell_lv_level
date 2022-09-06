energycosts_income = { # Euro / MWh
  'C_market_fit'    : 30,
  'C_market_obtain' : 300,
  'C_grid_charge'   : 50,
  'C_p2p'           : [],
  'C_flex_LV'       : 100,
  'C_flex_self'     : 20,
  'C_cur_load'      : 300,
  'C_cur_pv'        : 30,
}

investment_costs = {
  'battery' : 1000, # in Euro/kWh
}

operating_costs = {
  'percent' : .02, # in %/100 of the investmentcosts
}

annuity_factor = .05
