import os
os.chdir("../")

import pandas as pd
import os
import time
import matplotlib.pyplot as plt
from src.RUN_SUMO import CallSUMOGetCounts

from src.miscs import config, sim_setup, spsa_setup

num_sim = 100

input_od = pd.read_csv(config["NETWORK"] / sim_setup["prior_od"], sep='\s+', header=None, skiprows=5)

sim_setup['start_sim_sec'] =  sim_setup["starttime"]*3600 - 500
sim_setup['end_sim_sec']   =  sim_setup["endtime"]*3600 + 500
df_simulated = CallSUMOGetCounts(config, sim_setup, input_od)
