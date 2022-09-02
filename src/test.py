import matplotlib.pyplot as plt
import matplotlib.patches as mpatches


# 8133310
# winter, spring, summer, autumn
c = {
  'total' :              [28.25, 21.85, 13.75, 17],
  'self_consumed' :      [27, 53, 37, 50],
  'self_consumed_flex' : [0 , 14, 49, 11],
  'p2p' :                [6 , 22,  6, 27],
  'p2p_flex' :           [0 ,  2,  9,  1],
  'mv' :                 [67,  8,  0, 11],
  'curtailed' :          [0 ,  0,  0,  0],
}

g = {
  'total' :              [9.46, 25.54, 101.27, 18.53],
  'self_consumed' :      [78, 58, 12, 56],
  'self_consumed_flex' : [2 ,  0,  0,  0],
  'p2p' :                [16, 22,  3, 26],
  'p2p_flex' :           [1 ,  0,  0,  0],
  'mv' :                 [2 , 20, 24, 17],
  'curtailed' :          [0 ,  0, 62,  2],
}

c_year = {}
c_year['total'] = sum(c['total'])
c_year['self_consumed'] = sum([x*y/100 for (x,y) in zip(c['total'], c['self_consumed'])])/sum(c['total'])*100
c_year['self_consumed_flex'] = sum([x*y/100 for (x,y) in zip(c['total'], c['self_consumed_flex'])])/sum(c['total'])*100
c_year['p2p'] = sum([x*y/100 for (x,y) in zip(c['total'], c['p2p'])])/sum(c['total'])*100
c_year['p2p_flex'] = sum([x*y/100 for (x,y) in zip(c['total'], c['p2p_flex'])])/sum(c['total'])*100
c_year['mv'] = sum([x*y/100 for (x,y) in zip(c['total'], c['mv'])])/sum(c['total'])*100
c_year['curtailed'] = sum([x*y/100 for (x,y) in zip(c['total'], c['curtailed'])])/sum(c['total'])*100

g_year = {}
g_year['total'] = sum(g['total'])
g_year['self_consumed'] = sum([x*y/100 for (x,y) in zip(g['total'], g['self_consumed'])])/sum(g['total'])*100
g_year['self_consumed_flex'] = sum([x*y/100 for (x,y) in zip(g['total'], g['self_consumed_flex'])])/sum(g['total'])*100
g_year['p2p'] = sum([x*y/100 for (x,y) in zip(g['total'], g['p2p'])])/sum(g['total'])*100
g_year['p2p_flex'] = sum([x*y/100 for (x,y) in zip(g['total'], g['p2p_flex'])])/sum(g['total'])*100
g_year['mv'] = sum([x*y/100 for (x,y) in zip(g['total'], g['mv'])])/sum(g['total'])*100
g_year['curtailed'] = sum([x*y/100 for (x,y) in zip(g['total'], g['curtailed'])])/sum(g['total'])*100

print(c_year)
print(g_year)
#Aus Durchlauf: time_scope_year = { 'start_time' : '2017-01-01 00:00:00+01:00', 'end_time'   : '2018-01-01 00:00:00+01:00', 't_freq'     : '1H'}
#consumption
#43, 17, 14, 2, 24, 0
#generation
#26, 0, 8, 0, 25, 41

'''
fig, ax = plt.subplots()
ax.plot(c['self_consumed'], label='self_consumed')
ax.plot(c['self_consumed_flex'], label='self_consumed_flex')
ax.plot(c['p2p'], label='p2p')
ax.plot(c['p2p_flex'], label='p2p_flex')
ax.plot(c['mv'], label='mv')
ax.plot(c['curtailed'], label='curtailed')
ax.legend()

fig, ax = plt.subplots()
ax.plot(g['self_consumed'], label='self_consumed')
ax.plot(g['self_consumed_flex'], label='self_consumed_flex')
ax.plot(g['p2p'], label='p2p')
ax.plot(g['p2p_flex'], label='p2p_flex')
ax.plot(g['mv'], label='mv')
ax.plot(g['curtailed'], label='curtailed')
ax.legend()

plt.show()
'''
