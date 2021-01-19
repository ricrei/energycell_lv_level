from oem2orm import oep_oedialect_oem2orm as oem2orm
import os
import pandas as pd
import getpass

import json
import requests

oem2orm.setup_logger()

# Use individual token from OEP
os.environ["OEP_TOKEN"] = getpass.getpass('Token:')
#eca106d4564a5233e501cae70c2513ba07b8a5cc

db = oem2orm.setup_db_connection()
# Ricardo_Reibsch

metadata_folder = oem2orm.select_oem_dir(oem_folder_name="metadata")

tables_orm = oem2orm.collect_tables_from_oem(db, metadata_folder)

#create table
oem2orm.create_tables(db, tables_orm)

# In order to actually delete, you will need to type: yes
#oem2orm.delete_tables(db, tables_orm)
#Please confirm with either of the choices below:
#- yes
#- no
#- the indexes to drop in the format 0, 2, 3, 5
#Please type the choice completely as there is no default choice.


## Upload dataset active power ##
filepath_p = "load_p_sorted.csv"
df_p = pd.read_csv(filepath_p, encoding='utf8', sep=',')

# show the first 10 row´s
df_p[:10]

filepath_q = "load_q_sorted.csv"
df_q = pd.read_csv(filepath_q, encoding='utf8', sep=',')

# show the first 10 row´s
df_q[:10]

schema = "model_draft"
table_name_p = "energycell_load_active_power_v01"
table_name_q = "energycell_load_reactive_power_v01"
connection = db.engine

try: 
    df_p.to_sql(table_name_p, connection, schema=schema, if_exists='append', index=False)
    print('Inserted data to ' + schema + '.' + table_name)
except Exception as e:
    print('Writing to ' + table_name + ' failed!')
    print('Note that you cannot load the same data into the table twice. There will be an id conflict.')
    print('Delete and recreate with the commands above, if you want to test your upload again.')

try: 
    df_q.to_sql(table_name_q, connection, schema=schema, if_exists='append', index=False)
    print('Inserted data to ' + schema + '.' + table_name)
except Exception as e:
    print('Writing to ' + table_name + ' failed!')
    print('Note that you cannot load the same data into the table twice. There will be an id conflict.')
    print('Delete and recreate with the commands above, if you want to test your upload again.')







