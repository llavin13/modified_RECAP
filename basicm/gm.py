# -*- coding: utf-8 -*-
"""
Created on Fri Jan 04 15:51:52 2013

@author: Ryan Jones - Ryan.Jones@ethree.com
"""
import time
import numpy as _np
if not __name__ == "__main__":
    import const.constants as const

def explore_transmission_layers(zone, layer, layers_deep, done_zones, done_lines, transmission):
    """
    Recursively explores transmission and returns the layers in a dictionary where the key indicates the number of layers from the primary zone
    """
    for tline in transmission.zones[zone]:
        if tline in done_lines:
            continue
        
        done_lines.append(tline)
        
        for zone2 in transmission.lines[tline]:
            if zone2 in done_zones:
                continue
            
            #if not layers_deep.has_key(layer+1):
            if (layer+1) not in layers_deep:
                layers_deep[layer+1] = []
            
            layers_deep[layer+1].append(zone2)
            done_zones.append(zone2)
            
            if not _np.all([l in done_lines for l in transmission.zones[zone2]]):
                explore_transmission_layers(zone2, layer+1, layers_deep, done_zones, done_lines, transmission)
    return layers_deep


def monthly_median_load_calc(profile):
    years, months = _np.transpose(relevant_calendar_long(profile.dates)[:,0:2])
    medianpeak = {}
    for m in range(1,13):
        medianpeak[m,] = _np.median([max(profile.values[_np.all((years==year, months==m), axis = 0)]) for year in _np.unique(years)])
    return medianpeak


def adjust_load_to_peak_energy(profile, stats, load_scale_type):
    years = relevant_calendar_long(profile.dates)[:,0]
    existing_peak = _np.median([max(profile.values[years==year]) for year in _np.unique(years)])
    existing_energy = _np.sum(profile.values)/len(_np.unique(years))
    
    if load_scale_type=='Energy and 1-2 Peak Load':
        multi = (stats['energy']-8766*stats['peak'])/(existing_energy-8766*existing_peak)
        adder = stats['peak']-existing_peak*multi
    elif load_scale_type=="Energy":
        multi = stats['energy']/existing_energy
        adder = 0
    else:
        multi = 1
        adder = 0
    
    return profile.values*multi+adder

def relevant_calendar_long(dates):
    dates = dates[dates<=max(const.CALENDARlong[:,0])]
    return const.CALENDARlong[_np.searchsorted(const.CALENDARlong[:,0], _np.round(dates,2))][:,1:]

def relevant_calendar_short(dates):
    dates = dates[dates<=max(const.CALENDARlong[:,0])]
    return const.CALENDARshort[_np.unique(_np.searchsorted(const.CALENDARshort[:,0], _np.array(dates, dtype = int)))][:,1:]

class dates():
    def __init__(dates):
        dates.dates = dates
        dates.calendar = const.CALENDAR
    
    def years(self):
        pass
    
    def yearindex(self, year):
        pass
    
    def months(self):
        pass
    
    def monthindex(self, month):
        pass
    
    def hour(self):
        pass
    
    def hourindex(self, hour):
        pass
    
    def weekends(self):
        pass
    
    def weekendindex(self, i):
        pass
    
    def loadbin(self):
        pass
    
    def loadbinindex(self, bin_num):
        pass


def isnumeric(s):
    """Checks to see if an argument is a number. Returns: Boolean"""
    try:
        float(s)
        return True
    except ValueError:
        return False

def time_stamp(a):
    """Prints the difference between the parameter and current time. This is useful for timing program execution if timestamps are periodicly saved.
    
    Parameters:
        a: float
    
    Returns:
        current time: float
    """
    print ("%(time).1f seconds to execute \n" %{"time": time.time()-a})
    return time.time()

class empty_data():
    """Empty class"""
    def __init__(self):
        pass

def combination(arrays, repeat = 1):
    """Generator that takes a list of arrays and generates all combinations
    
    Parameters:
        arrays: list of numeric arrays
    
    Returns:
        combination: tuble
    """
    pools = list(map(tuple, [t for t in arrays])) * repeat
    result = [[]]
    for pool in pools:
        result = [x+[y] for x in result for y in pool]
    for prod in result:
        yield tuple(prod)


def reshape(array, ncolumns = 24):
    """Takes an vector and reshapes to have a user specified number of columns
    
    Useful for taking a vetor and creating an array where each row is a separate day
    """
    return _np.reshape(array,(int(len(array)/ncolumns),ncolumns))

def flatten_list(list_to_flatten):
    """Returns a list with sublists removed"""
    return [item for sublist in list_to_flatten for item in sublist]

