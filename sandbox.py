# -*- coding: utf-8 -*-
"""
Created on Sat Nov  3 10:10:19 2018

@author: llavi
"""

import numpy as _np
import pandas as pd
import csv as _csv
import const.constants as const
import basicm.pdm
import scipy.signal
import time


start = time.time()
## import temp dependent FOR table
def load_gen_temperatures():
    temp_FOR_df = pd.read_csv(const.STARTING_DIRECTORY+'\\cases\\Forced.outage.rates.by.temperature.and.unit.type.102618.csv', index_col=0)
    temp_FOR_dict = temp_FOR_df.to_dict()
    return temp_FOR_dict
#print(temp_FOR['-30C']['HD'])

## get generator stack
def create_gen_stack_FOR(temp_FOR):
    #this is a re-load of something that's already in RECAP and could instead be passed in, but OK for now
    gen_df = pd.read_csv(const.STARTING_DIRECTORY+'\\cases\\PJM_Test_largesolar\\inputs\\generator_module.csv')
    
    #assign new FORs
    for key in temp_FOR.keys():
        FOR_list = []
        for gen in range(len(gen_df.index)):
            FOR_list.append(temp_FOR[key][gen_df.iloc[gen]['Category']])
        #print(FOR_list)
        gen_df[key] = pd.Series(FOR_list).values
    return gen_df

## create supply availability distros based on temp dependent FORs

def outage_dist(cap, FOR, outagedist):
    return_dist = _np.ones((len(outagedist)+1,2))
    if (1.-FOR/_np.dot(outagedist[:,0], outagedist[:,1]))>0:
        return_dist[0,1] = (1.-FOR/_np.dot(outagedist[:,0], outagedist[:,1]))
        return_dist[1:,0]-=outagedist[:,0]
        return_dist[1:,1] = outagedist[:,1]*(1-return_dist[0,1])
    else:
        return_dist[1:,1] = outagedist[:,1][:]*FOR
        return_dist[0,1] = 1-FOR
        return_dist[1:,0]-=outagedist[:,0]
        
#        return_dist[0,1] = 0
#        return_dist[1:,0]-=outagedist[:,0]
#        return_dist[1:,1] = outagedist[:,1][:]
#        return_dist[:,1]*=(1-FOR)/_np.dot(return_dist[:,0], return_dist[:,1])
#        return_dist[-1,1]=1-sum(return_dist[:-1,1])
    
    return_dist[:,0]*=cap
    return basicm.pdm.space_dist(return_dist)


def gen_dists(month,temperature,gen_df):
    #creates full temperature-dependent FOR distributions for generators
    
    #manual FOR dist to be assigned to generators from input gen_df for now
    manual_outage_dist = _np.array([[.05, 0.16887827],
     [.1, 0.11924128],
     [.15, 0.05676093],
     [.2, 0.0660266],
     [.25, 0.0441866],
     [.3, 0.030344],
     [.35, 0.02460712],
     [.4, 0.02042499],
     [.45, 0.02162338],
     [.5, 0.02205312],
     [.55, 0.04304062],
     [.6, 0.00962204],
     [.65, 0.0061247],
     [.7, 0.00523377],
     [.75, 0.00321084],
     [.8, 0.00336457],
     [.85, 0.00405984],
     [.9,0.01485232],
     [.95,0.00916784],
     [1.,0.32717719]])
    
    gendata_temp = []
    for gen in range(len(gen_df.index)):
        if max(gen_df.iloc[gen][3:15])<1.: #mimics skipping of small generators in main RECAP
            continue
        if gen_df.iloc[gen][month]<.5:
            dist = _np.array([1.])
        else:
            dist = outage_dist(gen_df.iloc[gen][month], gen_df.iloc[gen][temperature], manual_outage_dist)
            dist = _np.hstack((_np.zeros(int(min(dist[:,0]))), dist[:,1]))
            assert round(sum(dist),6)==1.
        gendata_temp.append(dist)
    return(gendata_temp)

def copt_calc(gens):
    COPT = _np.array([1.])

    for i in range(len(gens)):
        #print(i)
        COPT = scipy.signal.fftconvolve(COPT,
                                        basicm.pdm.space_dist(_np.vstack((_np.arange(len(gens[i])),gens[i])).T)[:,1])
            
    COPT[_np.nonzero(COPT<0)]=0
    
    min_capacity = min(_np.nonzero(_np.cumsum(COPT)>const.LOW_PROB_CUT)[0])
    COPT/=sum(COPT)
    
    return _np.vstack((_np.arange(min_capacity,len(COPT)),COPT[min_capacity:])).T

#this is our distro for now, doesn't include planned maintenance
#you have to input the month and temp you want
#copt_calc(gen_dists('Jun','-30C'))

#this runs everything and wraps it as a dict of dicts, but takes a little while
def dict_supply_dists(temp_FOR):
    copt_output = {}
    count = 0
    gen_df = create_gen_stack_FOR(temp_FOR)
    for month in ['Jan','Jul']: #one winter, one summer
        copt_output[month] = {}
        for temperature in temp_FOR.keys():
            count+=1
            print("this is the "+str(count)+"th month-temp combo added")
            copt_output[month][temperature]=copt_calc(gen_dists(month,temperature,gen_df))
    return copt_output

#print(copt_output)
#print(copt_output['Jun']['30C'])

#run the full thing, if you like
dict_supply_dists(load_gen_temperatures())

print('right now this takes ' +str(time.time()-start) + ' seconds')


#this is for outputting results you'd like to transfer to R. Don't use it for now.
'''
test_df = pd.DataFrame()
for month in ['Jul']:
    for temperature in ['-30C']:
        temp_array = copt_calc(gen_dists(month,temperature))
        gen_string = month+temperature+'_GEN'
        test_df[gen_string] = temp_array[:,0]
write_df = pd.DataFrame().reindex_like(test_df)
#print(write_df)
for month in ['Jul']:
    for temperature in temp_FOR.keys():
        temp_array = copt_calc(gen_dists(month,temperature))
        gen_string = month+temperature+'_GEN'
        #write_df[gen_string] = temp_array[:,0]
        df_temp = pd.DataFrame()
        df_temp[gen_string]=temp_array[:,0]
        write_df = pd.concat([write_df,df_temp], ignore_index=True, axis=1)
        prob_string = month+temperature+'_PROB'
        df_temp = pd.DataFrame()
        df_temp[prob_string]=temp_array[:,1]
        write_df = pd.concat([write_df,df_temp], ignore_index=True, axis=1)
        #write_df[prob_string] = temp_array[:,1]
'''
#print(write_df)
#write_df.to_csv('summer_df.csv')
#C:\Users\llavi\Desktop\RECAP\Feb 2017 Model Release\R_graphing is desired directory

