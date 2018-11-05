# -*- coding: utf-8 -*-
"""
Created on Sun Oct 13 17:24:36 2013

@author: ryan
"""

import numpy as _np
if not __name__ == "__main__":
    import basicm as _basicm


def calc(gen, imports, netload, cap_short=0., output_intermediate_results = False):
    netgen = {}
    
    for key in netload.keys():
        if gen[key][0,0]+imports[key][0,0]>=_np.round(netload[key][-1,0]-cap_short) and not output_intermediate_results:
            netgen[key] = _np.array([[0.,1.]])
        else:
            netgen[key] = _basicm.pdm.fft_convolution(_basicm.pdm.fft_convolution(gen[key], imports[key], '+'), 
                            _basicm.pdm.space_dist(_np.vstack((_np.round(netload[key][:,0]-cap_short), netload[key][:,1])).T), '-')
    return netgen



