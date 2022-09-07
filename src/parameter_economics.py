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
  'intrest_rate' : .0507,
  'battery' : 1000, # in Euro/kWh
  'battery_lifespan' : 15, # years
  'tes' : 1500, # in Euro/kWh				# prüfen
  'tes_lifespan' : 20, # years				# prüfen
  'smart_grid' : 1500, # in Euro			# prüfen
  'smart_grid_lifespan' : 20, # years		# prüfen
  'grid'    : 1000,
  'grid_lifespan' : 30, # years
}

operating_costs = {
  'percent' : .01, # in %/100 of the investmentcosts
}
