import numpy as np
import pickle
import scipy.io
import pandas as pd
import RUN_SUMO # for counts
#import RUN_SUMO_tt as RUN_SUMO # for travel time
import Basic_scripts as bs
#%% 
def CB_gof(data,true_data,Weight,GoF):
    OF=[]
    for i in range(np.size(Weight)):
        data['diff_square'] = (data.iloc[:,i] - true_data.iloc[:,i])**2
        n = data.shape[0]
        sum_diff = data['diff_square'].sum()
        sum_true=true_data.iloc[:,0].sum()
        if GoF == 'RMSN':
            y=np.sqrt(n*sum_diff)/sum_true
            OF.append(y)
        elif GoF == 'RMSE':
            y=np.sqrt((sum_diff)/n)
            OF.append(y)
    print('OF:' + str(OF))
    print('OF with Weight:' + str(OF*Weight))
    return sum(OF*Weight)
 

### Convex Combination
# Evaluate objective function (CB_gof) between two points X0 and X1. Uses the C parameters from "c"
#%%
    '''
    INOUT:
        config = Network path for SUMO
        sim_setup = Network data
        spsa_setup = SPSA parameters. Specifically, we need the perturbation: spsa_setup["c"]=1
        data = data to calculate the objective function (counts, travel times, density, speed, ... )
        input_od = X0 - One of the two OD matrices
        input_od2 = X1 - One of the two OD matrices
        GoF = Objective function - RMSE or RMSN
        Weight = Weight of the information (counts, speeds, travel times,...)
        
    '''
def CB(config, sim_setup, spsa_setup, data, input_od, input_od2, GoF, Weight, Step, From_c=False):

    # Defining Evaluation Points
    c = spsa_setup["c"]
    
    #%%
    OD1 = bs.Vector2Full(input_od.iloc[:,2])  # to restore OD after perturbations
    OD2 = bs.Vector2Full(input_od2.iloc[:,2])  # to restore OD after perturbations
    
    # Get the stepsize for the analysis
    if From_c is True:
        Step=float(c)/np.max(OD1)
        Step=np.linspace(0,1,round(1/float(Step))+1)
    else:
        Step=np.linspace(0,1,Step)
    input_od_test=input_od.copy()
    
    # Get new matrix
    rmsn = []
    print('========================================')
    print('Convex combination for Delta (Max)= '+str(np.max(OD1-OD1*(1-Step[1])+OD2*Step[1])))
    print('Convex combination for Delta (Min)= '+str(np.min(OD1-OD1*(1-Step[1])+OD2*Step[1])))
    print('Convex combination for Delta (Avg)= '+str(np.mean(OD1-OD1*(1-Step[1])+OD2*Step[1])))
    print('========================================')
    
    for X in Step:
        OD_tmp=OD1*(1-X)+OD2*X
        OD_tmp = OD_tmp.copy()
        input_od_test.iloc[:,2]=np.reshape(OD_tmp,np.shape(input_od)[0])
        print('X = '+str(X)+' - Simulation started')
        print('Assigning X = '+str(sum(sum(OD_tmp))))
        data_sim = RUN_SUMO.CallSUMOGetCounts(config, sim_setup, input_od_test)
        data_eval = data_sim.dropna(axis=1)
        print('X = '+str(X)+' : Simulation completed')
        y = CB_gof(data_eval,data,Weight,GoF)
        rmsn.append(y)
        print(str(GoF)+' = ', y)
        print('========================================')
    
    return rmsn, Step
