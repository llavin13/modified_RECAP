# -*- coding: utf-8 -*-
"""
Created on Wed Oct 16 11:04:45 2013

@author: ryan
"""

import numpy as _np

def adjust_generator_stack(case_data, dx):
    if dx<0:
        change_made = 0
        while change_made>dx:
            index = _np.argmax(_np.array(case_data.gendata.retire)==case_data.gendata.retirement_index)
            index_gen_capacity = max([case_data.gendata.cap[m][index] for m in case_data.gendata.cap.keys()])
            impending_change = index_gen_capacity*case_data.gendata.derate[index]
            case_data.gendata.derate[index] = (impending_change-min(change_made-dx, impending_change))/index_gen_capacity
            change_made-=min(change_made-dx, impending_change)
            if case_data.gendata.derate[index]==0:
                case_data.gendata.retirement_index+=1
    else:
        change_made = 0
        while change_made<dx:
            index = _np.argmax(_np.array(case_data.gendata.retire)==case_data.gendata.retirement_index)
            if case_data.gendata.derate[index]==1:
                if index==_np.argmin(case_data.gendata.retire):
                    add_generator(case_data)
                case_data.gendata.retirement_index-=1
                index = _np.argmax(_np.array(case_data.gendata.retire)==case_data.gendata.retirement_index)
            index_gen_capacity = max([case_data.gendata.cap[m][index] for m in case_data.gendata.cap.keys()])
            impending_change = index_gen_capacity*(1-case_data.gendata.derate[index])
            case_data.gendata.derate[index] = 1-(impending_change-min(dx-change_made, impending_change))/index_gen_capacity
            change_made+=min(dx-change_made, impending_change)

def add_generator(case_data):
    for key in case_data.gendata.cap.keys():
        for att in ['cap', 'FOR', 'maint', 'gendist']:
            getattr(case_data.gendata, att)[key].append(getattr(case_data.gendata.average_unit, att)[key])
    
    for dist in ['maintdist', 'FORdist']:
        getattr(case_data.gendata, dist).append(getattr(case_data.gendata.average_unit, dist))
    
    case_data.gendata.derate.append(0.)
    case_data.gendata.retire.append(min(case_data.gendata.retire)-1)
    
    name = 'generic average unit '+str(min(case_data.gendata.retire)-1)
    case_data.gendata.names.append(name)
    case_data.gendata.units[case_data.calculation_settings.zone_to_analyze][name] = len(case_data.gendata.retire)-1

def reinitialize_generator_derates(case_data):
    #This function is not working because it does not reasign the retirement_index
    case_data.gendata.derate = [1.0 if i>=1 else 0.0 for i in case_data.gendata.retire]
    case_data.gendata.retirement_index = 1

