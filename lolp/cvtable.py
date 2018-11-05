# -*- coding: utf-8 -*-
"""
Created on Tue Feb 26 13:32:34 2013

@author: ryan
"""

import numpy as _np
import copy as _copy

if not __name__ == "__main__":
    import basicm
    import fileio
    import lolp.powersys as powersys

def capacity_energy_penetration_row(case_data, capacities):
    capacties_row = [c/case_data.calculation_settings.power_system_scaler for c in capacities]
    energy_row = [vg_average_annual_energy(case_data, vg_name)*capacity/case_data.calculation_settings.power_system_scaler for vg_name, capacity in zip(case_data.calculation_settings.CV_table_shape.keys(), capacities)]
    penetration_row = [e/(case_data.load.stats[case_data.calculation_settings.zone_to_analyze]['energy']/case_data.calculation_settings.power_system_scaler) for e in energy_row]
    return capacties_row+energy_row+penetration_row


def update_capacity(case_data, capacities):
    for vg_name, capacity in zip(case_data.calculation_settings.CV_table_shape.keys(), capacities):
        for zone in case_data.vg.stats.keys():
            if case_data.vg.profiles[zone].has_key(vg_name): 
                case_data.vg.stats[zone][vg_name]['capacity'] = capacity
                case_data.vg.bins[zone][vg_name] = basicm.bindata.hist_time_series_vg(case_data, case_data.vg.profiles[zone][vg_name], case_data.vg.stats[zone][vg_name]['correlation'], case_data.vg.stats[zone][vg_name]['capacity'], case_data.vg.stats[zone][vg_name]['weekends'])

def return_penetration(case_data, capacities):
    total_energy = 0
    for vg_name, capacity in zip(case_data.calculation_settings.CV_table_shape.keys(), capacities):
        total_energy+= vg_average_annual_energy(case_data, vg_name)*capacity
    return total_energy/case_data.load.stats[case_data.calculation_settings.zone_to_analyze]['energy']

def capacities_list(case_data, vg_name):
    if case_data.calculation_settings.CV_table_delineation=='Penetration by Energy':
        vg_energy = vg_average_annual_energy(case_data, vg_name)
        
        annual_energy = case_data.load.stats[case_data.calculation_settings.zone_to_analyze]['energy']
        
        start = round(annual_energy*case_data.calculation_settings.CV_table_shape[vg_name]['start']/vg_energy,1)
        stop = round(annual_energy*case_data.calculation_settings.CV_table_shape[vg_name]['stop']/vg_energy,1)
        step = round(annual_energy*case_data.calculation_settings.CV_table_shape[vg_name]['step']/vg_energy,1)
    elif case_data.calculation_settings.CV_table_delineation=='Installed Capacity':
        start = round(case_data.calculation_settings.CV_table_shape[vg_name]['start'],1)
        stop = round(case_data.calculation_settings.CV_table_shape[vg_name]['stop'],1)
        step = round(case_data.calculation_settings.CV_table_shape[vg_name]['step'],1)
    
    if start==0 and stop==0:
        return _np.array([0], dtype = float)
    elif step==0:
        return _np.array([start], dtype = float)
    else:
        return _np.arange(start, stop+step/2., step, dtype = float)

def vg_average_annual_energy(case_data, vg_name):
    for zone in case_data.vg.profiles.keys():
        if case_data.vg.profiles[zone].has_key(vg_name):
            return _np.mean(case_data.vg.profiles[zone][vg_name].values)*8766

def zero_vg_capacity(case_data):
    for zone in case_data.vg.stats.keys():
        for vg_name in case_data.vg.stats[zone].keys():
            case_data.vg.stats[zone][vg_name]['capacity'] = 0.0
            case_data.vg.bins[zone][vg_name] = basicm.bindata.hist_time_series_vg(case_data, case_data.vg.profiles[zone][vg_name], case_data.vg.stats[zone][vg_name]['correlation'], case_data.vg.stats[zone][vg_name]['capacity'], case_data.vg.stats[zone][vg_name]['weekends'])

def create_output_files(case_data):
    fileio.write_results.start_capacity_value_table_file(case_data)
    fileio.write_results.start_runs_completed(case_data)


def test_to_continue(case_data):
    try:
        completed_runs = fileio.write_results.completed_runs(case_data)
    except IOError:
        create_output_files(case_data)
        return True
    
    index_combinations = basicm.gm.combination([capacities_list(case_data, vg_name) for vg_name in case_data.calculation_settings.CV_table_shape.keys()])
    try:
        capacities = index_combinations.next()
        while str(capacities) in completed_runs:
            capacities = index_combinations.next()
        return True
    except StopIteration:
        should_we_continue = raw_input("Capacity value table appears complete, are you sure you want to recalculate? (y/n)")
        if should_we_continue.lower()=='y':
            create_output_files(case_data)
            return True
        else:
            return False

def run(case_data):
    if test_to_continue(case_data):
        zero_vg_capacity(case_data)
        months_to_run = [tuple(range(1,12+1))]+[(m,) for m in range(1,12+1)] if case_data.calculation_settings.monthly_capacity_value else [tuple(range(1,12+1))]
        
        no_renewables_system_capacity = {}
        for m in months_to_run:
            case_data.interm_calc.timeslicelist = [m, range(1,24+1), range(2), range(1, case_data.calculation_settings.numloadlevels+1)]
            psys = powersys.powersystem(case_data, m, include_supply_vg=False, include_demand_vg=False, include_imports=True)
            psys.initialize(case_data)
            psys.tunelolp(case_data)
            no_renewables_system_capacity[m] = psys.cap_short
        
        if case_data.calculation_settings.output_gen_stack_changes:
            fileio.write_results.start_gen_stack_change_file(case_data)

        index_combinations = basicm.gm.combination([capacities_list(case_data, vg_name) for vg_name in case_data.calculation_settings.CV_table_shape.keys()])
        try:
            while True:
                capacities = index_combinations.next()
                if sum(capacities)==0 and not case_data.calculation_settings.true_marginal_CV:
                    continue
                
                completed_runs = fileio.write_results.completed_runs(case_data)
                while str(capacities) in completed_runs:
                    capacities = index_combinations.next()
                
                fileio.write_results.update_runs_completed(case_data, capacities)
                
                if case_data.calculation_settings.CV_table_maximum_penetration and return_penetration(case_data, capacities)>(case_data.calculation_settings.CV_table_maximum_penetration+0.001):
                    continue #tests to see if the penetration is greater maximum penetration target
                
                print ("Starting run for " + str(zip(case_data.calculation_settings.CV_table_shape.keys(),[c/case_data.calculation_settings.power_system_scaler for c in capacities])))
                update_capacity(case_data, capacities)
                
            
                for m in months_to_run:
                    case_data.interm_calc.timeslicelist = [m, range(1,24+1), range(2), range(1, case_data.calculation_settings.numloadlevels+1)]
                    psys = powersys.powersystem(case_data, m, include_supply_vg=True, include_demand_vg=True, include_imports=True)
                    psys.initialize(case_data)
                    psys.tunelolp(case_data)
                    
                    if sum(capacities):
                        cv = (no_renewables_system_capacity[m]-psys.cap_short)/sum(capacities)
                    else:
                        cv = 0.
                    
                    fileio.write_results.append_rows_capacity_value_table_file(case_data, [cv, 'average', m]+capacity_energy_penetration_row(case_data, capacities))
                    
                    if case_data.calculation_settings.output_gen_stack_changes:
                        fileio.write_results.append_row_gen_stack_change_file(case_data, capacity_energy_penetration_row(case_data, capacities))
                    
                    if case_data.calculation_settings.true_marginal_CV:
                        marginal_CV(case_data, psys, m, capacities)
     
        except StopIteration:
            pass

def marginal_CV(case_data, tunedpsys, m, capacities):
    psys = tunedpsys
    
    start_cap_short = psys.cap_short
    
    psys.marginalcvmode = True
    
    for vg_name, starting_capacity in zip(case_data.calculation_settings.CV_table_shape.keys(), capacities):
        zone = [z for z in case_data.vg.profiles.keys() if vg_name in case_data.vg.profiles[z]][0]
        
        print ("Calculating marginal capacity value for "+vg_name)
        
        # Deep copy
        case_data.interm_calc.saved_bin = _copy.deepcopy(case_data.vg.bins[zone][vg_name])
        case_data.vg.bins[zone][vg_name] = basicm.bindata.hist_time_series_vg(case_data, case_data.vg.profiles[zone][vg_name],
                                                                              case_data.vg.stats[zone][vg_name]['correlation'],
                                                                              starting_capacity+case_data.calculation_settings.marginal_CV_step,
                                                                              case_data.vg.stats[zone][vg_name]['weekends'])
        
        psys.update_netload(case_data)
        psys.update_imports(case_data) #Necessary if the profile is outside of the primary zone
            
        psys.calc_lolp_table()
        
        psys.tunelolp(case_data)
        if case_data.calculation_settings.marginal_CV_calc_method=='Flat load carried' and case_data.calculation_settings.adjust_system_capacity_method=='Generator stack alteration':
            #This is a special case where the capacity adjust gets double counted without this correction. The true problem lies in powersys in the calc_lolp_table method
            #The is a temporary fix
            cv = (start_cap_short-(start_cap_short+psys.cap_short))/case_data.calculation_settings.marginal_CV_step
        else:
            #This is the normal case
            cv = (start_cap_short-psys.cap_short)/case_data.calculation_settings.marginal_CV_step
        
        print ("Marginal capacity value for "+ vg_name + " = " + str(round(cv*100,1)) + "%")
        print ("")
        
        fileio.write_results.append_rows_capacity_value_table_file(case_data, [cv, 'marginal '+vg_name, m]+capacity_energy_penetration_row(case_data, capacities))
        
        # Grab deep copy
        case_data.vg.bins[zone][vg_name] = case_data.interm_calc.saved_bin
    
    psys.marginalcvmode = False





#def marginal_CV(case_data, tunedpsys, m, capacities):
#    psys = tunedpsys
#    
#    start_cap_short = psys.cap_short
#    
#    psys.marginalcvmode = True
#    
#    for vg_name, starting_capacity in zip(case_data.calculation_settings.CV_table_shape.keys(), capacities):
#        for zone in case_data.vg.profiles.keys():
#            if case_data.vg.profiles[zone].has_key(vg_name):
#                
#                print "Marginal capacity value for "+vg_name
#                
#                case_data.interm_calc.saved_bin = _copy.deepcopy(case_data.vg.bins[zone][vg_name])
#                case_data.vg.bins[zone][vg_name] = basicm.bindata.hist_time_series_vg(case_data, case_data.vg.profiles[zone][vg_name], case_data.vg.stats[zone][vg_name]['correlation'], starting_capacity+case_data.calculation_settings.marginal_CV_step, case_data.vg.stats[zone][vg_name]['weekends'])
#                
#                psys.update_netload(case_data)
#                psys.update_imports(case_data) #Necessary if the profile is outside of the primary zone
#                psys.calc_lolp_table()
#                
#                psys.tunelolp(case_data)
#                cv = (start_cap_short-psys.cap_short)/case_data.calculation_settings.marginal_CV_step
#                
#                print "Marginal capacity value for "+ vg_name + " = " + str(round(cv*100,1)) + "%"
#                print ""
#                
#                fileio.write_results.append_rows_capacity_value_table_file(case_data, [cv, 'marginal '+vg_name, m]+capacity_energy_penetration_row(case_data, capacities))
#                
#                case_data.vg.bins[zone][vg_name] = case_data.interm_calc.saved_bin
