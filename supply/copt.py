# -*- coding: utf-8 -*-
"""
Created on Fri Dec 14 11:37:36 2012

@author: Ryan Jones - Ryan.Jones@ethree.com
"""

import numpy as _np
import scipy.signal
import pandas as pd #added by Luke
if not __name__ == "__main__":
    import const.constants as const
    import basicm as _basicm
    import timeseries as _timeseries
    import lukeaddon.temperature_supply as addon #added by Luke

def copt_calc(case_data, zone, month):
    COPT = _np.array([1.])

    for i in case_data.gendata.units[zone].values():
        #print(i)
        if case_data.gendata.derate[i]==0.:
            continue
        elif case_data.gendata.derate[i]==1.:
            COPT = scipy.signal.fftconvolve(COPT, case_data.gendata.gendist[month][i])
        else:
            COPT = scipy.signal.fftconvolve(COPT,
                                            _basicm.pdm.space_dist(_np.vstack((_np.arange(len(case_data.gendata.gendist[month][i]))*case_data.gendata.derate[i],case_data.gendata.gendist[month][i])).T)[:,1])
            
    COPT[_np.nonzero(COPT<0)]=0
    
    min_capacity = min(_np.nonzero(_np.cumsum(COPT)>const.LOW_PROB_CUT)[0])
    COPT/=sum(COPT)
    
    return _np.vstack((_np.arange(min_capacity,len(COPT)),COPT[min_capacity:])).T


def zone_gen(case_data, zone):
    gen = {}
    
    #check initialization of use of add on 
    #Luke_method = True
    print("right now use of alternative method is " +str(case_data.add_on_bool.Use_Add_On))

    for m in case_data.interm_calc.timeslicelist[0]:
        conv = _np.array([[0,1]], dtype = 'f8')
        
        #if case_data.gendata.units.has_key(zone):
        if zone in case_data.gendata.units:
            conv = copt_calc(case_data, zone, m)
            #make a call for the Luke-input COPT in the first month
            #if m==1 and Luke_method:
                #create a dict of dicts of seasonal temperature-dependent supply availability (in MW)
            #    copt_output = addon.dict_supply_dists(addon.load_gen_temperatures())
                    
                #get and create the calendar, too, since you only need that once
                #= _np.vstack((profile.dates, load_bin_calendar)).T this is how you originally get load_bin_calendar
            #    load_bin_df = pd.DataFrame(case_data.interm_calc.load_bin_calendar)
            #    calendar_df = addon.create_calendar(load_bin_df)
            #otherwise do what the tool normally does
            #else:
            #    conv = copt_calc(case_data, zone, m)
            
        for h, dt, ll in _basicm.gm.combination(case_data.interm_calc.timeslicelist[1:]):        
            
            #also force to only do this if the zone is the main zone (PJM)
            if case_data.add_on_bool.Use_Add_On and zone in case_data.gendata.units:
                #print(zone,m,h,dt,ll)
                gen[m, h, dt, ll] = addon.timeslice_supply(case_data.copt_output,case_data.calendar_df,m,h-1,dt,ll)
                
            #otherwise do what tool normally does
            else:
                gen[m, h, dt, ll] = conv
            
            #print this bs
            #if m==7 and h==16 and dt==0 and ll==3 and zone in case_data.gendata.units:
            #    print('we are in!!')
            #    df = pd.DataFrame(gen[m,h,dt,ll])
            #    print(df)
            #    df.to_csv('supply_pdf.csv')
            #    print('writing happened')
    return gen

def independent_zone_net_gen(case_data, include_supply_vg=True):
    include_demand_vg = True
    netsupply = {}
    
    netsupply[case_data.calculation_settings.zone_to_analyze] = {}
    for t in _basicm.gm.combination(case_data.interm_calc.timeslicelist):
        netsupply[case_data.calculation_settings.zone_to_analyze][t] = _np.array([[0,1]])
    
    for layer in range(max(case_data.transmission.layers.keys()), 0,-1):
        for zone in case_data.transmission.layers[layer]:
            netsupply[zone] = {}
            netload = _timeseries.netload.calc(case_data, zone, include_supply_vg=include_supply_vg, include_demand_vg=include_demand_vg)
            gen = zone_gen(case_data, zone)
            
            for m, h, dt, ll in _basicm.gm.combination(case_data.interm_calc.timeslicelist):
                netsupply[zone][m, h, dt, ll] = _basicm.pdm.fft_convolution(gen[m, h, dt, ll], netload[m, h, dt, ll], '-')
                
    return netsupply


