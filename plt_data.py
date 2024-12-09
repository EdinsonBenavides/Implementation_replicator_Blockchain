import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

df1 = pd.read_csv('D:/U/udenar/Proyecto/contrato3/MQTT_pruebas/PruebaMQTT/python2/agente1/evolution_data.csv')
df2 = pd.read_csv('D:/U/udenar/Proyecto/contrato3/MQTT_pruebas/PruebaMQTT/python2/agente2/evolution_data.csv')
df3 = pd.read_csv('D:/U/udenar/Proyecto/contrato3/MQTT_pruebas/PruebaMQTT/python2/agente3/evolution_data.csv')

f1 = list(df1["Fitness"])
f2 = list(df2["Fitness"])
f3 = list(df3["Fitness"])

p1 = list(df1["Potencia"])
p2 = list(df2["Potencia"])
p3 = list(df3["Potencia"])

plt.plot(p1,label="Agente 1")
plt.plot(p2,label="Agente 2")
plt.plot(p3,label="Agente 3")
plt.title("Potencia ")
plt.legend()
plt.xlabel("Iteraacion")
plt.ylabel("Evolucion de Potencias")
plt.show()

plt.plot(f1,label="Agente 1")
plt.plot(f2,label="Agente 2")
plt.plot(f3,label="Agente 3")
plt.title("Evolución de Fitness")
plt.legend()
plt.xlabel("Iteraacion")
plt.ylabel("Fitness")
plt.show()