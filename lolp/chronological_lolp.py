# -*- coding: utf-8 -*-
"""
Created on Sun Jan 06 22:20:53 2013

@author: Ryan Jones - Ryan.Jones@ethree.com
"""
import numpy as _np
import csv as _csv
import time

if not __name__ == "__main__":
    import const.constants as const
    import basicm as _basicm
    import timeseries as _timeseries

def calc_chronological_lolp(case_data, psys):

    vg = _timeseries.vargen.vg_supply(case_data, psys.zone, include_supply_vg = True, include_demand_vg = True)
    supply = vg_supply_for_chron_lolp(case_data, psys, vg, include_supply_vg = True, include_demand_vg = True)
    avevg = average_vg(case_data, vg)
    
    relevant_calendar = _basicm.gm.relevant_calendar_long(case_data.load.profile.dates)[:,1:]
    hourly_lolp = []
    year = int(const.CALENDARlong[const.CALENDARlong[:,0]==min(case_data.load.profile.dates)][0][1])
    i = 0
    a = time.time()
    
    for (m,dt,h), ll, load in zip(relevant_calendar, case_data.interm_calc.load_bin_calendar[:,1], case_data.load.profile.values):
        
        temp = [load/case_data.calculation_settings.power_system_scaler, avevg[m,h,dt,ll]]

        if round(load)<=min(supply[m,h,dt,ll][:,0]):
            hourly_lolp.append(temp+[0.0])
        elif round(load)>max(supply[m,h,dt,ll][:,0]):
            hourly_lolp.append(temp+[1.0])
        else:
            hourly_lolp.append(temp+[supply[m,h,dt,ll][_np.nonzero(supply[m,h,dt,ll][:,0]==round(load))[0]-1,1][0]])
        
        i+=1
        if not i%8766:
            print (year, time.time()-a)
            #print("secs to run")
            a = time.time()
            year+=1
    
    write_chronological_lolp(hourly_lolp, case_data.current_case_name)

def vg_supply_for_chron_lolp(case_data, psys, vg, include_supply_vg = True, include_demand_vg = True):
    supply = {}

    for key in _basicm.gm.combination(case_data.interm_calc.timeslicelist):
        supply[key] = _basicm.pdm.fft_convolution(_basicm.pdm.fft_convolution(psys.gen[key], psys.import_capability[key], '+'), vg[key], '+')
        if psys.flatloadcarried:
            supply[key][:,0]+=round(psys.cap_short)
        supply[key][:,1] = _np.cumsum(supply[key][:,1])
    return supply

def average_vg(case_data, vg):
    avevg = {}
    for key in _basicm.gm.combination(case_data.interm_calc.timeslicelist):
        avevg[key] = _np.dot(vg[key][:,0], vg[key][:,1])/case_data.calculation_settings.power_system_scaler
    return avevg
    
    
def write_chronological_lolp(hourly_lolp, current_case_name):
    with open(const.STARTING_DIRECTORY+'\\cases\\'+current_case_name+'\\outputs\\chronological_lolp.csv', 'w') as outfile:
        writer = _csv.writer(outfile, delimiter=',',lineterminator = '\n')
        writer.writerow(['Load MW','Mean variable generation MW','hourly LOLP'])
        for row in hourly_lolp:
            writer.writerow(row)
