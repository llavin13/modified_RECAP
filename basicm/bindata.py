# -*- coding: utf-8 -*-
"""
Created on Fri Jan 04 15:51:52 2013

@author: Ryan Jones - Ryan.Jones@ethree.com
"""

import basicm.gm as _gm
import numpy as _np
import basicm.pdm as _pdm

def bin_primary_load_profile(case_data, profile):
    bins, load_break_points = {}, {}
    rehapedload = _gm.reshape(profile.values, ncolumns = 24)
    load_bin_record = _np.zeros(_np.shape(rehapedload), dtype = int)
    
    load_bins = case_data.calculation_settings.load_bins

    
    relevant_calendar = _gm.relevant_calendar_short(profile.dates)[:,1:]
    
    for day_type in _gm.combination([range(1,13), range(2)]):
        calendar_bool = _np.all(day_type==relevant_calendar, axis = 1)
        load_slice = rehapedload[calendar_bool]
        load_bin_short_record = _np.zeros(_np.shape(load_slice), dtype = int)
        
        for i in load_bins.keys():
            if i == max(load_bins.keys()):
                start, end = _np.percentile(load_slice, load_bins[i][0], axis = 0), _np.percentile(load_slice, load_bins[i][1], axis = 0)
                load_bool = _np.all(_np.concatenate((load_slice>=start, load_slice<=end), axis = 0).reshape(2,len(load_slice),24), axis = 0)
            else:
                start, end = _np.percentile(load_slice, load_bins[i][0], axis = 0), _np.percentile(load_slice, load_bins[i][1], axis = 0)
                load_bool = _np.all(_np.concatenate((load_slice>=start, load_slice<end), axis = 0).reshape(2,len(load_slice),24), axis = 0)
            
            for h, (s, e) in enumerate(zip(start, end)):
                load_break_points[day_type[0], h+1, day_type[1], i] = s, e
            
            for h, fload in enumerate(load_bool.T):
                bins[day_type[0], h+1, day_type[1], i] = load_slice[fload, h]
            
            load_bin_short_record[_np.nonzero(load_bool)] = int(i)
        
        assert len(load_slice)==sum([len(bins[day_type[0], 1, day_type[1], ll]) for ll in load_bins.keys()])
        load_bin_record[calendar_bool] = load_bin_short_record
    
    load_bin_record = _np.reshape(load_bin_record, _np.prod(_np.shape(load_bin_record)))

    return bins, load_break_points, load_bin_record


def match_ind2_with_ind1(ind1, ind2):
    ind2 = ind2[ind2<=max(ind1)]
    ind2 = ind2[ind2>=min(ind1)]
    return _np.searchsorted(_np.round(ind1,2), _np.round(ind2,2))

def hist_time_series_vg(case_data, profile, correlation, capacity, weekdaymatters):
    bins = {}
    
    load_levels = case_data.interm_calc.load_bin_calendar[match_ind2_with_ind1(case_data.interm_calc.load_bin_calendar[:,0], profile.dates),1]
    numloadlevels = max(case_data.calculation_settings.load_bins.keys())
    
    if weekdaymatters:
        relevant_calendar = _gm.relevant_calendar_long(profile.dates)[:,1:]
        
        for m, dt, h in _gm.combination([range(1,13), range(2), range(1,25)]):
            calendar_bool = _np.all([m, dt, h]==relevant_calendar, axis = 1)
            
            vg_slice = profile.values[calendar_bool]*capacity
            
            if correlation:
                for ll in range(1, 1+numloadlevels):
                    bins[m, h, dt, ll] = return_hist_with_correlation(ll, calendar_bool, vg_slice, load_levels)
            else:
                bins[m, h, dt, 1] = _pdm.create_histogram(vg_slice)
                for ll in range(2, 1+numloadlevels):
                    bins[m, h, dt, ll] = bins[m, h, dt, 1]
    else:
        relevant_calendar = _gm.relevant_calendar_long(profile.dates)[:,1::2]
        
        for m, h in _gm.combination([range(1,13), range(1,25)]):
            calendar_bool = _np.all([m, h]==relevant_calendar, axis = 1)
            
            vg_slice = profile.values[calendar_bool]*capacity
            
            if correlation:
                for ll in range(1, 1+numloadlevels):
                    bins[m, h, 0, ll] = return_hist_with_correlation(ll, calendar_bool, vg_slice, load_levels)
                    bins[m, h, 1, ll] = bins[m, h, 0, ll]
            else:
                bins[m, h, 0, 1] = _pdm.create_histogram(vg_slice)
                bins[m, h, 1, 1] = bins[m, h, 0, 1]
                for ll in range(2, 1+numloadlevels):
                    bins[m, h, 0, ll], bins[m, h, 1, ll] = bins[m, h, 0, 1], bins[m, h, 1, 1]

    return bins
    

def return_hist_with_correlation(ll, calendar_bool, vg_slice, load_levels):
    ll_low = ll
    ll_high = ll
    
    while True:
        vg_slice_final = vg_slice[_np.any(_np.vstack((load_levels[calendar_bool]==ll_low, load_levels[calendar_bool]==ll_high)), axis = 0)]
        if len(vg_slice_final)==0:
            ll_low-=1
            ll_high+=1
            print ("  Caution: load correlation bin "+str(ll)+" expanded due to insufficient data.")
        else:
            return _pdm.create_histogram(vg_slice_final)
        

