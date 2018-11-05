# -*- coding: utf-8 -*-
"""
Created on Mon Dec 17 11:57:47 2012

@author: Ryan Jones - Ryan.Jones@ethree.com
"""

import numpy as _np
if not __name__ == "__main__":
    import basicm as _basicm
    import timeseries.vargen as _vargen


def calc(case_data, zone, include_supply_vg=True, include_demand_vg=True):
    netload = {}
    
    vg = _vargen.vg_supply(case_data, zone, include_supply_vg=include_supply_vg, include_demand_vg=include_demand_vg)

    for m, h, dt, ll in _basicm.gm.combination(case_data.interm_calc.timeslicelist):        
        
        #conv = case_data.load.bins[zone][m, h, dt, ll] if case_data.load.bins.has_key(zone) else _np.array([[0, 1]])
        conv = case_data.load.bins[zone][m, h, dt, ll] if zone in case_data.load.bins else _np.array([[0, 1]])

        #if case_data.vg.bins.has_key(zone):
        if zone in case_data.vg.bins:
            conv = _basicm.pdm.fft_convolution(conv, vg[m, h, dt, ll], '-')
        
        netload[m, h, dt, ll] = conv
    
    return netload


#def calc(case_data, zone, include_supply_vg = True, include_demand_vg = True):
#    netload = {}
#    
#    vg = _vargen.vg_supply(case_data, zone, include_supply_vg = include_supply_vg, include_demand_vg = include_demand_vg)
#
#    for m, h, dt, ll in _basicm.gm.combination(case_data.interm_calc.timeslicelist):        
#        
#        if case_data.load.bins.has_key(zone):
#            conv = case_data.load.bins[zone][m, h, dt, ll]
#            if case_data.vg.bins.has_key(zone):
#                conv = _basicm.pdm.fft_convolution(conv, vg[m, h, dt, ll], '-')
#        else:
#            conv = vg[m, h, dt, ll]
#        
#        netload[m, h, dt, ll] = conv
#    
#    return netload
