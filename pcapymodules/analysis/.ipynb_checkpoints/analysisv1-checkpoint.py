# -*- coding: utf-8 -*-
"""
Created on Mon Jan 30 17:12:56 2023

@author: prata
"""

import numpy as np
import re
import matplotlib.pyplot as plt
from .. import lanmpprojectv3 as lp
import pandas as pd

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


def pixel_to_um (p):
    return 24*p/163

def pol(array, angles):
    minv = min(array)
    maxv=max(array)
    min_i = np.argmin(array)
    max_i = np.argmax(array)
    return ((maxv-minv)/(minv+maxv), angles[min_i],angles[max_i])

   
    
class FileSet:
    def __init__(self, files, variable_name = 'Number', variables = None, pattern = None, whole_search=True):
        self.files = files
        self.variable_name = variable_name
        
        info_list = []
        for file in files:
            if variables==None:
                info = lp.get_file_info(file.filepath, pattern = pattern, variable = variable_name, whole_search=whole_search)
            else:
                info = lp.get_file_info(file.filepath)
            info_list.append(info)
        self.infos = pd.DataFrame(info_list)
        
        filenos = self.infos['fileno']
        proj = lp.Project(None,None,None)
        proj.get_project(self.infos['tag'][0])
        self.tag = r'[%s-%s-%d_%d]'%(proj.name, proj.device,min(filenos),max(filenos))
        
        n = len(self.files)
        self.size = n
        lambdas = self.files[0].get_spectrum()[0]
        self.lambdas = lambdas
        
        if variables==None: variables = self.infos[variable_name]
        self.variables = variables

        intensity = np.zeros((n,len(self.lambdas)))    
        for i in range(n): 
            intensity[i] = self.files[i].get_spectrum()[1]
            
        self.intensity = intensity
        
    def get_normalized(self):
        for i in range(self.size): 
            self.intensity[i] = get_norm(self.intensity[i])
        
        
    def plot_intesity(self,*args, **kwargs):
        plt.contour(self.lambdas, self.variables, self.intensity, *args, **kwargs)
        cbar = plt.colorbar()
        cbar.set_label('Intensity (count)')
        plt.xlabel(r'$\lambda$ (nm)')
        plt.ylabel (self.variable_name)
        put_tag(self.tag)
        
        
    def plot_lines(self, cmap = plt.cm.rainbow, skip=0, shift =0.0, **kwargs):
        colors = cmap(np.linspace(1,0,self.size))

        i=0
        for y,v,c in zip(self.intensity, self.variables,colors):
            if i%(skip+1)==0:
                plt.plot(self.lambdas, y+i*shift, label = v, color = c, **kwargs)
            i+=1
        plt.ylabel('Intensity (count)')
        plt.xlabel(r'$\lambda$ (nm)')
        plt.legend (title = self.variable_name)

        #plt.suptitle(tags[flake] + ': rRef(lambda, Pol_in)', fontsize = 'small', alpha = 1)
        put_tag(self.tag)
        
    def plot_max(self, **kwargs):
        i=0
        maxlist = []
        for y in self.intensity:
            maxlist.append(max(y))
        p=plt.plot(self.variables, maxlist, **kwargs)
        plt.ylabel('Max intensity (count)')
        plt.xlabel(self.variable_name)
        self.maxlist = maxlist

        #plt.suptitle(tags[flake] + ': rRef(lambda, Pol_in)', fontsize = 'small', alpha = 1)
        put_tag(self.tag)
        return p