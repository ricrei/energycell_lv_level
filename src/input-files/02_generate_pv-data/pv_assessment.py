import pandas as pd
import datetime
import matplotlib.pyplot as plt

def read_pv_data(filename):
    pv = pd.read_csv(filename, low_memory=False)
    #pv = pd.set_index(pd.to_datetime(pv['TIMESTAMP']))
    return pv

def print_pv_info(pv_assess):
    print('')
    print('Minimum Power: '+'south: '+str(round(pv_assess.south.min(),2))+' kW'+'\t\teast: '+str(round(pv_assess.east.min(),2))+' kW'+'\t\twest: '+str(round(pv_assess.west.min(),2))+' kW')
    print('Maximum Power: '+'south: '+str(round(pv_assess.south.max(),2))+' kW'+'\t\teast: '+str(round(pv_assess.east.max(),2))+' kW'+'\t\twest: '+str(round(pv_assess.west.max(),2))+' kW')
    print('Energy yield: '+'south: '+str(round(pv_assess.south.sum()/60,2))+' kWh'+'\teast: '+str(round(pv_assess.east.sum()/60,2))+' kWh'+'\twest: '+str(round(pv_assess.west.sum()/60,2))+' kWh')
    print('')

pv = pd.read_csv('pv_ac_power.csv', low_memory=False)
#pv = pv.set_index('TIMESTAMP')
'''
pv_assess = {'south' : [pv.south.min(), pv.south.max(), pv.south.sum()/60],
             'west' : [pv.west.min(), pv.west.max(), pv.west.sum()/60],
             'east' : [pv.east.min(), pv.east.max(), pv.east.sum()/60]
             }

print_pv_info(pv)
'''
#print(pv)
#plt.plot(pv['south'])
#plt.show()

pv_assess = pd.DataFrame(columns=['min','max','sum'])
pv_assess['min'] = pv.min()
pv_assess['max'] = pv.max()
pv_assess['sum'].loc['90'] = pv['90'].sum()/60
pv_assess['sum'].loc['100'] = pv['100'].sum()/60
pv_assess['sum'].loc['110'] = pv['110'].sum()/60
pv_assess['sum'].loc['120'] = pv['120'].sum()/60
pv_assess['sum'].loc['130'] = pv['130'].sum()/60
pv_assess['sum'].loc['140'] = pv['140'].sum()/60
pv_assess['sum'].loc['150'] = pv['150'].sum()/60
pv_assess['sum'].loc['160'] = pv['160'].sum()/60
pv_assess['sum'].loc['170'] = pv['170'].sum()/60
pv_assess['sum'].loc['180'] = pv['180'].sum()/60
pv_assess['sum'].loc['190'] = pv['190'].sum()/60
pv_assess['sum'].loc['200'] = pv['200'].sum()/60
pv_assess['sum'].loc['210'] = pv['210'].sum()/60
pv_assess['sum'].loc['220'] = pv['220'].sum()/60
pv_assess['sum'].loc['230'] = pv['230'].sum()/60
pv_assess['sum'].loc['240'] = pv['240'].sum()/60
pv_assess['sum'].loc['250'] = pv['250'].sum()/60
pv_assess['sum'].loc['260'] = pv['260'].sum()/60
print(pv_assess)

'''
print(' ')
print('Minimum value:')
print(pv.min())
print('Maximum value:')
print(pv.max())
print('Sum:')
print('90          ' + str(pv['90'].sum()/60))
print('110         ' + str(pv['110'].sum()/60))
print('120         ' + str(pv['120'].sum()/60))
print('130         ' + str(pv['130'].sum()/60))
print('140         ' + str(pv['140'].sum()/60))
print('150         ' + str(pv['150'].sum()/60))
print('160         ' + str(pv['160'].sum()/60))
print('170         ' + str(pv['170'].sum()/60))
print('180         ' + str(pv['180'].sum()/60))
print('190         ' + str(pv['190'].sum()/60))
print('200         ' + str(pv['200'].sum()/60))
print('210         ' + str(pv['210'].sum()/60))
print('220         ' + str(pv['220'].sum()/60))
print('230         ' + str(pv['230'].sum()/60))
print('240         ' + str(pv['240'].sum()/60))
print('250         ' + str(pv['250'].sum()/60))
print('260         ' + str(pv['260'].sum()/60))
print(' ')
'''
