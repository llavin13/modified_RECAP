# -*- coding: utf-8 -*-
"""
Created on Sun Oct 06 16:45:32 2013

@author: ryan
"""

import numpy as _np
import csv as _csv
import const.constants as const
import basicm

def calculation_settings(case):
    calculation_settings = basicm.gm.empty_data()
    with open(const.STARTING_DIRECTORY+'\\cases\\'+case+'\\inputs\\calculation_settings.csv', 'r') as readfile:
        csvreader = _csv.reader(readfile, delimiter = ',')
        for row in csvreader:
            if basicm.gm.isnumeric(row[1]):
                setattr(calculation_settings, row[0], float(row[1]))
            elif row[1]=='TRUE' or row[1]=='True':
                setattr(calculation_settings, row[0], True)
            elif row[1]=='FALSE' or row[1]=='False':
                setattr(calculation_settings, row[0], False)
            else:
                setattr(calculation_settings, row[0], row[1])
    
    calculation_settings.marginal_CV_step*= calculation_settings.power_system_scaler
    calculation_settings.simultaneous_import_limit*= calculation_settings.power_system_scaler
    
    return calculation_settings

def cv_table_shape(case, calculation_settings):
    CV_table_shape = {}
    
    with open(const.STARTING_DIRECTORY+'\\cases\\'+case+'\\inputs\\cv_table_shape.csv', 'r') as readfile:
        csvreader = _csv.reader(readfile, delimiter = ',')
        #header = csvreader.next()
        header = next(csvreader)
        ind1, ind2, ind3, ind4 = header.index('profile_name'), header.index('start'), header.index('step'), header.index('stop')
        for row in csvreader:
            CV_table_shape[row[ind1]] = {}
            CV_table_shape[row[ind1]]['start'] = float(row[ind2])*calculation_settings.power_system_scaler
            CV_table_shape[row[ind1]]['step'] = float(row[ind3])*calculation_settings.power_system_scaler
            CV_table_shape[row[ind1]]['stop'] = float(row[ind4])*calculation_settings.power_system_scaler
            
    return CV_table_shape

def correlation_bins(case):
    load_bins = {}
    with open(const.STARTING_DIRECTORY+'\\cases\\'+case+'\\inputs\\load_correlation_bins.csv', 'r') as readfile:
        csvreader = _csv.reader(readfile, delimiter = ',')
        #csvreader.next()
        next(csvreader)
        
        num = 1
        #last_row = csvreader.next()
        last_row = next(csvreader)
        for next_row in csvreader:
            load_bins[num] = float(last_row[1])*100, float(next_row[1])*100
            last_row = next_row
            num+=1
    return load_bins


def read_a_profile(profile_name, case):
    profile = basicm.gm.empty_data()
    profile.dates, profile.values = _np.genfromtxt(const.STARTING_DIRECTORY+'\\cases\\'+case+'\\inputs\\profiles\\'+profile_name+'.csv', delimiter = ',', skip_header = 1).T
    
    not_nan = ~_np.isnan(profile.values)
    profile.values = profile.values[not_nan]
    profile.dates = profile.dates[not_nan]
    
    return profile


def load_profile_stats(case_data):
    case = case_data.current_case_name
    profile_stats = {}
    
    with open(const.STARTING_DIRECTORY+'\\cases\\'+case+'\\inputs\\load_profile_settings.csv', 'r') as readfile:
        csvreader = _csv.reader(readfile, delimiter = ',')
        #header = csvreader.next()
        header = next(csvreader)
        ind1, ind2, ind3, ind4 = header.index('profile_name'), header.index('zone'), header.index('energy'), header.index('peak')
        for row in csvreader:
            #if not profile_stats.has_key(row[ind2]):
            if row[ind2] not in profile_stats:
                profile_stats[row[ind2]] = {}
            profile_stats[row[ind2]]['name'] = row[ind1]
            profile_stats[row[ind2]]['energy'] = float(row[ind3])*case_data.calculation_settings.power_system_scaler
            profile_stats[row[ind2]]['peak']  = float(row[ind4])*case_data.calculation_settings.power_system_scaler
    
    return profile_stats
    
def vg_profile_stats(case_data):
    profile_stats = {}
    
    with open(const.STARTING_DIRECTORY+'\\cases\\'+case_data.current_case_name+'\\inputs\\vg_profile_settings.csv', 'r') as readfile:
        csvreader = _csv.reader(readfile, delimiter = ',')
        #header = csvreader.next()
        header = next(csvreader)
        ind1, ind2, ind3, ind4, ind5, ind6, ind7 = header.index('profile_name'), header.index('zone'), header.index('capacity'), header.index('correlation'), header.index('weekends'), header.index('include'), header.index('PRM accounting')
        for row in csvreader:
            if not bool(int(row[ind6])):
                continue
            #if not profile_stats.has_key(row[ind2]):
            if row[ind2] not in profile_stats:
                profile_stats[row[ind2]] = {}
            profile_stats[row[ind2]][row[ind1]] = {}
            profile_stats[row[ind2]][row[ind1]]['capacity'] = float(row[ind3])*case_data.calculation_settings.power_system_scaler
            profile_stats[row[ind2]][row[ind1]]['PRM accounting'] = row[ind7]
            profile_stats[row[ind2]][row[ind1]]['correlation']  = True if row[ind4].upper()=='TRUE' else False
            profile_stats[row[ind2]][row[ind1]]['weekends']  = True if row[ind5].upper()=='TRUE' else False
    return profile_stats


