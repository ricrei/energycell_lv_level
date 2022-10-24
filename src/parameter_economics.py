energycosts_income = { # Euro / MWh
  'C_market_fit'    : 30,
  'C_market_obtain' : 300,
  'C_flex_LV'       : 100,
  'C_flex_self'     : 30,
  'C_cur_load'      : 300,
  'C_cur_pv'        : 10,
}

investment_costs = {
  'intrest_rate'    : .0307,
  'battery'         : 500,    # in Euro/kWh   # unterscheiden in HBSS und CBSS
  'battery_lifespan': 20,     # years
  'tes'             : 100,    # in Euro/kWh	  # prüfen
  'tes_lifespan'    : 20,     # years	      # prüfen
  'smart_grid'      : 1500,   # in Euro		  # prüfen
  'smart_grid_lifespan' : 20, # years		  # prüfen
  'grid'            : 1000,
  'grid_lifespan'   : 30,     # years
}

operating_costs = {
  'percent' : .01,            # in %/100 of the investmentcosts
}

