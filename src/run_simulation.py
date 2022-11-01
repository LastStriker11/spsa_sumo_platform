import pandas as pd
import os
import time
import matplotlib.pyplot as plt
from src.RUN_SUMO import CallSUMOGetCounts

from src.miscs import config, sim_setup, spsa_setup
#%%
num_sim = 100

input_od = pd.read_csv(config["NETWORK"] + sim_setup["prior_od"], sep='\s+', header=None, skiprows=5)