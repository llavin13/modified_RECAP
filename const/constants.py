# -*- coding: utf-8 -*-
"""
Created on Mon Dec 17 11:05:44 2012

@author: Ryan Jones - Ryan.Jones@ethree.com
"""


import numpy as _np
import csv as _csv
import os as _os

try:
    STARTING_DIRECTORY = _os.getcwd().split('code')[0]
    CALENDARshort = _np.genfromtxt(STARTING_DIRECTORY+'\\read_only\calendar.csv', delimiter = ',', skip_header = 1)
except:
    STARTING_DIRECTORY = _os.path.realpath(__file__).split('code')[0]
    CALENDARshort = _np.genfromtxt(STARTING_DIRECTORY+'\\read_only\calendar.csv', delimiter = ',', skip_header = 1)

print ('')
print (STARTING_DIRECTORY)
print ('')

LOW_PROB_CUT = 10**(-9)

DAYS_IN_MONTHS = _np.array([[31,28,31,30,31,30,31,31,30,31,30,31],[31,29,31,30,31,30,31,31,30,31,30,31]], dtype = 'i4')

MONTH_WRITE_DICT = dict(zip([tuple(range(1,12+1))]+[(m,) for m in range(1,12+1)], ['all']+list(range(1,12+1))))

LOLP_TABLE_WEIGHTS = _np.ones((2,24,12))
LOLP_TABLE_WEIGHTS*= _np.array([31,28.25,31,30,31,30,31,31,30,31,30,31])
LOLP_TABLE_WEIGHTS[0]*=(5./7.)
LOLP_TABLE_WEIGHTS[1]*=(2./7.)

CASES_TO_RUN = []
with open(STARTING_DIRECTORY+'\\read_only\cases_to_run.csv') as infile:
    infile.readline()  
    csvreader = _csv.reader(infile, delimiter = ',')    
    for row in csvreader:
        CASES_TO_RUN+=row

HOURS = [round(i/24.,2) for i in range(24)]

CALENDARlong = _np.repeat(CALENDARshort, 24, axis = 0)
CALENDARlong[:,0] = _np.round(_np.arange(min(CALENDARlong[:,0]), max(CALENDARlong[:,0])+1, 1./24.),2)
CALENDARlong = _np.vstack((CALENDARlong.T, _np.tile(_np.arange(1,25), int(len(CALENDARlong)/24.)))).T





