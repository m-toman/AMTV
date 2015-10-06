#!/usr/bin/python

import math

def spectrumKLD(means1, vars1, means2, vars2):
    '''
    Calculates KLD for spectral/cepstral distributions
    '''
    lp = min(len(means1), len(means2))
    flTmp = 0.0
    
    for i in range(lp):
        flTmp += ((1 / vars1[i] + 1 / vars2[i]) * (means1[i] - means2[i]) * (means1[i] - means2[i]) + 
                   vars1[i] / vars2[i] + vars2[i] / vars1[i]);        
        
    return flTmp / 2 - lp
        

def pitchKLD( weight1, means1, vars1, weight2, means2, vars2 ):
    return ( math.log ( weight1 / weight2 * (1-weight2) / (1-weight1) )
                 * (weight1 - weight2) + 0.5 * (weight1 - weight2)
                 * math.log( vars2[0] / vars1[0] ) + 0.5 * (means1[0] - means2[0]) * (means1[0] - means2[0])
                 * (weight1 / vars2[0] + weight2 / vars1[0]) - 0.5 * (weight1 + weight2)
                 + 0.5 * ( weight1 * vars1[0] / vars2[0] + weight2 * vars2[0] / vars1[0] ) )


def bndapKLD( means1, vars1, means2, vars2 ):
    flTmp = 0.0
    for i in range(len(means1)):
        flTmp += ( (1.0 / vars1[i] + 1.0 / vars2[i]) * (means1[i] - means2[i]) * (means1[i] - means2[i])
                 + vars1[i] / vars2[i] + vars2[i] / vars1[i] )        
    
    return flTmp / 2.0 - len(means1);


def durationKLD(mean1, var1, mean2, var2):
    return (math.log(var2 / var1) + 
           (math.pow(var1, 2) + math.pow(mean1 - mean2, 2)) / (2*math.pow(var2,2)) 
              - 0.5
           )
