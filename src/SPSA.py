import numpy as np
import pickle
import pandas as pd
from src.RUN_SUMO import parse_sumo_outputs
from src.miscs import vector2matrix, gof_eval
#%% Simultaneous Perturbation Stochastic Approximation
def SPSA(config, sim_setup, spsa_setup, df_true, input_od):

    # Defining the SPSA variables
    a = spsa_setup["a"]       
    c = spsa_setup["c"]
    A = spsa_setup["A"]
    alpha = spsa_setup["alpha"]
    gamma = spsa_setup["gamma"]

    G = spsa_setup["G"]
    N = spsa_setup["N"]
    seg = spsa_setup["seg"]
    
    #%%
    ODbase = vector2matrix(input_od.iloc[:,2]) # to restore OD after perturbations
    OD = ODbase.copy()
    
    print("Simulation 0 started")
    df_simulated = parse_sumo_outputs(config, sim_setup, input_od)
    df_true = df_true.fillna(0)
    print("Simulation 0 completed")
    y = gof_eval(df_true, df_simulated)
    rmsn = []
    rmsn.append(y)
    print("Starting RMSN = ", y)
    print("========================================")
    Best_OD = input_od.iloc[:,2]
    Best_RMSN = 100
    Best_simulatedCounts = df_simulated["simulated_counts"]

    OD_plus = input_od.copy()
    OD_minus = input_od.copy()
    OD_min = input_od.copy()
    # SPSA iterations
    list_ak = []
    list_ck = []
    list_g = []

    for iteration in range(1, N + 1):
        # calculating gain sequence parameters
        ak = a / ((iteration + A) ** alpha)
        ck = c / (iteration ** gamma)
        list_ak.append(ak)
        list_ck.append(ck)
        g_hat_it = pd.DataFrame()
        for ga in range(0, G):
            delta = 2*np.random.binomial(n=1, p=0.5, size=input_od.shape[0])-1 #Bernoulli distribution
            m = np.mean(OD)

            # perturbation
            for i in range(1, int(np.fix(OD.max()/seg)) + 1):#!!
                for f in range(0, OD.shape[1]):
                    for e in range(0, OD.shape[0]):
                        if OD[e, f] > 0:
                            q = i * seg   #upper limit
                            p = q - seg   #lower limit
                            if OD[e, f] > p and OD[e, f] <= q:
                                if OD[e, f] == ODbase[e, f]:
                                    #propotional perturbation right side
                                    OD[e, f] = OD[e, f] + (ck * delta[e*OD.shape[0]+f]) * q / m
                                    
            del p, q
            
            OD_plus.iloc[:,2] = pd.DataFrame(OD).stack().values
            print("Simulation %d . %d . plus perturbation" %(iteration, ga))
            df_simulated = parse_sumo_outputs(config, sim_setup, OD_plus)
            y = gof_eval(df_true, df_simulated)
            yplus = np.asarray(y)
            
            OD = ODbase.copy()

            for i in range(1, int(np.fix(OD.max()/seg)) + 1):#!!
                for f in range(0, OD.shape[1]):
                    for e in range(0, OD.shape[0]):
                        if OD[e, f] > 0:
                            q = i * seg
                            p = q - seg
                            if OD[e, f] > p and OD[e, f] <= q:
                                if OD[e, f] == ODbase[e, f]:
                                    #propotional perturbation left side
                                    OD[e, f] = OD[e, f] - (ck * delta[e*OD.shape[0]+f]) * q / m
            del p, q
            
            OD_minus.iloc[:,2] = pd.DataFrame(OD).stack().values
            print("Simulation %d . %d . minus perturbation" %(iteration, ga))
            df_simulated = parse_sumo_outputs(config, sim_setup, OD_minus)
            y = gof_eval(df_true, df_simulated)
            yminus = np.asarray(y)
            
            OD = ODbase.copy()

            # Gradient Evaluation
            g_hat_tem = pd.DataFrame((yplus - yminus)/(2*ck*delta))
            g_hat_it = pd.concat([g_hat_it, g_hat_tem], axis=1)

        g_hat = g_hat_it.mean(axis=1)

        list_g.append(abs(g_hat).mean())
        for i in range(1, int(np.fix(OD.max()/seg)) + 1):#!!
            for f in range(0, OD.shape[1]):
                for e in range(0, OD.shape[0]):
                    if OD[e, f] > 4:
                        q = i * seg
                        p = q - seg
                        if OD[e, f] > p and OD[e, f] <= q:
                            if OD[e, f] == ODbase[e, f]:
                                OD[e, f] = OD[e, f] - ((ak * g_hat[e*OD.shape[0]+f] * q) / m)
                            diff = ((OD[e, f] - ODbase[e, f]) / ODbase[e, f])
                            if diff < -0.15:
                                OD[e, f] = ODbase[e, f] * 0.85
                            if diff > 0.15:
                                OD[e, f] = ODbase[e, f] * 1.15
        ODbase = OD.copy()
        OD_min.iloc[:,2] = pd.DataFrame(OD).stack().values
        
        print("Simulation %d . %d . minimization" %(iteration, ga))
        df_simulated = parse_sumo_outputs(config, sim_setup, OD_min)
        y_min = gof_eval(df_true, df_simulated)

        rmsn.append(y_min)
        
        print("Iteration NO. %d done" % iteration)
        print("RMSN = ", y_min)
        print("Iterations remaining = %d" % (N-iteration))
        print("========================================")
        if y_min < Best_RMSN:
            Best_OD = OD_min.iloc[:,2]
            Best_RMSN = y_min
            Best_simulatedCounts = df_simulated["simulated_counts"]

    f = open("counts_SPSA.pckl", "wb") # for counts

    pickle.dump([Best_RMSN, Best_OD, Best_simulatedCounts, rmsn, list_ak, list_ck, list_g], f)
    f.close()
    
    return Best_RMSN, Best_OD, Best_simulatedCounts, rmsn, list_ak, list_ck, list_g
