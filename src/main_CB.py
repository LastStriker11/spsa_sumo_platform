import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import scipy.io
import seaborn as sns
import Conv_Combination as CB
import os

#%%
Network = 'SiouxFalls'
GoF='RMSN'
Weights = dict(Counts     = 1,\
             Speed        = 0.5,\
             Density      = 0,\
             TravelTimes  = 0)
Step=10                          # Define how many points you will evaluate with the Conex Combination
From_c=True                     # Derive the step size directly from the parameter 'c'

if Network == 'SiouxFalls': # only counts no traveltimes
    config = dict(NETWORK      = r'../Network/SiouxFalls/',\
                 python               = r'C:/ProgramData/Anaconda3/python.exe',\
                 SUMO      = r'C:/Program Files (x86)/Eclipse/Sumo/',\
                 pathtoScripts        = r'./',\
                 tempLocalLocation    = r'../temp/',\
                 ScenarioDataFolder   = r'../Network/SiouxFalls/',\
                 OS                   = 'windows')
    
#   objective = counts    
    sim_setup = dict(objective  = 'counts',\
                       mesoNet              = 'upd_MESO_SiouxFalls.net.xml',\
                       tazname              = 'myTaZes.taz.xml',\
                       loopDataName         = 'out.xml',\
                       additionalName       = 'adTrCounts.xml',\
                       inputOD              = 'start_od.txt',\
                       tripInfo             = 'tripInfo.xml',\
                       starttime            = "08.00",\
                       endtime              = "09.00",\
                       NSumoRep             = 2,\
                       Ass_type             = 'tripbased',\
                       NCountedLinks        = 3442,\
                       loop_data             = 'truedata.csv',\
                       tt_data          = 'true_tt.csv',\
                       scenarioID           = '')

    spsa_setup = dict(   G         = 2,\
                        Min_error = 0.15,\
                        a         = 4,\
                        c         = 1,\
                        A         = 25,\
                        alpha     = 0.3,\
                        gamma     = 0.15,\
                        h         = 0.7,\
                        N         = 10,\
                        seg       = 5)

elif Network == 'Munich_CC': # both counts and travel times 
    config = dict(NETWORK=r'../Network/Munich_cc/', \
                 python=r'C:/ProgramData/Anaconda3/python.exe', \
                 SUMO=r'C:/Program Files (x86)/Eclipse/Sumo/', \
                 pathtoScripts=r'./', \
                 tempLocalLocation=r'../temp/', \
                 ScenarioDataFolder=r'../Network/Munich_cc/', \
                 OS='windows')
    
#   objective = counts or travel_times
    sim_setup = dict( objective     = 'counts',\
                        mesoNet                 = 'Munich_cc2_mr.net.xml', \
                        tazname                 = 'taZes2.taz.xml', \
                        loopDataName            = 'out.xml', \
                        additionalName          = 'temp2.add.xml', \
                        inputOD                 = 'start_od.txt', \
                        tripInfo                = 'tripInfo.xml', \
                        starttime               = "08.00", \
                        endtime                 = "09.00", \
                        NSumoRep                = 2, \
                        Ass_type                = 'tripbased', \
                        NCountedLinks           = 3442, \
                        loop_data                = 'truedata.csv',\
                        tt_data             = 'true_tt.csv',\
                        scenarioID              = '')

    spsa_setup = dict(G=1, \
                     Min_error=0.15, \
                     a=40, \
                     c=0.15, \
                     A=25, \
                     alpha=0.3, \
                     gamma=0.15, \
                     h=0.7, \
                     N=1, \
                     seg=5)
    
if not os.path.exists(config["tempLocalLocation"]):
    os.mkdir(config["tempLocalLocation"])

config["CACHE"] = config["tempLocalLocation"]+sim_setup["scenarioID"]

# for travel time
if sim_setup["objective"] == 'travel_times':
    true_data = pd.read_csv(config["NETWORK"] + sim_setup['tt_data'], header=None)
    true_data['label'] = list(zip(true_data.iloc[:,0], true_data.iloc[:,1]))
    true_data.drop([0,1], axis=1, inplace=True)
    true_data.set_index('label', inplace=True)
    true_data.columns = ['true']
    Weight=np.array(Weights['TravelTimes'])
# for counts

elif sim_setup["objective"] == 'counts':
    true_data = pd.read_csv(config["NETWORK"] + sim_setup['loop_data'], header=None)
    true_data.columns = ['label', 'true_counts', 'true_speeds', 'true_density'] # for counts
    true_data.set_index('label', inplace=True) # for counts
    Weight=np.array([Weights['Counts'],Weights['Speed'],Weights['Density']])
    
#%%
#% Start Simulation Times
integ= np.floor(np.double(sim_setup["starttime"]))
fract=100*(np.double(sim_setup["starttime"])-integ)
beginSim = int(integ*60*60 + fract*60)
#% End Simulation Times
integ=np.floor(np.double(sim_setup["endtime"]))
fract=100*(np.double(sim_setup["endtime"])-integ)
endSim = int(integ*60*60 + fract*60)

sim_setup['start_sim_sec'] =  str(beginSim)
sim_setup['end_sim_sec']   =  str(endSim+500)
#%%
input_od = pd.read_csv(config["NETWORK"] + sim_setup["inputOD"], sep='\s+', header=None, skiprows=5)
#%%
input_od2=input_od.copy()

input_od2.iloc[:,2]=input_od2.iloc[:,2]*0.7
input_od.iloc[:,2]=input_od.iloc[:,2]*0.2
rmsn, Step =CB.CB(config, sim_setup, spsa_setup, true_data, input_od,input_od2, GoF,Weight,Step,From_c)
plt.plot(Step, rmsn, label = 'Frequency with '+str(GoF)+'  -  c = '+str(spsa_setup["c"])+' Weights='+str(Weight))
plt.xlabel("X")
plt.ylabel(str(GoF))
plt.legend()
plt.show()