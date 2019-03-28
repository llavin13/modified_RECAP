# -*- coding: utf-8 -*-
"""
Created on Sun Nov  4 19:51:53 2018

@author: llavi
"""

import numpy as _np
import csv as _csv
import scipy.signal
import pandas as pd
import datetime
import const.constants as const
import basicm.pdm

def load_gen_temperatures():
    temp_FOR_df = pd.read_csv(const.STARTING_DIRECTORY+'\\cases\\Forced.outage.rates.by.temperature.and.unit.type.102618.csv', index_col=0)
    temp_FOR_dict = temp_FOR_df.to_dict()
    return temp_FOR_dict
#print(temp_FOR['-30C']['HD'])

## get generator stack
def create_gen_stack_FOR(temp_FOR,case):
    #this is a re-load of something that's already in RECAP and could instead be passed in, but OK for now
    gen_df = pd.read_csv(const.STARTING_DIRECTORY+'\\cases\\'+str(case)+'\\inputs\\generator_module.csv')
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

def gen_outage_dists():
    FOR_dists = pd.read_csv(const.STARTING_DIRECTORY+'\\cases\\availability.distributions.by.unit.type.110518.csv')
    
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
    
    return generator_FORdist_dict

def gen_dists(month,temperature, gen_df, maintenance_schedule):
    #creates full temperature-dependent FOR distributions for generators

    #manual FOR dist to be assigned to generators from input gen_df for now
    #NO LONGER USED (11.10.18)
    #manual_outage_dist = _np.array([[.05, 0.16887827],
    # [.1, 0.11924128],
    # [.15, 0.05676093],
    # [.2, 0.0660266],
    # [.25, 0.0441866],
    # [.3, 0.030344],
    # [.35, 0.02460712],
    # [.4, 0.02042499],
    # [.45, 0.02162338],
    # [.5, 0.02205312],
    # [.55, 0.04304062],
    # [.6, 0.00962204],
    # [.65, 0.0061247],
    # [.7, 0.00523377],
    # [.75, 0.00321084],
    # [.8, 0.00336457],
    # [.85, 0.00405984],
    # [.9,0.01485232],
    # [.95,0.00916784],
    # [1.,0.32717719]])
    
    by_gentype_dists = gen_outage_dists()
    
    gendata_temp = []
    for gen in range(len(gen_df.index)):
        if max(gen_df.iloc[gen][3:15])<1.: #mimics skipping of small generators in main RECAP
            continue
        #cap = rowdata.cap[m-1]*(1-rowdata.maint[m-1]*(maintenance_schedule=="Ideal"))
        month_maint = str(month) + '.2' #for getting scheduled outage fraction
        cap = gen_df.iloc[gen][month]*(1-gen_df.iloc[gen][month_maint]*float(maintenance_schedule=="Ideal"))
        if gen_df.iloc[gen][month]<.5:
            dist = _np.array([1.])
        else:
            gen_type = gen_df.iloc[gen]['Category']
            dist = outage_dist(cap, gen_df.iloc[gen][temperature], by_gentype_dists[gen_type])
                        
            #if maintenance_schedule=="Random" and (rowdata.maintdist is not None):
            #    dist = basicm.pdm.limit_dist1_by_dist2(outage_dist(cap, rowdata.maint[m-1], outagedist[rowdata.maintdist]),dist)
            #a bit hacky, but my approach is the underlying generator outage dist for maintenance is only two-state, which I can 
            #force by making it DR. I also don't check if it's blank first. 
            if maintenance_schedule=="Random":
                print('testing random')
                dist = basicm.pdm.limit_dist1_by_dist2(outage_dist(cap, gen_df.iloc[gen][month_maint], by_gentype_dists['DR']), dist)
            
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
def dict_supply_dists(temp_FOR,case,maintenance_schedule):
    copt_output = {}
    count = 0
    gen_df = create_gen_stack_FOR(temp_FOR,case)
    month_list = ['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec']
    for month in month_list: #one winter, one spring, one summer, one fall
        copt_output[month] = {}
        for temperature in temp_FOR.keys():
            count+=1
            print("processing month-hour temp combo: "+month+","+temperature)
            copt_output[month][temperature]=copt_calc(gen_dists(month,temperature,gen_df,maintenance_schedule))
    return copt_output

def create_calendar(bin_df, case_data):
    #bin_df should pass in a pandas df of the Excel datetime in the first column and a bin float in the 2nd
    #calendar = pd.read_csv(const.STARTING_DIRECTORY+'\\cases\\load_bin_cal.csv')

    calendar = bin_df
    #create needed columns
    calendar.columns = ['Excel_Date','Bin']
    calendar['pd_date'] = pd.TimedeltaIndex(calendar['Excel_Date'], unit='d') + datetime.datetime(1899, 12, 30)
    calendar['pd_date'] = calendar['pd_date'].apply(lambda dt: datetime.datetime(dt.year, dt.month, dt.day, round(dt.hour+float(dt.minute)/60)))
    calendar['month'] = calendar.pd_date.apply(lambda x: x.month)
    calendar['hour'] = calendar.pd_date.apply(lambda x: x.hour)
    calendar['Date'] = calendar.Excel_Date.apply(lambda x: int(x))
    calendar['Bin'] = calendar.Bin.apply(lambda x: int(x))
    
    #add weekday/weekend by match merging
    daytype = pd.read_csv(const.STARTING_DIRECTORY+'\\read_only\\calendar.csv')
    calendar = pd.merge(calendar, daytype, how='left', on=['Date','month'])
    
    #add temperature by matching
    #right now formatting of the read in data is pretty poor
    weather = pd.read_csv(const.STARTING_DIRECTORY+'\\cases\\Temperature.time.series.Philly.DC.Cleveland.Chicago.102918.csv')
    calendar = pd.merge(calendar, weather, how='left', on=['Excel_Date'])
    
    #create avg temp on whatever you decide is the right way. 
    #Right now averages Philly, DC, Cleveland, and Chicago cols
    temp_cols = calendar.loc[: , "Philadelphia":"Chicago"]
    calendar['Mean_T'] = temp_cols.mean(axis=1)

    #This ithe climate-related add on
    #Note this ONLY affects the generator FORs, it DOES NOT affect the loads
    print ('Climate Case is ' + str(case_data.add_on_bool.Is_Climate_Case))
    if case_data.add_on_bool.Is_Climate_Case:
        calendar['Mean_T'] += calendar['Climate_Hourly_Shape']*case_data.add_on_bool.Degrees_Warming
        print('degrees C of increased temperature is ' + str(case_data.add_on_bool.Degrees_Warming))
        print('note this temp increase only affects generator outages, not loads')

    #round avg temp nearest 5, int(), string it with the C so it'll match the other inputs
    #note implicitly temps rounded to 45C+ or -35C- will break this approach
    calendar['T_string']=calendar.Mean_T.apply(lambda x: str(min(int(5*round(float(x)/5)),40))+"C")
    
    #return resulting pandas df
    return calendar

def timeslice_supply(supply_dict,input_df,m,h,dt,ll):
    time_slice = input_df[(input_df['Bin']==ll) & (input_df['month']==m) & (input_df['hour']==h) & (input_df['weekend']==dt)]
    timeslice_weights = time_slice['T_string'].value_counts(normalize=True)
    
    month_list = ['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec']
    time_str = month_list[m-1]
    #if m>=5 and m<=9: #define summer months; janky for now
    #    time_str = 'Jul' #should probably pass month keys of supply_dict here
    #else:
    #    time_str = 'Jan'
        
    count=0
    for key in supply_dict[time_str].keys():
        if key in timeslice_weights.index.values:
            x=supply_dict[time_str][key][:,0]
            y=supply_dict[time_str][key][:,1]*timeslice_weights[key]
            temp_df = pd.DataFrame({'x':x, 'y':y})
            if count==0:
                final_df = temp_df
            else:
                final_df = final_df.set_index('x').add(temp_df.set_index('x'), fill_value=0).reset_index()
            count+=1
        else:
            continue
    
    return final_df.values