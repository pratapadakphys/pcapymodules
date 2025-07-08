# -*- coding: utf-8 -*-
"""
Created on Mon Jan 30 17:12:56 2023

@author: prata
"""

import numpy as np
import re
import matplotlib.pyplot as plt

def get_angle_from_pixel(px, px_max=None, NA=0.7, n=1):
    '''
    px = pixel
    px_max = maximum pixel corresponding to the k_spcae boundary
    NA = Numerical aperture of the objective
    n = Refcative index of the medium
    '''
    if px_max == None:
        px_max = (max(px)-min(px))/2
    
    f= 0.2
    n=1
    NA= 0.7
    a_max = np.arcsin(NA/n)
    print (a_max*180/np.pi)
    d=px_max/ np.tan(a_max)
    a = np.arctan((px-px_max)/d)
    return a*180/np.pi

def get_flat(y):
    y_min = min (y)
    yf = y-y_min
    return yf

def get_norm(y):
    y_min = min (y)
    yf = np.array(y-y_min)
    return yf/max(yf)

def get_colors(List,cmap,start=0):
    n=len(List)
    if start==0:return cmap(np.linspace(0,1,n))
    else:return cmap(np.linspace(1,0,n))

def get_color(value, cmap, val_list ,start=0, N=1000):
    max_value = max(val_list)
    min_value = min(val_list)
    
    delta = max_value*1.0 - min_value*1.0
    dd = delta/N
    
    array = np.linspace(min_value,max_value,N)
    if start==0: colors =  cmap(np.linspace(0,1,N))
    else: colors =  cmap(np.linspace(1,0,N))    
    for a, c in zip(array, colors):
        if abs(value - a)<0.6*dd:
            return c       
    else: 
        return None
    
def put_tag(text):
    plt.figtext(0.99, 0.01, text, ha = 'right', color = 'lightgray', fontsize = 'xx-small')

 