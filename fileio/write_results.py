# -*- coding: utf-8 -*-
"""
Created on Thu Jan 24 11:43:19 2013

@author: ryan
"""
import csv as _csv
import numpy as _np
import os as _os
import time as _time
if not __name__ == "__main__":
    import const.constants as const

def savedistribution(dist, key, disttype, case_data):
    path = const.STARTING_DIRECTORY+'\\cases\\'+case_data.current_case_name+'\\outputs\\distributions\\'
    if not _os.path.exists(path):
        _os.makedirs(path)
    
    dayofweek = "Weekend" if key[2]==1 else "Weekday"
    file_name = "M"+str(key[0])+"_HE"+str(key[1])+"_"+dayofweek+"_LoadLevel"+str(key[3])+"_"+disttype
    
    with open(path+file_name+'.csv', 'w') as outfile:
        writer = _csv.writer(outfile, delimiter=',',lineterminator = '\n')
        writer.writerow(['(MW)', 'probability'])
        for row in dist:
            writer.writerow([row[0]/case_data.calculation_settings.power_system_scaler, row[1]])


def write_batch_capacity_value(list_of_results, case_data):
    with open(case_data.case_settings.batch_CV_folder+'\\results\\'+case_data.current_case_name+'_batch_capacity_value_results.csv', 'w') as outfile:
        csvwriter = _csv.writer(outfile, delimiter = ',')
        csvwriter.writerow(['file name', 'capacity value'])
        for row in list_of_results:
            csvwriter.writerow(row)

def start_results_cpm(case_data):
    with open(const.STARTING_DIRECTORY+'\\cases\\'+case_data.current_case_name+'\\outputs\\reliability statistics.csv', 'w') as outfile:
        writer = _csv.writer(outfile, delimiter=',',lineterminator = '\n')
        if case_data.calculation_settings.target_PRM:
            writer.writerow(['month',
                             '1-2 peak load', 
                             'PRM calculation month',
                             'generation resources',
                             'max imports (excluding variable generation)',
                             'Capacity value of variable generation (including imported variable generation)',
                             'total supply',
                             'PRM',
                             'target PRM',
                             'capacity shortage',
                             'starting LOLE',
                             'starting ALOLP',
                             'starting EUE',
                             'starting EUE Normalized',
                             'final LOLE',
                             'final ALOLP',
                             'final EUE',
                             'final EUE Normed',
                             'Capacity value of demand side variable generation',
                             'Capacity value of supply side variable generation',
                             'Capacity value of imports (excluding variable generation)'])
        else:
            writer.writerow(['month',
                             '1-2 peak load',
                             'capacity shortage',
                             'starting LOLE',
                             'starting ALOLP',
                             'starting EUE',
                             'starting EUE Normalized',
                             'final LOLE',
                             'final ALOLP',
                             'final EUE',
                             'final EUE Normed'])

def add_row_cpm(results, rowname, case_data):
    with open(const.STARTING_DIRECTORY+'\\cases\\'+case_data.current_case_name+'\\outputs\\reliability statistics.csv', 'a') as outfile:
        writer = _csv.writer(outfile, delimiter=',',lineterminator = '\n')
        if case_data.calculation_settings.target_PRM:
            imp_cv = results['no dvg, svg, imports']['cap_short'] - results['no dvg, svg']['cap_short']
            dvg_cv = results['no dvg, svg']['cap_short'] - results['no svg']['cap_short']
            svg_cv = results['no svg']['cap_short'] - results['tuned']['cap_short']
            vg_cv = dvg_cv + svg_cv
            
#            dvg_cv = results['no dvg, svg, imports']['cap_short'] - results['no svg, imports']['cap_short']
#            svg_cv = results['no svg, imports']['cap_short'] - results['no imports']['cap_short']
#            imp_cv = results['no imports']['cap_short'] - results['tuned']['cap_short']
#            vg_cv = dvg_cv + svg_cv
            
            writer.writerow([const.MONTH_WRITE_DICT[rowname],
                             results['initial']['1-2 peak load'],
                             results['initial']['prmcalcslice'][0],
                             results['initial']['max_gen'],
                             results['no dvg, svg']['max_imports'],
                             vg_cv,
                             results['initial']['max_gen']+results['no dvg, svg']['max_imports']+vg_cv,
                             (results['initial']['max_gen']+results['no dvg, svg']['max_imports']+vg_cv)/results['initial']['1-2 peak load'] - 1,
                             (results['initial']['max_gen']+results['no dvg, svg']['max_imports']+vg_cv+results['tuned']['cap_short'])/results['initial']['1-2 peak load'] - 1,
                             results['tuned']['cap_short'],
                             results['initial']['LOLE'], results['initial']['ALOLP'], results['initial']['EUE'], results['initial']['EUENORM'],
                             results['tuned']['LOLE'], results['tuned']['ALOLP'], results['tuned']['EUE'], results['tuned']['EUENORM'],
                             dvg_cv, svg_cv, imp_cv
                             ])
        else:
            writer.writerow([const.MONTH_WRITE_DICT[rowname],
                             results['initial']['1-2 peak load'],
                             results['tuned']['cap_short'],
                             results['initial']['LOLE'], results['initial']['ALOLP'], results['initial']['EUE'], results['initial']['EUENORM'],
                             results['tuned']['LOLE'], results['tuned']['ALOLP'], results['tuned']['EUE'], results['tuned']['EUENORM'],
                             ])


def add_row_marginalcv(cv, m, zone, vg_name, case_data):
    path = const.STARTING_DIRECTORY+'\\cases\\'+case_data.current_case_name+'\\outputs\\capacityvalue\\'
    
    with open(path+'marginal_capacity_value.csv', 'a') as outfile:
        writer = _csv.writer(outfile, delimiter=',',lineterminator = '\n')
        writer.writerow([zone, vg_name, const.MONTH_WRITE_DICT[m], cv])


def start_marginalcv(case_data):
    path = const.STARTING_DIRECTORY+'\\cases\\'+case_data.current_case_name+'\\outputs\\capacityvalue\\'
    if not _os.path.exists(path):
        _os.makedirs(path)
        
    with open(path+'marginal_capacity_value.csv', 'w') as outfile:
        writer = _csv.writer(outfile, delimiter=',',lineterminator = '\n')
        writer.writerow(['zone','profile name','months','capacity value (%)'])

def write_month_hour_tables(results, case_data):
    path = const.STARTING_DIRECTORY+'\\cases\\'+case_data.current_case_name+'\\outputs\\month_hour_tables\\'
    if not _os.path.exists(path):
        _os.makedirs(path)
    
    filenames = [' at current reliability', ' at target reliability', ' at target reliability LOAD ONLY'] if case_data.calculation_settings.target_PRM else [' at current reliability', ' at target reliability']
    resultnames = ['initial', 'tuned', 'no dvg, svg, imports'] if case_data.calculation_settings.target_PRM else ['initial', 'tuned']
    for filename, resultname in zip(filenames, resultnames):
        write_table(path, "lolp table"+filename, results[tuple(range(1,12+1))][resultname]['lolp_table'])
        write_table(path, "eue table"+filename, results[tuple(range(1,12+1))][resultname]['eue_table'])
        
        if case_data.calculation_settings.monthly_capacity_value:
            lolp_table, eue_table = _np.zeros((2,24,12)), _np.zeros((2,24,12))
            for m in range(1,12+1):
                lolp_table+=results[m,][resultname]['lolp_table']
                eue_table+=results[m,][resultname]['eue_table']
            
            write_table(path, "lolp table"+filename+" (month-by-month calculation)", lolp_table)
            write_table(path, "eue table"+filename+" (month-by-month calculation)", eue_table)

def write_table(path, file_name, lolp_table):
    weekday_lolp, weekend_lolp = lolp_table
    with open(path+file_name+'.csv', 'w') as outfile:
        writer = _csv.writer(outfile, delimiter=',',lineterminator = '\n')
        for lolp, daytype in [(weekday_lolp, 'weekday'), (weekend_lolp, 'weekend')]:
            writer.writerow([daytype,'jan', 'feb', 'mar', 'apr', 'may', 'jun', 'jul', 'aug', 'sep', 'oct', 'nov', 'dec'])
            for i, row in enumerate(lolp):
                writer.writerow([i+1]+list(row))

def start_capacity_value_table_file(case_data):
    with open(const.STARTING_DIRECTORY+'\\cases\\'+case_data.current_case_name+'\\outputs\\capacity_value_table.csv', 'w') as outfile:
        writer = _csv.writer(outfile, delimiter=',',lineterminator = '\n')
        writer.writerow(['Capacity Value Table'])
        writer.writerow(['Method for adjusting system capacity',case_data.calculation_settings.adjust_system_capacity_method])
        writer.writerow(['Method for determing marginal capacity value',case_data.calculation_settings.marginal_CV_calc_method])
        writer.writerow(['', 'start', 'step', 'stop'])
        for vg in case_data.calculation_settings.CV_table_shape.keys():
            writer.writerow([vg]+[case_data.calculation_settings.CV_table_shape[vg][t]/case_data.calculation_settings.power_system_scaler for t in ['start', 'step', 'stop']])
        writer.writerow(['capacity value (%)','capacity value type (average or marginal)', 'month']+
                        [vg+' capacity (MW)' for vg in case_data.calculation_settings.CV_table_shape.keys()]+
                        [vg+' energy (MWh)' for vg in case_data.calculation_settings.CV_table_shape.keys()]+
                        [vg+' penetration by energy (%)' for vg in case_data.calculation_settings.CV_table_shape.keys()])

def append_rows_capacity_value_table_file(case_data, row):
    while True:
        try:
            with open(const.STARTING_DIRECTORY+'\\cases\\'+case_data.current_case_name+'\\outputs\\capacity_value_table.csv', 'a') as outfile:
                writer = _csv.writer(outfile, delimiter=',',lineterminator = '\n')
                writer.writerow(row)
            break
        except:
            raw_input("Close capacity value table file and press enter to continue")

def start_gen_stack_change_file(case_data):
    with open(const.STARTING_DIRECTORY+'\\cases\\'+case_data.current_case_name+'\\outputs\\generator_stack_change_record.csv', 'w') as outfile:
        writer = _csv.writer(outfile, delimiter=',',lineterminator = '\n')
        
        unit_retirement = case_data.gendata.retire
        unit_names = case_data.gendata.names
        unit_capacity = [max(c)/case_data.calculation_settings.power_system_scaler for c in zip(*case_data.gendata.cap.values())]
        
        sort_order = _np.argsort(case_data.gendata.retire)[-1::-1]
        
        writer.writerow(['Records the changes to the generator stack for points in the capacity value table']+['']*(len(case_data.calculation_settings.CV_table_shape.keys())*3-2)+['Retirement order']+[unit_retirement[i] for i in sort_order])
        writer.writerow(['']*(len(case_data.calculation_settings.CV_table_shape.keys())*3-1)+['Generator name']+[unit_names[i] for i in sort_order])
        writer.writerow(['']*(len(case_data.calculation_settings.CV_table_shape.keys())*3-1)+['Generator capacity']+[unit_capacity[i] for i in sort_order])
        writer.writerow([vg+' capacity (MW)' for vg in case_data.calculation_settings.CV_table_shape.keys()]+
                        [vg+' energy (MWh)' for vg in case_data.calculation_settings.CV_table_shape.keys()]+
                        [vg+' penetration by energy (%)' for vg in case_data.calculation_settings.CV_table_shape.keys()])
     
def append_row_gen_stack_change_file(case_data, vg_discription):
    sort_order = _np.argsort(case_data.gendata.retire)[-1::-1]
    derates = [case_data.gendata.derate[i] for i in sort_order]
    
    while True:
        try:
            with open(const.STARTING_DIRECTORY+'\\cases\\'+case_data.current_case_name+'\\outputs\\generator_stack_change_record.csv', 'a') as outfile:
                writer = _csv.writer(outfile, delimiter=',',lineterminator = '\n')
                writer.writerow(vg_discription+derates)                  
            break
        except:
            raw_input("Close generator stack change file and press enter to continue")

def start_runs_completed(case_data):
    with open(const.STARTING_DIRECTORY+'\\cases\\'+case_data.current_case_name+'\\outputs\\capacity_value_table_temp.csv', 'w') as outfile:
        pass

def completed_runs(case_data):
    completed = []
    with open(const.STARTING_DIRECTORY+'\\cases\\'+case_data.current_case_name+'\\outputs\\capacity_value_table_temp.csv', 'r') as infile:
        reader = _csv.reader(infile, delimiter=',')
        for row in reader:
            completed.append(row[0])
    return completed

def update_runs_completed(case_data, capacities):
    with open(const.STARTING_DIRECTORY+'\\cases\\'+case_data.current_case_name+'\\outputs\\capacity_value_table_temp.csv', 'a') as outfile:
        writer = _csv.writer(outfile, delimiter=',',lineterminator = '\n')
        writer.writerow([capacities])

def try_repeatedly(f, *args):
    while True:
        try:
            return f(*args)
        except IOError:
            _time.sleep(2)








