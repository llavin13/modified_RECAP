# -*- coding: utf-8 -*-
"""
Created on Fri Jan 04 11:13:13 2013

@author: Ryan Jones - Ryan.Jones@ethree.com
"""

import numpy as _np
import csv as _csv
import const.constants as const
import basicm


def run_create_normal_or_gumbel(bins, case_data, minimum_load):
    mean_or_location = [_np.zeros((24,12)), _np.zeros((24,12))]
    std_or_scale = [_np.zeros((24,12)), _np.zeros((24,12))]
    distribution_type = _np.empty((2,24,12), dtype = 'S6')
    
    load_bins = case_data.calculation_settings.load_bins
    fraction_which_matters_for_fit = case_data.calculation_settings.fraction_which_matters_for_fit
    distribution_std_cutoff = case_data.calculation_settings.distribution_std_cutoff
    load_distribution_type = case_data.calculation_settings.load_distribution_type
    
    for day_type in basicm.gm.combination([range(1,13), range(1,25), range(2)]):
        combined_load_bins = []
        for i in load_bins.keys():
            combined_load_bins+=list(bins[day_type+(i,)])
        distribution_spec = basicm.pdm.normal_or_gumbel(combined_load_bins, fraction_which_matters_for_fit)
        mean_or_location[day_type[2]][day_type[1]-1][day_type[0]-1], std_or_scale[day_type[2]][day_type[1]-1][day_type[0]-1], distribution_type[day_type[2]][day_type[1]-1][day_type[0]-1] = distribution_spec
        
        arg = (distribution_spec[0],distribution_spec[1], distribution_std_cutoff, (min(combined_load_bins), max(combined_load_bins)))
        
        if distribution_spec[2]=='normal' or load_distribution_type == 'Normal Distribution':
            distribution = basicm.pdm.create_normal_pdf(arg[0],arg[1],arg[2],arg[3])
        else:
            distribution = basicm.pdm.create_gumbel_pdf(arg[0],arg[1],arg[2],arg[3])
               
        cumdist = _np.cumsum(distribution[:,1])*100
        for i in load_bins.keys():
            bins[day_type+(i,)] = distribution[_np.all(_np.vstack((cumdist>load_bins[i][0], cumdist<=load_bins[i][1])), axis = 0)]
            
            if bins[day_type+(i,)][-1,0]<minimum_load:
                bins[day_type+(i,)] = _np.array([[bins[day_type+(i,)][-1,0], sum(bins[day_type+(i,)][:,1])]])
            else:
                presum = sum(bins[day_type+(i,)][:,1])
                bins[day_type+(i,)] = bins[day_type+(i,)][bins[day_type+(i,)][:,0]>=minimum_load]
                bins[day_type+(i,)][0,1]+=(presum-sum(bins[day_type+(i,)][:,1]))
            
    with open(const.STARTING_DIRECTORY+'\\cases\\'+case_data.current_case_name+'\\outputs\\gross_load_distribution_stats.csv', 'w') as outfile:
        writer = _csv.writer(outfile, delimiter=',',lineterminator = '\n')
        for table in [('mean_or_location_weekday',mean_or_location[0]), ('std_or_scale_weekday',std_or_scale[0]), ('mean_or_location_weekend',mean_or_location[1]), ('std_or_scale_weekend',std_or_scale[1])]:
            writer.writerow([table[0],'jan', 'feb', 'mar', 'apr', 'may', 'jun', 'jul', 'aug', 'sep', 'oct', 'nov', 'dec'])
            _np.savetxt(outfile,_np.vstack((_np.arange(1,25),(table[1].T)/case_data.calculation_settings.power_system_scaler/(1+case_data.calculation_settings.operating_reserves_up))).T, delimiter = ',')
    with open(const.STARTING_DIRECTORY+'\\cases\\'+case_data.current_case_name+'\\outputs\\gross_load_distribution_types.csv', 'w') as outfile:
        writer = _csv.writer(outfile, delimiter=',',lineterminator = '\n')
        for daytype in zip(distribution_type, ['weekday', 'weekend']):
            writer.writerow([daytype[1],'jan', 'feb', 'mar', 'apr', 'may', 'jun', 'jul', 'aug', 'sep', 'oct', 'nov', 'dec'])
            hour = 1
            for row in daytype[0]:
                writer.writerow([hour]+list(row))
                hour+=1
    
    return bins


def run_create_raw_hist(bins, case_data, minimum_load):
    load_bins = case_data.calculation_settings.load_bins
    for item in bins.iteritems():
        bins[item[0]] = basicm.pdm.create_histogram(item[1])
        bins[item[0]][:,1]*=(_np.diff(load_bins[item[0][-1]])/100.)
    return bins
