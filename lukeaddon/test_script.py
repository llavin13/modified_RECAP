# -*- coding: utf-8 -*-
"""
Created on Sat Nov 10 15:13:57 2018

@author: llavi
"""

import numpy as _np
import csv as _csv
import scipy.signal
import pandas as pd
#import const.constants as const

FOR_dists = pd.read_csv('C:\\Users\\llavi\\Desktop\\RECAP\\Feb 2017 Model Release\\cases\\availability.distributions.by.unit.type.110518.csv')

total_out = FOR_dists['P(partial)']+FOR_dists['P(down)']
FOR_dists['relP(partial)']=(FOR_dists['P(partial)']/total_out)
FOR_dists['relP(down)']=1.-FOR_dists['relP(partial)']
FOR_dists['Rounded_Avg_partial']=(round(FOR_dists['Avg_partial']*2,1)/2)


FOR_increments = [.05,.1,.15,.2,.25,.3,.35,.4,.45,.5,.55,.6,.65,.7,.75,.8,.85,.9,.95,1.]
init_weights = [0]*len(FOR_increments)

generator_FORdist_dict = {}
for index in FOR_dists.index.values:
    FOR_dists_df = pd.DataFrame({'increment': FOR_increments, 'weight': init_weights})
    
    #load in the full derate percent
    rel_down = FOR_dists.iloc[index]['relP(down)']
    index_down = FOR_dists_df[FOR_dists_df.loc[:,'increment'] == 1.].index[0]
    #load in partial derate percent
    rel_partial = FOR_dists.iloc[index]['relP(partial)']
    rounded_avg_partial = FOR_dists.iloc[index]['Rounded_Avg_partial']
    index_partial = FOR_dists_df[FOR_dists_df.loc[:,'increment'] == rounded_avg_partial].index[0]

    #convert df to numpy array
    FOR_dists_np = FOR_dists_df.values
    FOR_dists_np[index_down][1] = rel_down
    FOR_dists_np[index_partial][1] = rel_partial
    
    #add generator as key and this np array of outage probabilities
    generator = FOR_dists.iloc[index][FOR_dists.columns.values[0]] 
    generator_FORdist_dict[generator] = FOR_dists_np

#add the POS demand response stuff at the end
DR_dists_df = pd.DataFrame({'increment': FOR_increments, 'weight': init_weights})
DR_dists_np = DR_dists_df.values
DR_dists_np[len(init_weights)-1][1]=1.
generator_FORdist_dict['DR']=DR_dists_np

print(generator_FORdist_dict)