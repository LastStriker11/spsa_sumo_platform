import os
os.chdir("../")
#%%
import pandas as pd
import time
import matplotlib.pyplot as plt
from src.SPSA import SPSA
from src.miscs import config, sim_setup, spsa_setup
#%%
input_od = pd.read_csv(config["NETWORK"] / sim_setup["prior_od"], sep="\s+", header=None, skiprows=5)

sim_setup["start_sim_sec"] =  sim_setup["starttime"]*3600 - 500
sim_setup["end_sim_sec"]   =  sim_setup["endtime"]*3600 + 500
#%%
if not os.path.exists(config["CACHE"]):
    os.mkdir(config["CACHE"])

# for travel time
if sim_setup["objective"] == "travel_times":
    true_data = pd.read_csv(config["NETWORK"] / sim_setup["tt_data"], header=None)
    true_data["label"] = list(zip(true_data.iloc[:,0], true_data.iloc[:,1]))
    true_data.drop([0,1], axis=1, inplace=True)
    true_data.set_index("label", inplace=True)
    true_data.columns = ["true"]
    
# for counts
elif sim_setup["objective"] == "counts":
    true_data = pd.read_csv(config["NETWORK"] / sim_setup["loop_data"], header=None)
    true_data.columns = ["label", "true_counts", "true_speeds", "true_density"] # for counts
    true_data.set_index("label", inplace=True) # for counts

# load demand
input_od = pd.read_csv(config["NETWORK"] / sim_setup["prior_od"], sep="\s+", header=None, skiprows=5)
#%%
start = time.time()
Best_RMSN, Best_OD, Best_SimulatedCounts, rmsn, list_ak, list_ck, list_g = SPSA(config, sim_setup, spsa_setup, true_data, input_od)
end = time.time()
print("Running time: %d" %(end-start))
plt.rcParams.update({"figure.figsize":(6,6), "figure.dpi":60, "figure.autolayout": True})
plt.figure()
plt.plot(rmsn, label = "SPSA")
plt.xlabel("No of Iterations")
plt.ylabel("RMSN")
plt.legend()
plt.show()