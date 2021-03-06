# -*- coding: utf-8 -*-
"""
Created on Thu Jan 23 08:56:00 2020

@author: Chae Gordon
"""

# -*- coding: utf-8 -*-

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

throttle_a = []
loss_a = []
energy_vio_a = []
resolution_hh = 30

df_2 = 2*pd.read_excel("Gigha_data_30_min.xlsx").values

# transform 48 30 min rows into a time series

power = []
for i in range(len(df_2)):
    for j in range(48):
        power.append(df_2[i,j+2])
        # the + 2 is due to the first x value being two in from the left

df = pd.DataFrame(data=power, columns=["Average Power/ kW"])
    
# want to take the 30 minute power data and interpolate into 1-minute data
    
# normalising data into fractional values of total rated power
    
power = df["Average Power/ kW"]
    
max_power = df["Average Power/ kW"].max()  # 3.6 MW

power_split = np.array_split(power.values, len(power)/24) # split into 12 hrs

power_agg = np.array([sum(i) for i in power_split]) # aggregate the 12 hours

sigma_12 = np.std(power_agg/max(power_agg))

power = df["Average Power/ kW"]/max_power

power = power.values

print(sigma_12)

loss_at_load_factor = 0

"""
Want to incorporate P&L and the powerdrive response time & workings
1)try and account for accuracy in forecast of weather (maybe add random noise)
2)talk through inner workings
"""


for i in range(31):
    throttle = 1
    sigma = i*0.01  # 0.4 needed for 10% loss !!
    interpolated = []
    
    load = throttle*np.average(power)
    
    # if 30 minute data change 10--> 30
    # energy should remain unaffected
                    
    lossy = []
    avg_line = []
    
    for i in range(len(power)-29):
        for j in range(resolution_hh):
            avg_line.append(power[i])
            # have it so random fluctuation is centred on previous point
            if j==0:
                a = power[i] + np.random.normal(loc=0,scale=sigma)
            else:
                a = interpolated[i*resolution_hh+j-1] + np.random.normal(loc=0,scale=sigma)
            if a > 0:
                if 1 > a:
                    interpolated.append(a)
                    if power[i]>load:
                        if a < load:
                            lossy.append((load-a)*(1/60))
                        else:
                            lossy.append(0)
                    if load >= power[i]:
                        if a > load:
                            lossy.append((1/60)*(a - load))
                        else:
                            lossy.append(0)
                else:
                    a=1
                    interpolated.append(a)
                    if power[i]>load:
                        if a < load:
                            lossy.append((load-a)*(1/60))
                        else:
                            lossy.append(0)
                    if load >= power[i]:
                        if a > load:
                            lossy.append((1/60)*(a - load))
                        else:
                            lossy.append(0)
                
            else:
                interpolated.append(0)
                lossy.append(0)
    
    lost_E = sum(lossy)*max_power #  kWh
    print("lost Energy: {0:.2f} kWh".format(lost_E))
    # checking energy conservation
        
    energy_interpolated = sum(interpolated)*(1/60)*max_power  # kWh
    energy_data = (1/2)*sum(power)*max_power  # kWh
    
    print("lost Energy: {0:.2f} %".format(100*lost_E/energy_data))
    print("Energy Conservation Violated by {0:.2f} %".format(100*(energy_interpolated-energy_data)/(energy_data)))
    
    throttle_a.append(sigma)
    loss_a.append(100*lost_E/energy_data)
    energy_vio_a.append(100*(energy_interpolated-energy_data)/(energy_data))
    
    if sigma == 0.03:
        power_g = power[0:3]
        interpolated_g = interpolated[0:61]  # check this
        avg_line_g = avg_line[0:61]
        
        loss_at_load_factor = 100*lost_E/energy_data  # loss when IT sized at average power
        
        plt.figure()
        plt.title("Interpolation of 1-minute Points")
        plt.plot(np.linspace(0, len(interpolated_g),num=len(interpolated_g),endpoint=False), interpolated_g, label="interpolated points")
        plt.plot(np.linspace(0, len(interpolated_g),num=len(interpolated_g),endpoint=False), avg_line_g, label="cumulative average power points")
        plt.scatter(np.linspace(0, 30*len(power_g),num=len(power_g),endpoint=False), power_g, label="inferred average power from data")
        plt.legend()
        plt.xlabel("Time Elapsed (min)")
        plt.ylabel("Power Fraction of Rated Capacity")
        #plt.savefig("interpolation_example.pdf")
        # plt.show()
        
        energy_t_interpolated = np.log((1/60)*np.cumsum(interpolated)*max_power)
        energy_t_data = np.log((1/2)*np.cumsum(power)*max_power )
        
        plt.figure()
        plt.title("Log of Cumulative Energy for Interpolated and Real Data")
        plt.ylabel(r"ln( Energy/[kWh] )")
        plt.xlabel("Time Elapsed (min)")
        plt.plot(np.linspace(0, len(energy_t_interpolated),num=len(energy_t_interpolated),endpoint=False), energy_t_interpolated)
        plt.plot(np.linspace(0, 30*len(energy_t_data),num=len(energy_t_data),endpoint=False), energy_t_data)
        #plt.savefig("energy_cons.pdf")
    else:
        pass

# zero loss when IT = 0

loss_a[0]=0

plt.figure()
plt.plot(throttle_a,loss_a)
plt.title("Percentage Energy Loss as a funciton of 1-min Variability")
plt.ylabel(r"Percentage Energy Loss (%)")
plt.xlabel("1-min Variability (% COV)")
plt.savefig("loss_sigma.pdf")

plt.figure()
plt.plot(throttle_a,energy_vio_a)
plt.title("Percentage Energy Violation as a funciton of 1-min Variability")
plt.ylabel(r"Percentage Energy Violation (%)")
plt.xlabel(r"1-min Variability (% COV)")
plt.savefig("e_cons_sigma.pdf")

