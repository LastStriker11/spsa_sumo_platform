import os
os.chdir("../")
#%%
import pandas as pd
import numpy as np
from src.RUN_SUMO import parse_sumo_outputs
from src.miscs import config, sim_setup
#%%
# load the prior od
input_od = pd.read_csv(config["NETWORK"] / sim_setup["prior_od"], sep='\s+', header=None, skiprows=5)
input_od.iloc[:, 2] = input_od.iloc[:, 2] + 5

sim_setup['start_sim_sec'] =  sim_setup["starttime"]*3600 - 500
sim_setup['end_sim_sec']   =  sim_setup["endtime"]*3600 + 500
df_simulated = parse_sumo_outputs(config, sim_setup, input_od)

df_simulated.to_csv(config["NETWORK"] / "true_data.csv", index=True)
#%%
np.random.seed(11)
x = 1.2
y = np.random.normal(0.15, 0.333, size=len(input_od))
input_od.iloc[:, 2] = input_od.iloc[:, 2]*(x+y)
input_od.iloc[:, 2] = input_od.iloc[:, 2].astype(int)

head_text = (f"$OR;D2 \n* From-Time  To-Time \n{sim_setup['starttime']}.00 {sim_setup['endtime']}.00\n* Factor \n1.00\n")
file_name = config["NETWORK"] / "start_od.txt"
file = open(file_name, "w")
file.write(head_text)
file.close()
input_od.to_csv(file_name, header=False, index=False, sep=" ", mode="a")

