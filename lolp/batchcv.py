# -*- coding: utf-8 -*-
"""
Created on Fri Jan 18 10:19:05 2013

@author: ryan
"""

import numpy as _np
import os
import csv as _csv
import copy as _copy
if not __name__ == "__main__":
    import fileio
    import basicm
    import const.constants as const




def marginal_CV(case_data, tunedpsys, m):
    psys = tunedpsys
    
    start_cap_short = psys.cap_short
    m_CV = {}
    
    psys.marginalcvmode = True
    
    if case_data.calculation_settings.reserve_calc_marginal_CV:
        for zone in case_data.vg.profiles.keys():
            for vg_name in case_data.vg.profiles[zone].keys():
                
                print ("Marginal capacity value for "+vg_name)
                
                case_data.interm_calc.saved_bin = _copy.deepcopy(case_data.vg.bins[zone][vg_name])
                case_data.vg.bins[zone][vg_name] = basicm.bindata.hist_time_series_vg(case_data, case_data.vg.profiles[zone][vg_name], case_data.vg.stats[zone][vg_name]['correlation'], case_data.vg.stats[zone][vg_name]['capacity']+case_data.calculation_settings.marginal_CV_step, case_data.vg.stats[zone][vg_name]['weekends'])
                
                psys.update_netload(case_data)
                psys.update_imports(case_data)
                psys.calc_lolp_table()
                psys.tunelolp(case_data)
                
                if case_data.calculation_settings.marginal_CV_calc_method=='Flat load carried' and case_data.calculation_settings.adjust_system_capacity_method=='Generator stack alteration':
                    #This is a special case where the capacity adjust gets double counted without this correction. The true problem lies in powersys in the calc_lolp_table method
                    #The is a temporary fix
                    cv = (start_cap_short-(start_cap_short+psys.cap_short))/case_data.calculation_settings.marginal_CV_step
                else:
                    #This is the normal case
                    cv = (start_cap_short-psys.cap_short)/case_data.calculation_settings.marginal_CV_step                
                
                m_CV[vg_name] = cv
                
                fileio.write_results.add_row_marginalcv(cv, m, zone, vg_name, case_data)
                
                case_data.vg.bins[zone][vg_name] = case_data.interm_calc.saved_bin
    
    if case_data.calculation_settings.run_batch_CV:
        batch_profiles = batch_profile_generator(case_data)
        
        while True:
            try:
                profilename = batch_profiles.next()
                
                psys.update_netload(case_data)
                psys.calc_lolp_table()
                psys.tunelolp(case_data)

                if case_data.calculation_settings.marginal_CV_calc_method=='Flat load carried' and case_data.calculation_settings.adjust_system_capacity_method=='Generator stack alteration':
                    #This is a special case where the capacity adjust gets double counted without this correction. The true problem lies in powersys in the calc_lolp_table method
                    #The is a temporary fix
                    cv = (start_cap_short-(start_cap_short+psys.cap_short))/case_data.vg.stats[case_data.calculation_settings.zone_to_analyze][profilename]['capacity']
                else:
                    #This is the normal case
                    cv = (start_cap_short-psys.cap_short)/case_data.vg.stats[case_data.calculation_settings.zone_to_analyze][profilename]['capacity'] 
                
                m_CV[profilename] = cv
                
                fileio.write_results.add_row_marginalcv(cv, m, case_data.calculation_settings.zone_to_analyze, profilename, case_data)
                    
                del case_data.vg.stats[case_data.calculation_settings.zone_to_analyze][profilename]
                del case_data.vg.bins[case_data.calculation_settings.zone_to_analyze][profilename]
                
            except StopIteration:
                break
    
    return m_CV

def batch_profile_generator(case_data):
    for file_name in os.listdir(const.STARTING_DIRECTORY+"\\profiles\\batch_marginal_capacity_value"):
        if file_name.endswith(".csv"):
            profilename = file_name.rstrip('.csv')
            with open(const.STARTING_DIRECTORY+'\\profiles\\batch_marginal_capacity_value\\'+file_name, 'r') as infile:
                csvreader = _csv.reader(infile, delimiter = ',')              
                header = csvreader.next()

                if len(header)>2 and header[2]=='FALSE':
                    batch_profile_correlation = False
                else:
                    batch_profile_correlation = True

                if len(header)>3 and basicm.pdm.is_strnumeric(header[3]):
                    marginal_CV_step = float(header[3])*case_data.calculation_settings.power_system_scaler
                else:
                    marginal_CV_step = case_data.calculation_settings.marginal_CV_step*(-1 if case_data.calculation_settings.batch_CV_add_or_subtract_vg == 'Subtract marginal profile' else 1)
                
                data = _np.genfromtxt(infile, delimiter = ',')[:,:2]
                profile = basicm.gm.empty_data()
                profile.dates = data[:,0]
                profile.values = data[:,1]
                
                weekends = False
                
                case_data.vg.stats[case_data.calculation_settings.zone_to_analyze][profilename] = {}
                case_data.vg.stats[case_data.calculation_settings.zone_to_analyze][profilename]['PRM accounting'] = 'supply resource'
                case_data.vg.stats[case_data.calculation_settings.zone_to_analyze][profilename]['weekends'] = weekends
                case_data.vg.stats[case_data.calculation_settings.zone_to_analyze][profilename]['capacity'] = marginal_CV_step
                case_data.vg.stats[case_data.calculation_settings.zone_to_analyze][profilename]['correlation'] = batch_profile_correlation
                
                case_data.vg.bins[case_data.calculation_settings.zone_to_analyze][profilename] = basicm.bindata.hist_time_series_vg(case_data, profile, batch_profile_correlation, marginal_CV_step, weekends)
                
                print ("Marginal capacity value for "+profilename)
                yield profilename
