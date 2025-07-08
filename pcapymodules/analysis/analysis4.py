# -*- coding: utf-8 -*-
"""
Created on Mon Jan 30 17:12:56 2023

@author: prata
"""

import numpy as np
import re
import matplotlib.pyplot as plt
from .. import lanmpproject as lp
import pandas as pd
import os
from .spereader  import *
TAG = True
from scipy.signal import savgol_filter
from scipy.signal import find_peaks

def _put_tag (self):
        _pathname, _extension = os.path.splitext(os.path.basename(self.filepath))
        if TAG: 
            _tag = lp.Tag().read(_pathname)
            plt.gcf().text(0.95,0.01,_tag, size = 'xx-small', color='lightgrey', horizontalalignment = 'right')
        
SpeFile.customize = _put_tag        

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

def degree_of_polarization(array, angles):
    minv = min(array)
    maxv=max(array)
    min_i = np.argmin(array)
    max_i = np.argmax(array)
    return ((maxv-minv)/(minv+maxv), angles[min_i],angles[max_i])

def my_find_peaks (x, y, select = [0], filter_args= {'window_length':9, 'polyorder':2}, find_peak_args={'prominence':0.005, 'height':0.01}, plot = True, cmap =plt.cm.rainbow):
    
    y = (y-min(y))/max((y-min(y)))
    
    y_filter = savgol_filter(y, **filter_args)
    
    peaks = find_peaks(y_filter, **find_peak_args)[0]
    peaks = np.append(0,peaks)
    peaks_true=peaks[select]
    if plot :
        plt.figure(figsize=(16,4))
        plt.plot(x,y)
        plt.plot(x, y_filter)
        plt.plot(x[peaks], y[peaks], 'o', label='all peaks', color='lightgrey', zorder=-2)
        colors = get_colors(x[peaks_true], cmap)
        plt.scatter(x[peaks_true], y[peaks_true], c = colors, label='all peaks', zorder=-2)
        j=0
        for p in peaks_true:
            plt.text(x[p], y[p]+0.05, '%.1f'%x[j], rotation = 90, ha='center', fontsize='xx-small', color = colors[j])
            j+=1
        
    return (peaks_true,x[peaks_true])
   
    
class SpeFileSet(FileSet):
    def __init__(self, files, pattern = None, search = None, filename = None):
        super().__init__(files, pattern, search, filename)
        
        self._load_data()
        self._load_data(col=1, keys = ['x_bg', 'y_bg'])
        self._get_tag()
        self._update_min_max()
        
        
    def reload(self):
        self._load_data()
        self._update_min_max()

        return self
        
    def _load_data(self, col=0, keys = ['x','y']):
        
        if col in self.df.columns:
            xlist = []; ylist = []
            for file in self.df.iloc[:,col]:
                (x,y) = file.get_spectrum()
                xlist.append(np.array(x)); ylist.append(np.array(y))
            self.df[keys[0]] = xlist; self.df[keys[1]] = ylist 
         
        
    def _get_tag(self):
        if TAG:
            (t, fnos) = lp.Tag().combine(self.df['filename'])
        else:
            (t, fnos) = (None, None)
        self.tag = t
        if fnos is None: fnos = range(len(self.df[0]))
        self.df['no'] = fnos
        
    def flat_field(self):
        fy_list = []
        if 'y_bg' in self.df.columns:
            self.df['y']= self.df['y']-self.df['y_bg']
        else:
            self.df['y']= self.df['y'].apply(lambda x: x-min(x))
         
        self._update_min_max()
        return self
        
    def normalize(self):
        self.df['y'] = self.df['y'].apply(get_norm)
        self._update_min_max()
        return self
        
    def _update_min_max(self):
        self.df['min'] = self.df['y'].apply(lambda x: x.min())
        self.df['max'] = self.df['y'].apply(lambda x: x.max())
        
    def data(self, variable = None, transposed = False, round_lambda = 2):
        if variable is None: variable = self.variable
        l = self.df['x'][0]
        if round_lambda is not None: l = l.round(round_lambda)
            
        if transposed:
            dt = pd.DataFrame(np.stack(self.df['y']).transpose(), columns=self.df[variable], index = l)
        else: 
            dt = pd.DataFrame(np.stack(self.df['y']), index=self.df[variable], columns = l)
        return dt
        
    def mycontour(self, variable =None, *args,  **kwargs):
        if variable is None: variable = self.variable
        plt.contour(self.df['x'][0], self.df[variable], np.stack(self.df['y']), *args, **kwargs)
        cbar = plt.colorbar()
        cbar.set_label('Intensity (count)')
        plt.xlabel(r'$\lambda$ (nm)')
        plt.ylabel (variable)
        put_tag(self.tag)
        
        
    def myplot(self, variable =None, *args, cmap = plt.cm.rainbow, skip=0, shift =0.0, **kwargs):
        if variable is None: variable = self.variable
        vs =self.df[variable]
        colors = get_colors(vs, cmap)
        i=0
        for y,v,c in zip(np.stack(self.df['y']), vs ,colors):
            if i%(skip+1)==0:
                plt.plot(self.df['x'][0], y+i*shift, label = v, color = c, *args, **kwargs)
            i+=1
        plt.ylabel('Intensity (count)')
        plt.xlabel(r'$\lambda$ (nm)')
        plt.legend (title = variable)

        #plt.suptitle(tags[flake] + ': rRef(lambda, Pol_in)', fontsize = 'small', alpha = 1)
        put_tag(self.tag)
        
    def myplot_max(self, variable =None, *args, **kwargs):
        if variable is None: variable = self.variable
        p=plt.plot(self.df[variable], self.df['max'], *args, **kwargs)
        plt.ylabel('Max intensity (count)')
        plt.xlabel(variable)

        #plt.suptitle(tags[flake] + ': rRef(lambda, Pol_in)', fontsize = 'small', alpha = 1)
        put_tag(self.tag)
        return p
    
    def plot_all(self):
        for file in self.df.iloc[:,0]:
            file.plot()
            plt.close()
            
   
    
    def savefig (self, name='plot', transparent = True, dpi = 300, **kwargs):
        _directory = os.path.dirname(self.df[0][0].filepath)
                       
        _directory += r'/Plot/'
        isExist = os.path.exists(_directory)
        if not isExist:
            os.makedirs(_directory)
            print("A new directory is created!")
        
        image_filename = os.path.join(_directory,self.tag+' '+name+'.png')
        plt.savefig(image_filename, transparent = transparent, dpi=dpi, **kwargs)
        return image_filename
    

    
    