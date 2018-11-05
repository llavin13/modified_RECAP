# -*- coding: utf-8 -*-
"""
Created on Fri Aug 31 14:22:44 2012

@author: Ryan Jones - Ryan.Jones@ethree.com
"""

import numpy as np
import time
import fileio.write_results
import fileio.read
import fileio.read_case_data
#import fileio
import const.constants
import lolp.batchcv
import lolp.capacityplanning
import lolp.chronological_lolp
import lolp.cvtable
import lolp.powersys
import basicm.bindata
import basicm.gm
import basicm.pdm
import fileio
import timeseries.grossload
import timeseries.netload
import timeseries.vargen
import supply.adjustgen
import supply.copt
import supply.netgen
import supply.topt

#from matplotlib import pylab
#def plotdist(dist):
#    pylab.plot(dist[:,0], dist[:,1])
#    pylab.show()

def dotdist(dist):
    return np.dot(dist[:,0],dist[:,1])

a = time.time()
for case in const.constants.CASES_TO_RUN:
    print ('Running case '+str(const.constants.CASES_TO_RUN.index(case)+1)+' of '+str(len(const.constants.CASES_TO_RUN))+'\n')
    #print ('Hello world')
    print ("loading data for " + case)
    case_data = fileio.read_case_data.load_data(case)

    a = basicm.gm.time_stamp(a)
    
    if (not case_data.calculation_settings.create_CV_table_only) or (not case_data.calculation_settings.create_CV_table):
        results, m_CV = lolp.capacityplanning.run(case_data)
        a = basicm.gm.time_stamp(a)
    
    if case_data.calculation_settings.create_CV_table:
        print ("Creating value table")
        lolp.cvtable.run(case_data)
        a = basicm.gm.time_stamp(a)

print ('All cases ran successfully!')

#months_to_run = [tuple(range(1,12+1))]+[(m,) for m in range(1,12+1)] if case_data.calculation_settings.monthly_capacity_value else [tuple(range(1,12+1))]
##m = (12,)
#m = tuple(range(1,12+1))
#
#case_data.interm_calc.timeslicelist = [m, range(1,24+1), range(2), range(1, case_data.calculation_settings.numloadlevels+1)]
#
#psys = lolp.powersys.powersystem(case_data, m, include_supply_vg = True, include_demand_vg = True, include_imports = True)
#psys.initialize(case_data)
#psys.tunelolp(case_data)



#psys = lolp.powersys.powersystem(case_data, m, include_supply_vg = False, include_demand_vg = False, include_imports = False)
#psys.initialize(case_data)
#psys.tunelolp(case_data)
#
#psys.include_demand_vg = True
#psys.update_netload(case_data)
#psys.calc_lolp_table()
#psys.tunelolp(case_data)
#
#psys.include_supply_vg = True
#psys.update_netload(case_data)
#psys.calc_lolp_table()
#psys.tunelolp(case_data)
#
#psys.include_imports = True
#psys.update_supply(case_data)
#psys.calc_lolp_table()
#psys.tunelolp(case_data)


