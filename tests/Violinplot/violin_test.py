
import seaborn as sns
import matplotlib.pyplot as plt

sns.set_theme(style="whitegrid")


tips = sns.load_dataset("tips")

#ax = sns.violinplot(x="day", y="total_bill", data=tips)

'''
flights = sns.load_dataset("flights")

print(flights)
flights = flights.pivot("month", "year", "passengers")
print(flights)
ax = sns.heatmap(flights)

plt.show()
'''
ax = sns.barplot(x="day", y="total_bill", data=tips)
plt.show()
