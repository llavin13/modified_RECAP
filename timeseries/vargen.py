# -*- coding: utf-8 -*-
"""
Created on Fri Jan 04 15:55:28 2013

@author: Ryan Jones - Ryan.Jones@ethree.com
"""

import numpy as _np
if not __name__ == "__main__":
    import basicm as _basicm

def vg_conv(vg_profiles, vg_stats, timeslice, include_supply_vg = True, include_demand_vg = True):
    re_conv = _np.array([[0,1]], dtype = 'f8')
    for vg in vg_profiles.keys():
        if (vg_stats[vg]['PRM accounting']=='supply resource' and include_supply_vg) or (vg_stats[vg]['PRM accounting']=='demand modifier' and include_demand_vg):
            re_conv = _basicm.pdm.fft_convolution(re_conv, vg_profiles[vg][timeslice], '+')
    return re_conv

def vg_supply(case_data, zone, include_supply_vg = True, include_demand_vg = True):
    vg_supply = {}
    
    for m, h, dt, ll in _basicm.gm.combination(case_data.interm_calc.timeslicelist):
        #if case_data.vg.bins.has_key(zone):
        if zone in case_data.vg.bins:
            vg_supply[m, h, dt, ll] = vg_conv(case_data.vg.bins[zone], case_data.vg.stats[zone], (m, h, dt, ll), include_supply_vg = include_supply_vg, include_demand_vg = include_demand_vg)
        else:
            vg_supply[m, h, dt, ll] = _np.array([[0,1]])
    
    return vg_supply





    

