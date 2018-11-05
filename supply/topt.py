# -*- coding: utf-8 -*-
"""
Created on Mon Dec 17 17:46:29 2012

@author: Ryan Jones - Ryan.Jones@ethree.com
"""

import time
if not __name__ == "__main__":
    import basicm as _basicm
    import supply.copt as _copt


def combine_zones_vertically(importingzone, exportingzone, tline_dist):
    return _basicm.pdm.fft_convolution(importingzone, _basicm.pdm.limit_dist1_by_dist2(tline_dist, _basicm.pdm.negatives_become_zero(exportingzone)), '+')

def combine_zones_horizontally(firstzone, secondzone):
    return _basicm.pdm.fft_convolution(_basicm.pdm.negatives_become_zero(firstzone), _basicm.pdm.negatives_become_zero(secondzone), '+')

def imports(case_data, include_supply_vg=True, include_imports=True):
#    a = time.time()
    zone_supply = _copt.independent_zone_net_gen(case_data, include_supply_vg=include_supply_vg) #always include demand size, does not include the primary zone
#    print "zone supply " + str(time.time()-a)
    
    for layer in range(max(case_data.transmission.layers.keys())-1, -1,-1): #starts at numzones-1 and goes to the primary zone
#        a = time.time()
    
        #This first loop brings in transmission to zones in the layer
        for zone in case_data.transmission.layers[layer]: #takes each zone in the layer 
            if zone_supply[zone]==None: #because a zone could have been made None when it was combined horizontally
                continue
            for line in case_data.transmission.zones[zone]: #looks at each line connected to that zone
            
                for zone2 in case_data.transmission.lines[line]: #looks at the zone connected to each line
                
                    if zone2 in case_data.transmission.layers[layer+1]: #otherwise, if the zone is in the layer above, combine it subject to transmission
                        
#                        if zone2 in case_data.load.stats.keys() and not include_imports: #if the zone has load and we are not importing surplus from neighbors, it is thrown out
#                            zone_supply[zone2] = None
#                            continue
                        
                        for key in zone_supply[zone].keys():
                            zone_supply[zone][key] = combine_zones_vertically(importingzone = zone_supply[zone][key], exportingzone = zone_supply[zone2][key], tline_dist = case_data.transmission.transdist[line])
        
#        print str(layer)+" "+ str(time.time()-a)
#        a = time.time()
        
        if layer==0: #layer 0 has no parallel zones and if we don't break here it will become None
            break
        
        #This second loop combines zones in a layer that share a common transmission pathway out
        for zone in case_data.transmission.layers[layer]: #takes each zone in the layer again
#            if zone in case_data.load.stats.keys() and not include_imports: #if the zone has load and we are not importing surplus from neighbors, it is thrown out
#                zone_supply[zone] = None
#                continue
            
            for line in case_data.transmission.zones[zone]: #look at the connecting lines to that zone
                for zone2 in case_data.transmission.lines[line]: #look at the zones on the other end of that line

                    if zone_supply[zone2] == None: #zone2 could have been thrown out when it was zone
                        continue
                    
                    if (zone2 in case_data.transmission.layers[layer]) and (zone!=zone2): #if zone2 is on the same layer, shares a transmission line, and is not the same as zone1, combine
                        
#                        if zone2 in case_data.load.stats.keys() and not include_imports: #if the zone has load and we are not importing surplus from neighbors, it is thrown out
#                            zone_supply[zone2] = None
#                            continue
                        
                        for key in zone_supply[zone].keys():
                            zone_supply[zone][key] = combine_zones_horizontally(firstzone = zone_supply[zone][key], secondzone = zone_supply[zone2][key])
                        zone_supply[zone2] = None #we have taken zone2 and added it to zone1, therefore we zero zone2 to avoid double counting
        
#        print str(layer)+" "+ str(time.time()-a)
    
#    a = time.time()
    for key in zone_supply[zone].keys(): #cap all the imports coming in at the simultaneous import limit
        zone_supply[case_data.transmission.layers[0][0]][key] = _basicm.pdm.cap_dist(zone_supply[case_data.transmission.layers[0][0]][key], case_data.calculation_settings.simultaneous_import_limit)
#    print "simultaneous limit "+ str(time.time()-a)
       
    return zone_supply[case_data.transmission.layers[0][0]]













