import os
os.chdir("../")
#%%
import pandas as pd
import numpy as np
import time
import subprocess
from src.miscs import config, sim_setup, parse_loop_data
from src.RUN_SUMO import run_sumo, write_od
#%% paths definition
input_od = pd.read_csv(config["NETWORK"] / sim_setup["prior_od"], sep="\s+", header=None, skiprows=5)

sim_setup["start_sim_sec"] =  sim_setup["starttime"]*3600 - 500
sim_setup["end_sim_sec"]   =  sim_setup["endtime"]*3600 + 500
#%% replicate sumo running
write_od(config, sim_setup, input_od)
np.random.seed(11)
random_seeds = np.random.normal(0, 10000, sim_setup["n_sumo_replicate"]).astype("int32")
counts = pd.DataFrame()
time = pd.DataFrame()
for counter in range(sim_setup["n_sumo_replicate"]):
    print(f"Run the {counter}-th iteration")
    # Run simulation
    run_sumo(config, sim_setup, counter, random_seeds[counter])
    
    # travel times      
    route_xml = config["CACHE"] / f"{counter}routes.vehroutes.xml"
    route_csv = config["CACHE"] / f"{counter}routes.vehroutes.csv"
    data2csv = (
        f"python {config['SUMO']}\\tools\\xml\\xml2csv.py {route_xml} "
        f"-x {config['SUMO']}\\data\\xsd\\routes_file.xsd -o {route_csv}"
        )
    subprocess.run(data2csv)
    df_tt = pd.read_csv(route_csv, sep=";")
    df_tt["Travel_time"] = (df_tt["vehicle_arrival"] - df_tt["vehicle_depart"])
    df_tt = df_tt.groupby(["vehicle_fromTaz","vehicle_toTaz"]).mean()
    time = pd.concat([time, df_tt["Travel_time"]], axis=1)
    # counts
    loop_file = str(counter) + "out.xml"
    df_loop = parse_loop_data(config, 
                              loop_file,
                              sim_setup["endtime"])
    df_loop = pd.DataFrame(df_loop)
    df_loop.columns = ["label", "counts", "speeds", "density"]
    df_loop = df_loop.set_index("label")
    counts = pd.concat([counts, df_loop["counts"]], axis=1, sort=True)
#%% result output
counts.to_csv("networks/synthetic_small/t_test_counts100.csv", header=False)
time.to_csv("networks/synthetic_small/t_test_time100.csv", header=False)