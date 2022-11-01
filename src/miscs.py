import json
import pandas as pd
import numpy as np
import subprocess
from typing import Union
from pathlib import Path

def load_experiment_config(config: Union[Path, str]="config.json",
                           sim_setup: Union[Path, str]="simulation_setups.json",
                           spsa_setup: Union[Path, str]="spsa_setups.json"):
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
    

def Vector2Full(allODArray):
    """A simple function that converts an OD vector to OD matrix. We read
    through the vector (row after row) and create a matrix.

    Parameters
    ----------
    allODArray : TYPE
        DESCRIPTION.

    Returns
    -------
    FullOD : TYPE
        DESCRIPTION.

    """
    nZones = int(np.sqrt(allODArray.shape[0]))
    FullOD = np.zeros((nZones,nZones))
    m = 0
    for i in range(0, nZones):
        for j in range(0, nZones):
            FullOD[i,j]= allODArray[m];
            m=m+1;
    return FullOD


def parse_loop_data(pathToSUMOtools, pathtoCaseOutput, loop_file, endtime):
    """Read the Loop Detectors Data: Each SUMO run produces a file with the
    traffic counts. This function reads the corresponding traffic counts file
    and converts the readings to traffic counts usable in Matlab. The process
    is the simple xml2csv and readcsv process commonly used.
    

    Parameters
    ----------
    pathToSUMOtools : TYPE
        DESCRIPTION.
    pathtoCaseOutput : TYPE
        DESCRIPTION.
    loopDataName : TYPE
        DESCRIPTION.
    endtime : TYPE
        DESCRIPTION.
    OS : TYPE
        DESCRIPTION.

    Returns
    -------
    AllPeriodEdgesFlows : TYPE
        DESCRIPTION.

    """
    # We first do some time manipulations necessary.
    fract=float(endtime)
    integ=int(fract)
    fract=round(fract-integ, 2)
    endSimTime=integ*60*60 + fract*60
        
    Loopdata_csv=(r''+ pathtoCaseOutput + '/' 'loopDataName.csv')

    Data2csv = (r'python ' '"' + pathToSUMOtools + 'tools/xml/xml2csv.py' '"'\
                ' ' '"' + pathtoCaseOutput + loop_file + '"' ' --x '\
                '"' + pathToSUMOtools + 'data/xsd/det_e1meso_file.xsd' '"'+ ' -o '\
                '"' + Loopdata_csv + '"')
    subprocess.run(Data2csv)

    # Then we read the data from this run (taking into account the proper time
    # interval).
    
    simulated_tripsInTable= pd.read_csv(Loopdata_csv, sep=";", header=0)
    simulated_tripsInTable = simulated_tripsInTable[simulated_tripsInTable['interval_end'] \
                                                    < endSimTime]

    # The final step is to aggregate the counts per link (so that we do can
    # estimate per link flow and not per lane). 
    Detector_ID=simulated_tripsInTable['interval_id']
    myEdges = [word.split('_')[1] for word in Detector_ID]
    simulated_tripsInTable['EdgeID'] = myEdges
    
    temp = pd.DataFrame()
    temp['EdgeID'] = myEdges
    temp['Counts'] = simulated_tripsInTable['interval_entered']
    temp['Speeds'] = simulated_tripsInTable['interval_speed']
    temp['Density'] = simulated_tripsInTable['interval_density']
    temp=temp.fillna(0)
    Grouped = temp.groupby('EdgeID').agg(np.sum)
    Grouped2 = temp.groupby('EdgeID').agg(np.average)
    Grouped['Edge'] = Grouped.index
    Grouped2['Edge'] = Grouped.index
    AllPeriodEdgesFlows = pd.DataFrame()
    AllPeriodEdgesFlows['Counts'] = Grouped['Counts']
    AllPeriodEdgesFlows['Speeds'] = Grouped2['Speeds']
    AllPeriodEdgesFlows['Density'] = Grouped2['Density']
    AllPeriodEdgesFlows = AllPeriodEdgesFlows.reset_index()
    AllPeriodEdgesFlows = AllPeriodEdgesFlows.values
    del temp, Grouped
    return AllPeriodEdgesFlows
    
def gof_eval(truedata, simulatedCounts):
    """This function provides some measures of Goodness of Fit.
    

    Parameters
    ----------
    truedata : TYPE
        DESCRIPTION.
    simulatedCounts : TYPE
        DESCRIPTION.

    Returns
    -------
    TYPE
        DESCRIPTION.
    counts : TYPE
        DESCRIPTION.

    """
    truedata = truedata.reshape(len(truedata), 1)
    simulatedCounts = simulatedCounts.reshape(len(simulatedCounts),1)
    kk=truedata.shape
    RMSNE=[]
    for i in range(0, kk[1]):
        RMSNE.append(0)
        for j in range(0, kk[0]):
            if truedata[j,i]>0:
                RMSNE[i]=RMSNE[i]+((simulatedCounts[j,i]-truedata[j,i])/truedata[j,i])**2
            elif simulatedCounts[j,i]>0:
                RMSNE[i]=RMSNE[i]+1
        RMSNE[i]=np.sqrt(RMSNE[i]/kk[0])
    y = RMSNE    
    return y #, counts

