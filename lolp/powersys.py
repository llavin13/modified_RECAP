# -*- coding: utf-8 -*-
"""
Created on Mon Oct 14 17:50:07 2013

@author: ryan
"""

import numpy as _np
import operator as _operator
import time
if not __name__ == "__main__":
    import const.constants as const
    import basicm as _basicm
    import timeseries as _timeseries
    import supply as _supply

class powersystem:
    def __init__(self, case_data, months_to_analyze, marginalcvmode=False, cap_short=0, include_supply_vg = True, include_demand_vg = True, include_imports=True):
        for att in ['power_system_scaler', 'operating_reserves_up', 'simultaneous_import_limit', 'available_imports_setting', 'numloadlevels', 'target_metric', 'target_metricvalue', 'threshold', 'adjust_system_capacity_method', 'marginal_CV_calc_method', 'output_intermediate_results', 'peak_load_month']:
            setattr(self, att, getattr(case_data.calculation_settings, att))
        
        self.marginalcvmode = marginalcvmode

        self.flatloadcarried = True if (self.adjust_system_capacity_method=='Flat load carried') or (self.marginalcvmode and self.marginal_CV_calc_method=='Flat load carried') else False
        self.genstackalter = False if self.flatloadcarried else True

        self.include_supply_vg = include_supply_vg
        self.include_demand_vg = include_demand_vg
        self.include_imports = include_imports
        self.cap_short = cap_short
        
        self.zone = case_data.calculation_settings.zone_to_analyze
        self.months_to_analyze = months_to_analyze        
        
        if months_to_analyze == tuple(range(1,12+1)):
            self.medianpeak = case_data.load.stats[self.zone]['peak']
        else:
            self.medianpeak = case_data.load.stats[self.zone]['monthly_median_peak'][months_to_analyze]
        
        
        self.annual_energy  = case_data.load.stats[self.zone]['energy']
        self.timeslicelist = case_data.interm_calc.timeslicelist
        
        self.target_metricvalue*=(len(self.timeslicelist[0])/12.)
        
    def update_netload(self, case_data):
#        a = time.time()
        self.netload = _timeseries.netload.calc(case_data, self.zone, include_supply_vg=self.include_supply_vg, include_demand_vg=self.include_demand_vg)
#        print "netload " + str(time.time()-a)
    
    def initialize(self, case_data):
        _supply.adjustgen.reinitialize_generator_derates(case_data) #Needed otherwise cap_short is not tracked
        self.update_netload(case_data)
        self.update_supply(case_data)
        self.calc_lolp_table()
    
    def update_supply(self, case_data):
#        a = time.time()
        self.update_imports(case_data)
#        print "imports " + str(time.time()-a)
        
#        a = time.time()
        self.update_generation(case_data)
#        print "generation " + str(time.time()-a)
    
    def update_imports(self, case_data):
        if self.include_imports:
            if self.available_imports_setting == 'Contracted resources only':
                self.import_capability = _supply.topt.imports(case_data, include_supply_vg=self.include_supply_vg, include_imports=self.include_imports)
            elif self.available_imports_setting == 'Full import capability':
                self.import_capability = {}
                for key in self.netload.keys():
                    self.import_capability[key] = _np.array([[_np.round(self.simultaneous_import_limit), 1.]]) 
        else:
            self.import_capability = {}
            for key in self.netload.keys():
                self.import_capability[key] = _np.array([[0, 1.]])
    
    def update_generation(self, case_data):
        self.gen = _supply.copt.zone_gen(case_data, self.zone)
    
    def max_gen(self):
        if self.genstackalter:
            return self.gen[self.prmcalcslice()][-1,0]/self.power_system_scaler
        else:
            return (self.gen[self.prmcalcslice()][-1,0]+self.cap_short)/self.power_system_scaler
    
    def max_imports(self):
        return (self.import_capability[self.prmcalcslice()][-1,0])/self.power_system_scaler
    
    def max_conventional_supply(self):
        return self.max_imports()+self.max_gen()
    
    def calc_lolp_table(self):
        if self.genstackalter:
            self.netgen = _supply.netgen.calc(self.gen, self.import_capability, self.netload, cap_short=0., output_intermediate_results=self.output_intermediate_results)
        else:
            self.netgen = _supply.netgen.calc(self.gen, self.import_capability, self.netload, cap_short=self.cap_short, output_intermediate_results=self.output_intermediate_results)
            
        self.lolp_table, self.eue_table = _np.zeros((2,24,12)), _np.zeros((2,24,12))
        
        for m, h, dt, ll in _basicm.gm.combination(self.timeslicelist):
            if min(self.netgen[m, h, dt, ll][:,0])>=0:
                continue
            self.lolp_table[dt, h-1, m-1]+= _np.sum(self.netgen[m, h, dt, ll][_np.nonzero(self.netgen[m, h, dt, ll][:,0]<0)][:,1])
            self.eue_table[dt, h-1, m-1]+= _np.sum(-_np.prod(self.netgen[m, h, dt, ll][_np.nonzero(self.netgen[m, h, dt, ll][:,0]<0)], axis = 1))
    
    def prmcalcslice(self):        
        if self.peak_load_month in self.months_to_analyze:
            m = [int(self.peak_load_month)]
        else:
            m = range(1,13)
        
        keys = [k for k in self.netload.keys() if k[0] in m]
        values = [self.netload[k][-1,0] for k in keys]
        index, value = max(enumerate(values), key=_operator.itemgetter(1))
        return keys[index]
    
    def LOLE(self):
        #this definition is changed by Luke 3.23.19
        #return _np.sum(self.lolp_table*const.LOLP_TABLE_WEIGHTS)
        test_array = self.lolp_table*const.LOLP_TABLE_WEIGHTS
        return _np.sum(test_array.max(axis=1))
        
    
    def ALOLP(self):
        return 1-(_np.prod((1-self.lolp_table)**const.LOLP_TABLE_WEIGHTS))
        
    def EUE(self):
        return _np.sum(self.eue_table*const.LOLP_TABLE_WEIGHTS)/self.power_system_scaler

    def EUENORM(self):
        return self.EUE()/(self.annual_energy/self.power_system_scaler)
    
    def results(self):
        results = {}
        results['cap_short'] = self.cap_short/self.power_system_scaler
        results['1-2 peak load'] = self.medianpeak/self.power_system_scaler
        results['lolp_table'], results['eue_table'] = self.lolp_table, self.eue_table
        for metric in ['LOLE', 'ALOLP', 'EUE', 'EUENORM', 'max_conventional_supply', 'max_imports', 'max_gen', 'prmcalcslice']:
            results[metric] = getattr(self, metric)()
        return results
    
    def tunelolp(self, case_data):
        self.flatloadcarried = True if (self.adjust_system_capacity_method=='Flat load carried') or (self.marginalcvmode and self.marginal_CV_calc_method=='Flat load carried') else False
        self.genstackalter = False if self.flatloadcarried else True
        fine_tune = False
        
        metricvalue = getattr(self,self.target_metric)()
        
        print ("initial reliability statistic: "+self.target_metric+" = %(value).3f" %{"value": metricvalue}+", target "+self.target_metric+" = "+str(self.target_metricvalue))
        
        if abs(metricvalue/self.target_metricvalue-1)<self.threshold:
            print ("reliability standard is met")
            return
        
        dx = self.max_conventional_supply()/self.power_system_scaler*.03
        y = metricvalue
        dy = max(y, 10**-5)
        i = 0
        
        while True:
            i+=1

            direction = -1 if metricvalue < self.target_metricvalue else 1
            self.cap_short+= dx*direction

            print (str(i)+" Changing the supply-stack by %(change).1f MW" %{"change": direction*dx/self.power_system_scaler})

            if self.genstackalter:
                _supply.adjustgen.adjust_generator_stack(case_data, direction*dx)
                self.update_supply(case_data)
            
            self.calc_lolp_table()
            metricvalue = getattr(self, self.target_metric)()
            
            dy = metricvalue - y
            y = metricvalue
            
            if not fine_tune:
                #If we are not within 5% use newton's method to get dx
                dx = self._newton_dx(dx, dy, metricvalue)
                if (abs(metricvalue/self.target_metricvalue-1)<0.05):
                    fine_tune = True
            else:
                #Check to see if it is base 10, if not, make the conversion
                if not 10**int(_np.log10(dx))==dx:
                    dx = int(10**int(_np.log10(dx)))
                elif (-1 if metricvalue < self.target_metricvalue else 1) !=direction:
                    dx/=10
            
            if (abs(metricvalue/self.target_metricvalue-1)<self.threshold) or dx==0 or i>100:
#            if (abs(metricvalue/self.target_metricvalue-1)<self.threshold) or abs(dx)<1 or i>1000:
                print ("final reliability: "+self.target_metric+" = %(value).3f"  %{"value": metricvalue})
                print ("")
                return
            else:
                print ("   Resulting " +self.target_metric+" = %(value).3f"  %{"value": metricvalue})

    def _newton_dx(self, dx, dy, metricvalue, alpha = 0.8):
        new_dx = abs((self.target_metricvalue - metricvalue)*dx/(10**-5 if dy==0. else dy))
        return min(10**int(_np.log10(self.medianpeak))/2, alpha*new_dx)

#    def tunelolp(self, case_data):
#        self.flatloadcarried = True if (self.adjust_system_capacity_method=='Flat load carried') or (self.marginalcvmode and self.marginal_CV_calc_method=='Flat load carried') else False
#        self.genstackalter = False if self.flatloadcarried else True
#        
#        metricvalue = getattr(self,self.target_metric)()
#        
#        starting_max_supply = self.max_conventional_supply()
#        print "initial reliability statistic: "+self.target_metric+" = %(value).4f" %{"value": metricvalue}+", target "+self.target_metric+" = "+str(self.target_metricvalue)
#        
#        if abs(metricvalue/self.target_metricvalue-1)<self.threshold:
#            print "reliability standard is met"
#            return
#        
#        dx = starting_max_supply*.03 if metricvalue/self.target_metricvalue>1 else -starting_max_supply*.03
#        y = metricvalue
#        dy = max(y, 10**-5)
#        i = 0
#        
#        while True:
#            i+=1
#            dx = self._next_dx(dx, dy, metricvalue)
#            print str(i)+" Changing the supply-stack by %(change).1f MW" %{"change": dx/self.power_system_scaler}
#            
#            self.cap_short+= dx
#            
#            if self.genstackalter:
#                _supply.adjustgen.adjust_generator_stack(case_data, dx)
#                self.update_supply(case_data)
#            
#            self.calc_lolp_table()
#            
#            old_metricvalue, metricvalue = metricvalue, getattr(self,self.target_metric)()
#            
#            dy = metricvalue - y
#            y = metricvalue
#            
#            if abs(metricvalue/self.target_metricvalue-1)<self.threshold or (abs(dx)<=1 and i>10) or i>20:
#                print "final reliability: "+self.target_metric+" = %(value).3f"  %{"value": metricvalue}
#                return
#            else:
#                print "   Resulting " +self.target_metric+" = %(value).3f"  %{"value": metricvalue}

#    def _next_dx(self, dx, dy, metricvalue, scale_step_size_limit = 0.05, alpha = 0.9):
#        new_dx = (self.target_metricvalue - metricvalue)*dx/(10**-5 if dy==0. else dy)
#        new_dx = abs(new_dx) if metricvalue/self.target_metricvalue>1 else -abs(new_dx)
#        return min(self.medianpeak*scale_step_size_limit,max(-self.medianpeak*scale_step_size_limit,alpha*new_dx))
