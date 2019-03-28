# -*- coding: utf-8 -*-
"""
Created on Mon Dec 17 16:01:18 2012

@author: Ryan Jones - Ryan.Jones@ethree.com
"""

import numpy as _np
import csv as _csv
import lukeaddon.temperature_supply as addon #added by Luke
import pandas as pd

if not __name__ == "__main__":
    import fileio.read as read
    import const.constants as const
    import basicm
    import timeseries

def _empty_case():
    case_data = basicm.gm.empty_data()
    case_data.interm_calc = basicm.gm.empty_data()
    return case_data

def _load_calculation_settings(case):
    calculation_settings = read.calculation_settings(case)
    
    if calculation_settings.create_CV_table:
        calculation_settings.CV_table_shape = read.cv_table_shape(case, calculation_settings)
    
    calculation_settings.load_bins = read.correlation_bins(case)
    calculation_settings.numloadlevels = max(calculation_settings.load_bins.keys())
    
    return calculation_settings


def _load_load_data(case_data):
    
    zone = case_data.calculation_settings.zone_to_analyze
    case_data.load.bins = {}
    
    profile = read.read_a_profile(case_data.load.stats[zone]['name'], case_data.current_case_name)
    profile.values = basicm.gm.adjust_load_to_peak_energy(profile, case_data.load.stats[zone], case_data.calculation_settings.load_scale_type)
    case_data.load.stats[zone]['monthly_median_peak'] = basicm.gm.monthly_median_load_calc(profile)
    
    minimum_load = round(case_data.calculation_settings.ignore_load_percentile*case_data.load.stats[zone]['peak'])
    if minimum_load>0:
        print (" Load below " + str(int(minimum_load/case_data.calculation_settings.power_system_scaler)) +" MW is ignored")
        print ("  ...caution, this can cause calculation problems")
    
    #Add operating reserves
    profile.values*=(1+case_data.calculation_settings.operating_reserves_up)
    case_data.load.profile = profile
    
    bins, load_break_points, load_bin_calendar = basicm.bindata.bin_primary_load_profile(case_data, profile)
    case_data.interm_calc.load_bin_calendar = _np.vstack((profile.dates, load_bin_calendar)).T
    #write_df = pd.DataFrame(case_data.interm_calc.load_bin_calendar)
    #write_df.to_csv('load_bin_cal.csv')
    
    if case_data.calculation_settings.load_distribution_type=='Raw Data':
        case_data.load.bins[zone] = timeseries.grossload.run_create_raw_hist(bins, case_data, minimum_load)
    else:
        case_data.load.bins[zone] = timeseries.grossload.run_create_normal_or_gumbel(bins, case_data, minimum_load)
    
    
    for zone in case_data.load.stats.keys():
        if zone==case_data.calculation_settings.zone_to_analyze:
            continue
        profile = read.read_a_profile(case_data.load.stats[zone]['name'], case_data.current_case_name)
        profile.values = basicm.gm.adjust_load_to_peak_energy(profile, case_data.load.stats[zone], case_data.calculation_settings.load_scale_type)
        #Add operating reserves
        profile.values*=(1+case_data.calculation_settings.operating_reserves_up)
        case_data.load.bins[zone] = basicm.bindata.hist_time_series_vg(case_data, profile, correlation = True, capacity = 1.0, weekdaymatters = True)
    
    return case_data


def _load_vg_data(case_data):
    case_data.vg.profiles = {}
    case_data.vg.bins = {}
    
    for zone in case_data.vg.stats.keys():
        case_data.vg.profiles[zone] = {}
        case_data.vg.bins[zone] = {}
        
        for vg_name in case_data.vg.stats[zone].keys():
            print (" processing: " + vg_name)
            profile = read.read_a_profile(vg_name, case_data.current_case_name)
            case_data.vg.profiles[zone][vg_name] = profile
            case_data.vg.bins[zone][vg_name] = basicm.bindata.hist_time_series_vg(case_data, profile, case_data.vg.stats[zone][vg_name]['correlation'], case_data.vg.stats[zone][vg_name]['capacity'], case_data.vg.stats[zone][vg_name]['weekends'])
    
    return case_data

def load_data(case):
    case_data = _empty_case()
    
    case_data.current_case_name = case
    case_data.calculation_settings  = _load_calculation_settings(case)
    
    case_data.load = basicm.gm.empty_data()
    case_data.load.stats = read.load_profile_stats(case_data)
    case_data = _load_load_data(case_data)
    
    case_data.vg = basicm.gm.empty_data()
    case_data.vg.stats = read.vg_profile_stats(case_data)
    case_data = _load_vg_data(case_data)
    
    case_data.gendata = _load_generator_data(case_data)
    
    case_data.transmission = _load_import_data(case_data)
    
    #added by LUKE
    case_data.add_on_bool = load_adder(case)
    #run the loading of my script only if you want to use it, and only do it the one time
    
    if case_data.add_on_bool.Use_Add_On:
        print('processing add-on because it has been input as ' + str(case_data.add_on_bool.Use_Add_On))
        #get and create the calendar, too, since you only need that once
        #= _np.vstack((profile.dates, load_bin_calendar)).T this is how you originally get load_bin_calendar
        load_bin_df = pd.DataFrame(case_data.interm_calc.load_bin_calendar)
        case_data.calendar_df = addon.create_calendar(load_bin_df, case_data)
        #do the new copt
        case_data.copt_output = addon.dict_supply_dists(addon.load_gen_temperatures(),case,case_data.calculation_settings.maintenance_schedule)
                
    #end added by LUKE
    
    return case_data

#added by Luke 11.10.18
def load_adder(case):
    add_on_bool = read.use_add_on(case)
    return add_on_bool
#end added

def process_gen_row(row, power_system_scaler):
    rowdata = basicm.gm.empty_data()
    rowdata.cap = [float(r)*power_system_scaler for r in row[3:15]]
    rowdata.FORdist = int(row[15])
    rowdata.FOR = [float(r) for r in row[16:28]]
    rowdata.maintdist = int(row[28])
    rowdata.maint = [float(r) for r in row[29:41]]
    rowdata.retire = int(row[43])
    return rowdata

def start_gen_data():
    gendata = basicm.gm.empty_data()
    
    for att in ['retire', 'FORdist', 'maintdist', 'names']:
        setattr(gendata, att, [])
    
    for att in ['cap', 'FOR', 'maint', 'units', 'gendist']:
        setattr(gendata, att, {})

    for m in range(1,13):
        gendata.cap[m] = []
        gendata.FOR[m] = []
        gendata.maint[m] = []
        gendata.gendist[m] = []
    
    return gendata

def _load_generator_data(case_data):
    outagedist = _load_outage_dist(case_data)
    
    gendata = start_gen_data()
    
    with open(const.STARTING_DIRECTORY+'\\cases\\'+case_data.current_case_name+'\\inputs\\generator_module.csv', 'r') as infile:
        csvreader = _csv.reader(infile, delimiter = ',')
        #csvreader.next()
        next(csvreader)
        
        unitnumber = 0
        
        for row in csvreader:
            name, category, zone = row[:3]
            if not bool(int(row[44])):
                continue
            #if not gendata.units.has_key(zone):
            if zone not in gendata.units:
                gendata.units[zone] = {}
            
            rowdata = process_gen_row(row, case_data.calculation_settings.power_system_scaler)
            
            if max(rowdata.cap)<1.:
                continue
            
            gendata.units[zone][name] = unitnumber
            unitnumber+=1
            
            gendata.names.append(name)
            
            for att in ['retire', 'FORdist', 'maintdist']:
                getattr(gendata, att).append(getattr(rowdata, att))
            
            for m in range(1,13):
                for att in ['cap', 'FOR', 'maint']:
                    getattr(gendata, att)[m].append(getattr(rowdata, att)[m-1])
                gendata.gendist[m].append(makegendist(m, rowdata, outagedist, case_data.calculation_settings.maintenance_schedule))
        #print(len(gendata.gendist[1]))
        #print(type(gendata.gendist[1]))
    
    gendata.derate = [1.]*len(gendata.retire)
    
    gendata.retire = _np.array(gendata.retire)
    gendata.retire[_np.argsort(gendata.retire)] = _np.arange(1, len(gendata.retire)+1)
    gendata.retire = list(gendata.retire)
    
    gendata.retirement_index = min(gendata.retire)
    
    gendata.average_unit = _average_unit(case_data, gendata, outagedist)
#    gendata.average_unit = _average_unit(gendata, outagedist, case_data.calculation_settings.maintenance_schedule)
 
    return gendata


def makegendist(m, rowdata, outagedist, maintenance_schedule):
    cap = rowdata.cap[m-1]*(1-rowdata.maint[m-1]*(maintenance_schedule=="Ideal"))
    
    if cap<.5:
        return _np.array([1.])

    dist = outage_dist(cap, rowdata.FOR[m-1], outagedist[rowdata.FORdist])
    if maintenance_schedule=="Random" and (rowdata.maintdist is not None):
        dist = basicm.pdm.limit_dist1_by_dist2(outage_dist(cap, rowdata.maint[m-1], outagedist[rowdata.maintdist]),dist)
    
    dist = _np.hstack((_np.zeros(int(min(dist[:,0]))), dist[:,1]))
    
    assert round(sum(dist),6)==1.

    return dist

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

def _average_unit(case_data, gendata, outagedist):
    average_unit = basicm.gm.empty_data()
    for att in ['cap', 'FOR', 'maint', 'gendist']:
        setattr(average_unit, att, {})

    average_unit.FORdist = case_data.calculation_settings.generic_generator_outage_distID
    average_unit.maintdist = None

    for m in range(1,13):
        average_unit.cap[m] = case_data.calculation_settings.generic_generator_capacity*case_data.calculation_settings.power_system_scaler
        average_unit.FOR[m] = case_data.calculation_settings.generic_generator_outage
        average_unit.maint[m] = 0.0
        average_unit.gendist[m] = makegendist(m+1, average_unit, outagedist, case_data.calculation_settings.maintenance_schedule)

    return average_unit

def _load_outage_dist(case_data):
    outage_dist = {}
    
    readdist = _np.genfromtxt(const.STARTING_DIRECTORY+'\\cases\\'+case_data.current_case_name+'\\inputs\\outage_distributions.csv', delimiter = ',', skip_header = 1)
    
    for distnum in _np.unique(readdist[:,0]):
        outage_dist[distnum] = readdist[readdist[:,0]==distnum, 1:]
    return outage_dist




def _load_import_data(case_data):
    power_system_scaler = case_data.calculation_settings.power_system_scaler
    case = case_data.current_case_name
    main_zone = case_data.calculation_settings.zone_to_analyze
    
    import_data = basicm.gm.empty_data()
    for att in ['zones', 'lines', 'transdist']:
        setattr(import_data, att, {})
    
    import_data.transdist = []
    
    linenames = {}
    
    with open(const.STARTING_DIRECTORY+'\\cases\\'+case+'\\inputs\\imports.csv', 'r') as infile:
        csvreader = _csv.reader(infile, delimiter = ',')
        #header = csvreader.next()
        header = next(csvreader)
        
        ind1, ind2, ind3, ind4 = header.index('Transmission Line'), header.index('Pathway Start'), header.index('Pathway End'), header.index('Maximum Capacity')
        
        dist_domain = _np.array([float(f)*power_system_scaler for f in header[15:] if not f==""])
        
        line_number = 0
        for row in csvreader:
            #if not import_data.zones.has_key(row[ind2]):
            if row[ind2] not in import_data.zones:
                import_data.zones[row[ind2]] = []
            #if not import_data.zones.has_key(row[ind3]):
            if row[ind3] not in import_data.zones:
                import_data.zones[row[ind3]] = []
            
            #if linenames.has_key(row[ind1]):
            if row[ind1] in linenames:
                line_number = linenames[row[ind1]]
                
                for zone in [row[ind2], row[ind3]]:
                    if not line_number in import_data.zones[zone]:
                        import_data.zones[zone].append(line_number)
                    if not zone in import_data.lines[line_number]:
                        import_data.lines[line_number].append(zone)
                
            else:
                linenames[row[ind1]] = line_number
            
                import_data.zones[row[ind2]].append(line_number)
                import_data.zones[row[ind3]].append(line_number)
                
                import_data.lines[line_number] = [row[ind2], row[ind3]]
                
                import_data.transdist.append(basicm.pdm.space_dist(_np.array([dist_domain*float(row[ind4]), [float(f) for f in row[15:] if not f==""]]).T))
            
            line_number= max(linenames.values())+1
    
    import_data.layers = basicm.gm.explore_transmission_layers(zone = main_zone, 
                                                               layer = 0, layers_deep = {}, 
                                                                done_zones = [main_zone], done_lines = [],
                                                                transmission = import_data)
    import_data.layers[0] = [main_zone]
    
    return import_data



