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
from . import spereaderv3 as sr
import os

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
    def __init__(self, files, bgfiles = None, pattern = None):
        '''
        files: String of folder or list of SpeFiles
        pattern: A dictionary of pattern
        '''
        if type(files) == str:
            self.files = sr.load_files(files)
            
        else: self.files = files
        self.bgfiles = None

        if bgfiles is not None:
            if type(bgfiles) == str:self.bgfiles = sr.load_files(bgfiles)
            else: self.bgfiles = bgfiles
        self.data = None
        self.variable = 'fileno'

        self.size = len(self.files)
        self._load_data()
        self._get_tag()
        self._get_flat()
        self._update_min_max()
        self._get_norm_data()
        if pattern is not None: self._update_variables(pattern)
        self.update_data()
        

    def _load_data(self):
        data_list = []
        i=0
        for file in self.files:
            data = lp.get_file_info(file.filepath)
            (x,y) = file.get_spectrum()
            data['x'] = x
            data['y']=y
            if self.bgfiles is not None:
                (x,y) = self.bgfiles[i].get_spectrum()
                data['x_bg'] = x
                data['y_bg']=y
            data_list.append(data)
            i+=1
            
        self.data = pd.DataFrame(data_list)
        
        
    def _get_tag(self):
        filenos = self.data['fileno']
        proj = lp.Project(None,None,None)
        proj.get_project(self.data['tag'][0])
        self.tag = r'[%s-%s-%d_%d]'%(proj.name, proj.device,min(filenos),max(filenos))
        
        
    def _update_variables(self, pattern): 
        new_data = self.data
        for key in pattern:
            val_list =[]
            for file in self.files:
                filename = os.path.basename(file.filepath).split('/')[-1]
                res = re.search(pattern[key], filename)
                res = re.search(r"[-+]?(?:\d*\.*\d+)", res.group())
                number = float(res.group())
                val_list.append(number)
            new_data[key]=val_list
            self.variable = key
        self.data = new_data
        
    def _get_flat(self):
        fy_list = []
        if self.bgfiles is None:
            for y in self.data['y']:
                ym = min(y)
                y=y-ym
                fy_list.append(y)
        else:
            for y in self.data['y']:
                ym = min(y)
                y=y-ym
                fy_list.append(y)
        self.data['fy'] = fy_list  
        
    def _get_norm_data(self):
        ny_list = []
        for fy in self.data['fy']:
            ny=fy/max(fy)
            ny_list.append(ny)
        self.data['ny'] = ny_list  
                
        '''
        if variables==None: variables = self.infos[variable_name]
        self.variables = variables

        intensity = np.zeros((n,len(self.lambdas)))    
        for i in range(n): 
            intensity[i] = self.files[i].get_spectrum()[1]
            
        self.intensity = intensity
        '''
        
    def get_normalized(self):
        self.update_data(norm=True)
            
    def update_data(self, norm=False):
        n=self.size
        self.lambdas = self.data['x'][0]
        intensity = np.zeros((n,len(self.lambdas)))    
        for i in range(n): 
            if norm:
                intensity[i] = np.array(self.data['ny'][i])
            else:
                intensity[i]=np.array(self.data['y'][i])
            
        self.intensity = intensity
        
    def _update_min_max(self):
        maxlist = []; minlist = []
        for y in self.data['fy']: 
            maxlist.append(max(y))
            minlist.append(min(y))
            
        self.data['max'] = maxlist
        self.data['min'] = minlist
        
    def plot_intensity(self, variable =None, *args, **kwargs):
        if variable is None: variable = self.variable
        plt.contour(self.lambdas, self.data[variable], self.intensity, *args, **kwargs)
        cbar = plt.colorbar()
        cbar.set_label('Intensity (count)')
        plt.xlabel(r'$\lambda$ (nm)')
        plt.ylabel (self.variable)
        put_tag(self.tag)
        
        
    def plot_lines(self, variable =None, cmap = plt.cm.rainbow, skip=0, shift =0.0, **kwargs):
        if variable is None: variable = self.variable
        colors = cmap(np.linspace(1,0,self.size))
        i=0
        for y,v,c in zip(self.intensity,  self.data[variable],colors):
            if i%(skip+1)==0:
                plt.plot(self.lambdas, y+i*shift, label = v, color = c, **kwargs)
            i+=1
        plt.ylabel('Intensity (count)')
        plt.xlabel(r'$\lambda$ (nm)')
        plt.legend (title = self.variable)

        #plt.suptitle(tags[flake] + ': rRef(lambda, Pol_in)', fontsize = 'small', alpha = 1)
        put_tag(self.tag)
        
    def plot_max(self, variable =None, **kwargs):
        if variable is None: variable = self.variable
        p=plt.plot(self.data[variable], self.maxlist, **kwargs)
        plt.ylabel('Max intensity (count)')
        plt.xlabel(self.variable)

        #plt.suptitle(tags[flake] + ': rRef(lambda, Pol_in)', fontsize = 'small', alpha = 1)
        put_tag(self.tag)
        return p
    
def get_file_set (folders, pattern = None):
    if type (folders) is dict:
        Fs ={}
        for key in folders:
            Fs[key]= FileSet(folders[key], pattern = pattern)
        
        return Fs
    
    elif type (folders) is list:
        Fs = []
        for f in folders:
            Fs.append(FileSet(f), pattern = pattern)
        
        return Fs
    
    elif type (folders) is str:
        return FileSet(folders, pattern = pattern)
    
    