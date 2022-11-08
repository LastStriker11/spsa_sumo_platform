import os
os.chdir("../")

import pandas as pd
import os
from src.RUN_SUMO import parse_sumo_outputs
from src.miscs import config, sim_setup

# load the prior od
input_od = pd.read_csv(config["NETWORK"] / sim_setup["prior_od"], sep='\s+', header=None, skiprows=5)

sim_setup['start_sim_sec'] =  sim_setup["starttime"]*3600 - 500
sim_setup['end_sim_sec']   =  sim_setup["endtime"]*3600 + 500
df_simulated = parse_sumo_outputs(config, sim_setup, input_od)
