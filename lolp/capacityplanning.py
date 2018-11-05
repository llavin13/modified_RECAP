# -*- coding: utf-8 -*-
"""
Created on Fri Jan 18 10:19:05 2013

@author: ryan
"""

from collections import defaultdict as _defaultdict

if not __name__ == "__main__":
    import fileio
    import lolp.powersys as powersys
    import lolp.batchcv as batchcv
    import lolp.chronological_lolp as chronological_lolp
    import timeseries

def run(case_data):    
    print ("Running capacity planning module")
    fileio.write_results.start_results_cpm(case_data)
    if case_data.calculation_settings.reserve_calc_marginal_CV or case_data.calculation_settings.run_batch_CV:
        fileio.write_results.start_marginalcv(case_data)
    
    results = _defaultdict(dict)
    m_CV = {}
    
    months_to_run = [tuple(range(1,12+1))]+[(m,) for m in range(1,12+1)] if case_data.calculation_settings.monthly_capacity_value else [tuple(range(1,12+1))]
    for m in months_to_run:
        case_data.interm_calc.timeslicelist = [m, range(1,24+1), range(2), range(1, case_data.calculation_settings.numloadlevels+1)]

        psys = powersys.powersystem(case_data, m, include_supply_vg=True, include_demand_vg=True, include_imports=True)
        psys.initialize(case_data)
        results[m]['initial'] = psys.results()
        
        if case_data.calculation_settings.output_intermediate_results:
            savedistributions(psys, case_data)
        
        psys.tunelolp(case_data)
        results[m]['tuned'] = psys.results()
            
        if case_data.calculation_settings.write_dr_input_file and m==tuple(range(1,12+1)):
            chronological_lolp.calc_chronological_lolp(case_data, psys)
        
        if case_data.calculation_settings.reserve_calc_marginal_CV or case_data.calculation_settings.run_batch_CV:
            m_CV[m] = batchcv.marginal_CV(case_data, psys, m)

        if case_data.calculation_settings.target_PRM:
            psys = powersys.powersystem(case_data, m, include_supply_vg=False, include_demand_vg=False, include_imports=False)
            psys.initialize(case_data)
            psys.tunelolp(case_data)
            results[m]['no dvg, svg, imports'] = psys.results()
            
            psys.include_imports = True
            psys.update_imports(case_data)
            psys.calc_lolp_table()
            psys.tunelolp(case_data)
            results[m]['no dvg, svg'] = psys.results()
            
            psys.include_demand_vg = True
            psys.update_netload(case_data)
            psys.update_imports(case_data)
            psys.calc_lolp_table()
            psys.tunelolp(case_data)
            results[m]['no svg'] = psys.results()
        
        fileio.write_results.add_row_cpm(results[m], m, case_data)
        
    fileio.write_results.write_month_hour_tables(results, case_data)
    
    return results, m_CV


def savedistributions(psys, case_data):
    print (" Saving distributions...")
    print ("  variable generation")    
    vg = timeseries.vargen.vg_supply(case_data, case_data.calculation_settings.zone_to_analyze, include_supply_vg = True, include_demand_vg = True)
    itersavedist(vg, 'variablegen', case_data)
    print ("  gross load") 
    itersavedist(case_data.load.bins[case_data.calculation_settings.zone_to_analyze], 'load', case_data)
    
    for dist in ['netload', 'gen', 'import_capability', 'netgen']:
        print ("  "+dist)
        itersavedist(getattr(psys, dist), dist, case_data)

def itersavedist(distdict, disttype, case_data):
    for key in distdict:
        fileio.write_results.savedistribution(distdict[key], key, disttype, case_data)


