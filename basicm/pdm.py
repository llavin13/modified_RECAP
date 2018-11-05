# -*- coding: utf-8 -*-
"""
Created on Fri Jan 04 15:51:52 2013

@author: Ryan Jones - Ryan.Jones@ethree.com
"""
import numpy as _np
import scipy.stats as _stats
import scipy.signal as _signal
import time

def is_strnumeric(s):
    """
    Checks to see if a string is numeric.
    
    Args:
        s (string)
        
    Returns:
        Boolean    
    """
    try:
        float(s)
        return True
    except ValueError:
        return False

def cap_dist(dist, cap):
    """
    Caps a distribution at some number; useful for enforcing maximum imports
    """
    if max(dist[:,0])<=cap:
        return dist
    if min(dist[:,0])>=cap:
        return _np.array([[cap,1]], dtype = 'f8')
        
    dist[[dist[:,0]==cap],1]+= _np.sum(dist[[dist[:,0]>cap],1])
    return dist[dist[:,0]<=cap]


def negatives_become_zero(dist):
    """
    calculating zone export capability; fuctions removes negatives from the distribution and adds associated probability to zero
    """
    if min(dist[:,0])>=0:
        return dist
    if max(dist[:,0])<=0:
        return _np.array([[0,1]], dtype = 'f8')
    
    dist[_np.nonzero(dist[:,0]==0),1] += _np.sum(dist[_np.nonzero(dist[:,0]<0),1])
    
    return dist[_np.nonzero(dist[:,0]>=0)]

def space_dist(dist):
    """
    Takes a distribution and spaces it in interger increments merging the probability distribution where necessary
    """
    dist = dist[dist[:,0].argsort(),] #sorts the distribution on the first column
    
    mini = dist[min(_np.nonzero(_np.cumsum(dist[:,1])>10**(-9))[0]),0]
    maxi = dist[-min(_np.nonzero(_np.cumsum(dist[::-1,1])>10**(-9))[0])-1,0]
    
    dist = dist[_np.all([dist[:,0]>=mini,dist[:,0]<=maxi], axis = 0)]
    
    temp = dist_of_zeros(mini, maxi)
    
    if _np.all(_np.round(dist[:,0])==dist[:,0]):
        temp[_np.array(_np.round(dist[:,0])-mini, dtype = int),1] = dist[:,1]
        return temp
    else:
        dist[:,0] = _np.round(dist[:,0])
        for n in _np.unique(dist[:,0]):
            temp[int(n-mini),1] = _np.sum((dist[:,0]==n)*dist[:,1])
        return temp

def dist_of_zeros(mini, maxi):
    return _np.vstack((_np.arange(round(mini), round(maxi)+1), _np.zeros(int(round(maxi))-int(round(mini))+1))).T

def common_indices_dist(*args):
    """
    takes a list of probability distributions where the first column is an index and returns the same list over a common set of indicies
    """
    min_point, max_point = min(args[0][:,0]), max(args[0][:,0])
    for dist in args[1:]:
        min_point, max_point = min(min(dist[:,0]), min_point), max(max(dist[:,0]), max_point)
    
    return_list = []
    for dist in args:
        temp = dist_of_zeros(min_point, max_point)
        temp[_np.array(_np.round(dist[:,0])-min_point, dtype = int),1] = dist[:,1]
        return_list.append(temp)
        
    return return_list

def limit_dist1_by_dist2(tx_dist,gen_dist):
    
    # adjust inputs for common indices
    tx_dist_adj, gen_dist_adj = common_indices_dist(_np.vstack((_np.hstack((_np.arange(min(tx_dist[:,0])+1), tx_dist[:,0]+1)), _np.hstack((_np.zeros(int(min(tx_dist[:,0]))+1), tx_dist[:,1])))).T
                                                    , space_dist(gen_dist))
    
#    tx_dist_adj, gen_dist_adj = common_indices_dist(_np.vstack((tx_dist[:,0]+1, tx_dist[:,1])).T, space_dist(gen_dist))
    
    # Unpack Inputs
    output = dist_of_zeros(min(min(tx_dist[:,0]), min(gen_dist[:,0])), min(max(tx_dist[:,0]), max(gen_dist[:,0])))
#    index_mw = _np.arange(min(min(tx_dist[:,0]), min(gen_dist[:,0])), max(gen_dist[:,0])+1)
    tx_pdf = tx_dist_adj[:,1]
    gen_pdf = gen_dist_adj[:,1]
    
    # Compute reverse cumulative distribution function   
    tx_cdf = 1 - _np.cumsum(tx_pdf)
    gen_cdf = 1 - _np.cumsum(gen_pdf)
    
    # combine two distributions  
    limited_gen = (gen_pdf*tx_cdf)[:-1] + (tx_pdf[1:]*gen_cdf[:-1])
    
    output[_np.array(tx_dist_adj[_np.array(output[:,0]-min(tx_dist_adj[:,0]), dtype = int),0]-min(output[:,0]), dtype = int),1] = limited_gen[_np.array(_np.round(output[:,0])-min(tx_dist_adj[:,0]), dtype = int)]
    
    return output


def test_limit_dist1_by_dist2():
    
    a = dist_of_zeros(0, 10)
    b = dist_of_zeros(0, 10)
    b[-1,-1] = 1
    a[-1,-1] = 1
    
    assert _np.all(limit_dist1_by_dist2(a, b)==a)
    assert _np.all(limit_dist1_by_dist2(b, a)==a)
    
    b = dist_of_zeros(0, 5)
    b[-1,-1] = 1
    
    assert _np.all(limit_dist1_by_dist2(b,a) == b)
    assert _np.all(limit_dist1_by_dist2(a,b) == b)
    
    a = dist_of_zeros(10, 20)
    a[-1,-1] = 1
    
    assert _np.all(limit_dist1_by_dist2(b,a) == b)
    assert _np.all(limit_dist1_by_dist2(a,b) == b)
    
    b = dist_of_zeros(0, 30)
    b[-1,-1] = 1
    
    c = dist_of_zeros(0, 20)
    c[-1,-1] = 1
    assert _np.all(limit_dist1_by_dist2(b,a) == c)
    assert _np.all(limit_dist1_by_dist2(a,b) == c)
    
    a = dist_of_zeros(5, 5)
    b = dist_of_zeros(0, 0)
    b[-1,-1] = 1
    a[-1,-1] = 1
    
    assert _np.all(limit_dist1_by_dist2(b,a) == b)
    assert _np.all(limit_dist1_by_dist2(a,b) == b)
 

def year_distribution(net_load):
    import constants
    days_in_month_average = constants.DAYS_IN_MONTHS[0]*3./4.+constants.DAYS_IN_MONTHS[1]/4.
    weights = [[days*5./7./8766. for days in days_in_month_average],[days*2./7./8766. for days in days_in_month_average]]
    year_distribution = None
    for m in range(1,13):
        for h in range(1,25):
            for dt in range(2):
                try:
                    year_distribution = add_distributions(year_distribution, 
                                                               _np.vstack((net_load[m][h][dt][:,0],net_load[m][h][dt][:,1]*weights[dt][m-1])).T)
                except:
                    year_distribution = _np.vstack((net_load[m][h][dt][:,0],net_load[m][h][dt][:,1]*weights[dt][m-1])).T
    return _np.vstack((year_distribution[:,0], year_distribution[:,1]/sum(year_distribution[:,1]))).T

def load_slicer(load, re_profile):
    load_slice = _np.array([], dtype = 'i4')
    for y in _np.intersect1d(load[:,0], re_profile[:,0]):
        load_slice = _np.hstack((load_slice,_np.nonzero(load[:,0]==y)[0]))
    return (load_slice,)

def overlaping_dist_area(dist1, dist2, low_prob_cut = 10**-15):
#    dist 1 = net load, dist 2 = supply side resources
    if max(dist1[:,0])<0 or dist2[_np.nonzero(dist2[:,0]<=max(dist1[:,0]))][-1,1]<low_prob_cut:
        #if no net load points are above the sum of supply side resources and the maximum point on demand side
        #corresponds to a probability of supply less than the cut point, return 0
        #this saves time and avoids unwarranted precision
        return 0.0
    elif min(dist1[:,0])>=max(dist2[:,0]):
        #if all the net load points are higher, return 1
        return 1.0
    elif min(dist1[:,0])<0:
        dist1 = dist1[_np.nonzero(dist1[:,0]>=0)]
        # If net load is negative, you do not have LOL
    
    dist1 = dist1[_np.nonzero(dist1[:,1]>low_prob_cut)]
    #Remove the tails of the net load distribution to speed the calculation
    lookup = _np.array(dist1[_np.nonzero(dist1[:,0]<=max(dist2[:,0]))][:,0], dtype = 'i4')
    #Here we use the actual values of dist1 as indicies later for dist2
    dist2 = dist2[lookup,]
    #This is needed to allow for skips and duplicates when scaling occurs
    main_portion = _np.dot(dist1[_np.nonzero(dist1[:,0]<=max(dist2[:,0]))][:,1],dist2[:,1])
    #dot product for those portions aligned
    high_portion = _np.sum(dist1[_np.nonzero(dist1[:,0]>max(dist2[:,0])),1])
    return main_portion+high_portion

def add_distributions(dist1, dist2):
    i = _np.union1d(dist1[:,0],dist2[:,0])
    sum_dist = _np.vstack((i, _np.zeros(len(i)))).T 
    sum_dist[_np.nonzero(min(dist1[:,0])==i)[0][0]:_np.nonzero(min(dist1[:,0])==i)[0][0]+len(dist1[:,0]),1]+= dist1[:,1]
    sum_dist[_np.nonzero(min(dist2[:,0])==i)[0][0]:_np.nonzero(min(dist2[:,0])==i)[0][0]+len(dist2[:,0]),1]+= dist2[:,1]
#    sum_dist[:,1]/=_np.sum(sum_dist[:,1])
    return sum_dist

def fft_convolution(dist1, dist2, operation):
    if operation=='+':
        end_points = min(dist1[:,0])+min(dist2[:,0]), max(dist1[:,0])+max(dist2[:,0])
        conv = _signal.fftconvolve(dist1[:,1], dist2[:,1])
    elif operation=='-':
        end_points = min(dist1[:,0])-max(dist2[:,0]), max(dist1[:,0])-min(dist2[:,0])
        conv = _signal.fftconvolve(dist1[:,1], dist2[-1::-1,1])
    conv[_np.nonzero(conv<0)] = 0
    return _np.vstack((_np.arange(min(end_points),max(end_points)+1),conv)).T

def gumbel_fit(data):
    l = 0.577215
    scale = _np.sqrt(6*_np.var(data)/(_np.pi)**2)
    location = _np.mean(data)-l*scale
    return location, scale

def gumbel_cdf_given_x(x, location, scale):
    return _np.exp(-_np.exp(-(x-location)/scale))

def gumbel_pdf_given_x(x, location, scale):
    z = -(x-location)/scale
    return _np.exp(z-_np.exp(z))/scale
    
def create_gumbel_pdf(location, scale, num_std, max_min_points = None):
    upper_scale_factor = -_np.log(-_np.log(_stats.norm.cdf(num_std)))
    lower_scale_factor = _np.log(-_np.log(1-_stats.norm.cdf(num_std)))
    if max_min_points == None:
        i = _np.arange(round(location-scale*lower_scale_factor),round(location+scale*upper_scale_factor))
    else:
        i = _np.arange(round(max(max_min_points[0],location-scale*lower_scale_factor)),round(min(max_min_points[1],location+scale*upper_scale_factor)))
    n = gumbel_pdf_given_x(i, location, scale)
    return _np.vstack((i,n/sum(n))).T

def create_normal_pdf(mean, std, num_std, max_min_points = None):
    if max_min_points == None:
        i = _np.arange(round(mean-std*num_std),round(mean+std*num_std))
    else:
        i = _np.arange(round(min(max_min_points[0],mean-std*num_std)),round(max(max_min_points[1],mean+std*num_std)))
    n = _stats.norm.pdf(i,mean,std)
    return _np.vstack((i,n/sum(n))).T

def create_histogram(ts_bin):

    ts_bin = _np.array(ts_bin)+.5
    
    if _np.ceil(max(ts_bin))==_np.floor(min(ts_bin)):
        return _np.array([[_np.round(_np.mean(ts_bin)), 1.]])
    #print(_np.ceil(max(ts_bin))-_np.floor(min(ts_bin)))
    temp = _np.histogram(ts_bin, range=(_np.floor(min(ts_bin)), _np.ceil(max(ts_bin))), bins = int(_np.ceil(max(ts_bin))-_np.floor(min(ts_bin))), normed = True)
    return _np.vstack((_np.delete(temp[1], -1), temp[0])).T

def normal_or_gumbel(data, fraction_which_matters): #fraction which matters goes from top down so that 1% means only the top 1% of the data matters. 100% means all the data matters.
    data_pdf = create_histogram(data)
    data_cdf_x = data_pdf[:,0]+0.5
    data_cdf = _np.cumsum(data_pdf[:,1])

    location, scale = gumbel_fit(data)
    mean, std = _np.mean(data), _np.std(data)
    
    gumbel_error = _np.sum((data_cdf[-int(len(data_cdf)*fraction_which_matters):]-gumbel_cdf_given_x(data_cdf_x, location, scale)[-int(len(data_cdf)*fraction_which_matters):])**2)
    normal_error = _np.sum((data_cdf[-int(len(data_cdf)*fraction_which_matters):]-_stats.norm.cdf(data_cdf_x, _np.mean(data), _np.std(data))[-int(len(data_cdf)*fraction_which_matters):])**2)
    if gumbel_error>normal_error:
        return mean, std, 'normal'
    else:
        return location, scale, 'gumbel'

def remove_outliers(list_of_data_points): #assumes the data is normally distributed
    location, scale, distribution_type = normal_or_gumbel(list_of_data_points, 1)
    while True:
        ranks = _np.argsort(list_of_data_points)
        done_points=0
        
        for index in [ranks[0], ranks[-1]]:
            if distribution_type=='normal':
                p_value = _stats.norm.cdf(list_of_data_points[index], location, scale)
            elif distribution_type=='gumbel':
                p_value = gumbel_cdf_given_x(list_of_data_points[index], location, scale) 
                   
            p_value_x_len = min(p_value,1-p_value)*len(list_of_data_points)
            
            if p_value_x_len<0.5:
                del list_of_data_points[index]
                if distribution_type=='normal':
                    location, scale = _np.mean(list_of_data_points), _np.std(list_of_data_points)
                elif distribution_type=='gumbel':
                    location, scale = gumbel_fit(list_of_data_points)
                break
            done_points+=1

        if done_points==2:
            return list_of_data_points

def ltqnorm(p):
    if p <= 0 or p >= 1:
        raise ValueError( "Argument to ltqnorm %f must be in open interval (0,1)" % p )

    # Coefficients in rational approximations.
    a = (-3.969683028665376e+01,  2.209460984245205e+02, \
         -2.759285104469687e+02,  1.383577518672690e+02, \
         -3.066479806614716e+01,  2.506628277459239e+00)
    b = (-5.447609879822406e+01,  1.615858368580409e+02, \
         -1.556989798598866e+02,  6.680131188771972e+01, \
         -1.328068155288572e+01 )
    c = (-7.784894002430293e-03, -3.223964580411365e-01, \
         -2.400758277161838e+00, -2.549732539343734e+00, \
          4.374664141464968e+00,  2.938163982698783e+00)
    d = ( 7.784695709041462e-03,  3.224671290700398e-01, \
          2.445134137142996e+00,  3.754408661907416e+00)

    # Define break-points.
    plow  = 0.02425
    phigh = 1 - plow

    # Rational approximation for lower region:
    if p < plow:
       q  = _np.sqrt(-2*_np.log(p))
       return (((((c[0]*q+c[1])*q+c[2])*q+c[3])*q+c[4])*q+c[5]) / \
               ((((d[0]*q+d[1])*q+d[2])*q+d[3])*q+1)

    # Rational approximation for upper region:
    if phigh < p:
       q  = _np.sqrt(-2*_np.log(1-p))
       return -(((((c[0]*q+c[1])*q+c[2])*q+c[3])*q+c[4])*q+c[5]) / \
                ((((d[0]*q+d[1])*q+d[2])*q+d[3])*q+1)

    # Rational approximation for central region:
    q = p - 0.5
    r = q*q
    return (((((a[0]*r+a[1])*r+a[2])*r+a[3])*r+a[4])*r+a[5])*q / \
           (((((b[0]*r+b[1])*r+b[2])*r+b[3])*r+b[4])*r+1)