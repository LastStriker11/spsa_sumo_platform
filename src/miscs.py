import json
import pandas as pd
import numpy as np
import subprocess
from typing import Union
from pathlib import Path


def gof_eval(df_true, df_simulated):
    data = pd.DataFrame()
    data['diff_square'] = (df_simulated['simulated_counts'] - df_true['true_counts'])**2
    n = data.shape[0]
    sum_diff = data['diff_square'].sum()
    sum_true = df_true['true_counts'].sum()
    RMSN = np.sqrt(n*sum_diff)/sum_true
    return RMSN

def load_experiment_config(config: Union[Path, str]="config.json",
                           sim_setup: Union[Path, str]="simulation_setups.json",
                           spsa_setup: Union[Path, str]="spsa_setups.json"):
    """Load paths, simulation setups and algorithm setups
    

    Parameters
    ----------
    config : Union[Path, str], optional
        Paths to cache, network, and SUMO. The default is "config.json".
    sim_setup : Union[Path, str], optional
        Simulation parameters. The default is "simulation_setups.json".
    spsa_setup : Union[Path, str], optional
        SPSA parameters. The default is "spsa_setups.json".

    Returns
    -------
    config : Dictionary
    sim_setup : Dictionary
    spsa_setup : Dictionary

    """
    config = Path(config) if isinstance(config, str) else config
    config = json.load(open(config))
    for k, v in config.items():
        config[k] = Path(v)
    
    sim_setup = Path(sim_setup) if isinstance(sim_setup, str) else sim_setup
    sim_setup = json.load(open(sim_setup))
    for k, v in sim_setup.items():
        sim_setup[k] = v
    
    spsa_setup = Path(spsa_setup) if isinstance(spsa_setup, str) else spsa_setup
    spsa_setup = json.load(open(spsa_setup))
    for k, v in spsa_setup.items():
        spsa_setup[k] = v
        
    return config, sim_setup, spsa_setup

config, sim_setup, spsa_setup = load_experiment_config()
    

def vector2matrix(od_vector):
    """A simple function that converts an OD vector to OD matrix. We read
    through the vector (row after row) and create a matrix.

    Parameters
    ----------
    od_vector : Pandas DataFrame

    Returns
    -------
    od_matrix : Numpy array
        Two-dimensional numpy array.

    """
    n_zones = int(np.sqrt(od_vector.shape[0]))
    od_matrix = np.zeros((n_zones, n_zones))
    m = 0
    for i in range(0, n_zones):
        for j in range(0, n_zones):
            od_matrix[i,j]= od_vector[m];
            m = m + 1;
    return od_matrix


def parse_loop_data(config, loop_file, endtime):
    """Read the Loop Detectors Data: Each SUMO run produces a file with the
    traffic counts. This function reads the corresponding traffic counts file
    and converts the readings to traffic counts usable in Matlab. The process
    is the simple xml2csv and readcsv process commonly used.
    

    Parameters
    ----------
    config : Dictionary
        Necessary paths.
    loop_file : String
        SUMO detector data file.
    endtime : Float/Int
        End time of the current interval.

    Returns
    -------
    df_all : Pandas Dataframe
        All loop data.

    """
    # We first do some time manipulations necessary.
    fract = float(endtime)
    integ = int(fract)
    fract = round(fract-integ, 2)
    endSimTime = integ*60*60 + fract*60
        
    output_file =(config["NETWORK"] / "loopDataName.csv")
    data2csv = (
        f"python {config['SUMO']}\\tools\\xml\\xml2csv.py "
        f"{config['NETWORK']/loop_file} "
        f"--x {config['SUMO']}\\data\\xsd\\det_e1meso_file.xsd "
        f"-o {output_file}"
        )
        
    subprocess.run(data2csv)

    # Then we read the data from this run (taking into account the proper time
    # interval).
    
    df_trips = pd.read_csv(output_file, sep=";", header=0)
    df_trips = df_trips[df_trips["interval_end"] < endSimTime]

    # The final step is to aggregate the counts per link (so that we do can
    # estimate per link flow and not per lane). 
    det_id = df_trips["interval_id"]
    edge_id = [word.split("_")[1] for word in det_id]
    df_trips["EdgeID"] = edge_id
    
    temp = pd.DataFrame()
    temp["EdgeID"] = edge_id
    temp["Counts"] = df_trips["interval_entered"]
    temp["Speeds"] = df_trips["interval_speed"]
    temp["Density"] = df_trips["interval_density"]
    temp = temp.fillna(0)
    df_group = temp.groupby("EdgeID").agg(np.sum)
    df_group2 = temp.groupby("EdgeID").agg(np.average)
    df_group["Edge"] = df_group.index
    df_group2["Edge"] = df_group.index
    df_all = pd.DataFrame()
    df_all["Counts"] = df_group["Counts"]
    df_all["Speeds"] = df_group2["Speeds"]
    df_all["Density"] = df_group2["Density"]
    df_all = df_all.reset_index()
    df_all = df_all.values
    del temp, df_group
    return df_all
    
