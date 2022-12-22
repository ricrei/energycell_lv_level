energycosts_income = { # Euro / MWh
  'C_market_fit'    : 30,
  'C_market_obtain' : 400,	# Dez 22, https://www.bdew.de/service/daten-und-grafiken/bdew-strompreisanalyse/
  'C_flex_LV'       : 100,
  'C_flex_self'     : 30,
  'C_cur_load'      : 0,
  'C_cur_pv'        : 10,
}

investment_costs = {
  'intrest_rate'    : .05,    # aktuelle Regulierungsperiode Eigenkapitalzinssatz
  'battery_HH'      : 500,    # in Euro/kWh   # HBSS
  'battery_CBSS'     : 300,    # in Euro/kWh   # CBSS
  'battery_lifespan': 20,     # years
  'pv'              : 800,    # in Euro/kW
  'pv_lifespan'     : 30,     # years
  'tes'             : 150,    # in Euro/kWh	  # prüfen
  'tes_lifespan'    : 20,     # years	      # prüfen
  'smart_grid'      : 0,      # in Euro		  # prüfen
  'smart_grid_lifespan' : 20, # years		  # prüfen
  'grid_lifespan'   : 30,     # years
}

operating_costs = {
  'percent' : .02,            # in %/100 of the investmentcosts
}

