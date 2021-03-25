v = [1.1,1.2,.98,.93,1.0]

q = v*0

for i in v:
  q[i > 1] = 1
  q[i <= 1] = 0

print(q)
