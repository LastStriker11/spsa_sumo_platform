import pandas as pd
import numpy as np
import subprocess
import os
from src.miscs import parse_loop_data
#%%
def write_od(config, sim_setup, od_demand):
    """Write the current OD to a text file based specific format.

    Parameters
    ----------
    od_demand : Pandas Dataframe
        Current demand.

    Returns
    -------
    None.

    """
    head_text = (f"$OR;D2 \n* From-Time  To-Time \n{sim_setup['starttime']}.00 {sim_setup['endtime']}.00\n* Factor \n1.00\n")
    file_name = config["CACHE"] / "od_updated.txt"
    file = open(file_name, "w")
    file.write(head_text)
    file.close()
    od_demand.to_csv(file_name, header=False, index=False, sep=" ", mode="a")
#%%
def run_sumo(config, sim_setup, k, seed):
    """Run OD2Trips and SUMO simulation.
    

    Parameters
    ----------
    k : Int
        SUMO replication index.
    seed : Int
        Random seed.

    Returns
    -------
    None.

    """
    p_reroute = 0.1 # rerouting probability
    # Run od2trips_cmd to generate trips file
    od2trips_cmd = (
        f"od2trips --no-step-log --output-prefix {k} --spread.uniform "
        f"--taz-files {config['NETWORK']/sim_setup['taz']} "
        f"-d {config['CACHE']}\\od_updated.txt "
        f"-o {config['CACHE']}\\upd_od_trips.trips.xml --seed {seed}"
        )
    subprocess.run(od2trips_cmd)
    
    # Run SUMO to generate outputs
    sumo_run = (
        f"sumo --mesosim --no-step-log --output-prefix {k} "
        f"-n {config['NETWORK']/sim_setup['net']} "
        f"-b {sim_setup['start_sim_sec']} -e {sim_setup['end_sim_sec']} "
        f"-r {config['CACHE']}\\{k}upd_od_trips.trips.xml "
        f"--vehroutes {config['CACHE']}\\routes.vehroutes.xml "
        f"--additional-files {config['NETWORK']/sim_setup['detector']} "
        f"--xml-validation never --device.rerouting.probability {p_reroute} --seed {seed}"
        )
    subprocess.run(sumo_run)
#%% Aggregate the outputs
def parse_sumo_outputs(config, sim_setup, od_demand):
    """Read and parse SUMO outputs.
    
    """
    write_od(config, sim_setup, od_demand)
    
    np.random.seed(11)
    random_seeds = np.random.normal(0, 10000, sim_setup["n_sumo_replicate"]).astype("int32")
    counts = pd.DataFrame()
    speeds = pd.DataFrame()
    density = pd.DataFrame()
    time = pd.DataFrame()
    for counter in range(sim_setup["n_sumo_replicate"]):
        # Run simulation
        run_sumo(config, sim_setup, counter, random_seeds[counter])
        
        # travel times      
        if sim_setup["objective"] == "travel_times":
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
        elif sim_setup["objective"] == "counts":
            loop_file = str(counter) + "out.xml"
            df_loop = parse_loop_data(config, 
                                      loop_file,
                                      sim_setup["endtime"])
            df_loop = pd.DataFrame(df_loop)
            df_loop.columns = ["label", "counts", "speeds", "density"]
            df_loop = df_loop.set_index("label")
            counts = pd.concat([counts, df_loop["counts"]], axis=1, sort=True)
            speeds = pd.concat([speeds, df_loop["speeds"]], axis=1, sort=True)
            density = pd.concat([density, df_loop["density"]], axis=1, sort=True)
    
    os.remove(config["CACHE"] / "od_updated.txt")
    if sim_setup["objective"] == "travel_times":
        df_tt_mean = time.mean(axis=1)
        return df_tt_mean
    elif sim_setup["objective"] == "counts":
        # df_counts_mean = counts.astype("int32")
        df_counts_mean = pd.DataFrame(columns = ["simulated_counts","simulated_speeds","simulated_density"])
        df_counts_mean["simulated_counts"]= counts.mean(axis=1)
        df_counts_mean["simulated_speeds"]= speeds.mean(axis=1)
        df_counts_mean["simulated_density"]= density.mean(axis=1)
        df_counts_mean.index.names = ["label"]
        return df_counts_mean

    
    
    
    