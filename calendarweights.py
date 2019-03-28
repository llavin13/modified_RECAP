# -*- coding: utf-8 -*-
"""
Created on Sun Nov  4 00:49:42 2018

@author: llavi
"""

import pandas as pd
import const.constants as const
import datetime
import time

start = time.time()

def create_calendar():
    #this part can probably be passed in the real script
    calendar = pd.read_csv(const.STARTING_DIRECTORY+'\\cases\\load_bin_cal.csv')
    print(type(calendar))
    #create needed columns
    calendar.columns = ['index', 'Excel_Date','Bin']
    calendar['pd_date'] = pd.TimedeltaIndex(calendar['Excel_Date'], unit='d') + datetime.datetime(1899, 12, 30)
    calendar['pd_date'] = calendar['pd_date'].apply(lambda dt: datetime.datetime(dt.year, dt.month, dt.day, round(dt.hour+float(dt.minute)/60)))
    calendar['month'] = calendar.pd_date.apply(lambda x: x.month)
    calendar['hour'] = calendar.pd_date.apply(lambda x: x.hour)
    calendar['Date'] = calendar.Excel_Date.apply(lambda x: int(x))
    calendar['Bin'] = calendar.Bin.apply(lambda x: int(x))
    
    #add weekday/weekend by match merging
    daytype = pd.read_csv(const.STARTING_DIRECTORY+'\\read_only\\calendar.csv')
    calendar = pd.merge(calendar, daytype, how='left', on=['Date','month'])
    
    #add temperature by matching
    #right now formatting of the read in data is pretty poor
    weather = pd.read_csv(const.STARTING_DIRECTORY+'\\cases\\Temperature.time.series.Philly.DC.Cleveland.Chicago.102918.csv')
    calendar = pd.merge(calendar, weather, how='left', on=['Excel_Date'])
    
    #create avg temp on whatever you decide is the right way. 
    #Right now averages Philly, DC, Cleveland, and Chicago cols
    temp_cols = calendar.loc[: , "Philadelphia":"Chicago"]
    calendar['Mean_T'] = temp_cols.mean(axis=1)
    
    #round avg temp nearest 5, int(), string it with the C so it'll match the other inputs
    #note implicitly temps rounded to 45C+ or -35C- will break this approach
    calendar['T_string']=calendar.Mean_T.apply(lambda x: str(int(5*round(float(x)/5)))+"C")
    
    #return resulting pandas df
    return calendar

#function for creation of re-weighted np array of supply availability by month-hour-daytype-bin
def timeslice_supply(supply_dict,input_df,m,h,dt,ll):
    time_slice = input_df[(input_df['Bin']==ll) & (input_df['month']==m) & (input_df['hour']==h) & (input_df['weekend']==dt)]
    timeslice_weights = time_slice['T_string'].value_counts(normalize=True)
    
    if m>=5 and m<=9: #define summer months; janky for now
        time_str = 'Jul' #should probably pass month keys of supply_dict here
    else:
        time_str = 'Jan'
        
    count=0
    for key in supply_dict[time_str].keys():
        if key in timeslice_weights.index.values:
            x=supply_dict[time_str][key][:,0]
            y=supply_dict[time_str][key][:,1]*timeslice_weights[key]
            temp_df = pd.DataFrame({'x':x, 'y':y})
            if count==0:
                final_df = temp_df
            else:
                final_df = final_df.set_index('x').add(temp_df.set_index('x'), fill_value=0).reset_index()
            count+=1
        else:
            continue
    
    return final_df.values

#run them all for kicks to test time
'''
for m in range(1,13):
    for h in range(0,24):
        for dt in range(0,2):
            for ll in range(1,4):
                print(m,h,dt,ll)
                timeslice_supply(copt_output,calendar,m,h,dt,ll)
'''

print(create_calendar().columns.values)
print('right now this takes ' +str(time.time()-start) + ' seconds')