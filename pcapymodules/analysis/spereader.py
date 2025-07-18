# -*- coding: utf-8 -*-
"""
Created on Sat Dec 17 23:58:27 2022

@author: Pratap Chandra Adak
@version: 1

This is module to read and manipulate .spe files generated from Princeton 
This requires the follwoing package to be installed:
    numpy
    matplotlib
    scp2py: Install from https://pypi.org/project/spe2py/
"""
# Import os module
import os
import re
import matplotlib.pyplot as plt
import numpy as np

# Install from https://pypi.org/project/spe2py/
from . import spe_loader as sl
##

class SpeFile (sl.SpeFile):
    '''
    This is a class that holds an .spe file from a given filepath
    '''
    def _get_roi_info(self):
        """
        Returns region of interest attributes and numbers of regions of interest
        """
        try:
            camerasettings = self.footer.SpeFormat.DataHistories.DataHistory.Origin.Experiment.Devices.Cameras.Camera
            #regionofinterest = camerasettings.ReadoutControl.RegionsOfInterest.CustomRegions.RegionOfInterest
            #In original class this was always referring to custom regions 
            #which gives error if custom region is different than used region
            regionofinterest = camerasettings.ReadoutControl.RegionsOfInterest.children[-1].children
            
        except AttributeError:
            print("XML Footer was not loaded prior to calling _get_roi_info")
            raise

        if isinstance(regionofinterest, list):
            nroi = len(regionofinterest)
            roi = regionofinterest
        else:
            nroi = 1
            roi = [regionofinterest]  # cast element to list for consistency

        return roi, nroi
    
    
    @property
    def central_wavelength(self):
        s=self.footer.SpeFormat.DataHistories.DataHistory.Origin.Experiment.Devices.Spectrometers.Spectrometer.Grating.CenterWavelength.cdata
        return float(s)
    
    @property
    def image_mode(self):
        if self.central_wavelength <1:
            return True
        else: return False
        
    def get_spectrum (self, frame=0, roi = 0, row=None):
        '''
        This generates the single spectrum from a SpeFile

        Parameters
        ----------
        frame : TYPE = Integer, optional
            DESCRIPTION. The default is 0.
        roi : TYPE = Integer, optional
            DESCRIPTION. The default is 0.
        row : TYPE = Integer, optional
            DESCRIPTION. The default is None. In that case the middle row will be chosen if there are multiple.
        
        Returns
        -------
        (x,y) array -> x is wavelength, y is intensity

        '''
        x = self.xcoord[0]
        
        if self.central_wavelength > 0 and  self.wavelength is not None:
            x=self.wavelength
        y = self.data[frame][roi]
        if row == None:
            row = int(y.shape[0]/2)
            
        #print (len(x), len(y[row]))
        if len(x) == len(y[row]):   
            return (x,y[row].astype(np.int32))
        else:   
            return (x[self.xcoord[0]],y[row].astype(np.int32))
    
    def plot_spectrum (self, frame=0, roi = 0, row=None, **kwargs):
        '''
        This plots the single spectrum from a SpeFile

        Parameters
        ----------
        frame : TYPE = Integer, optional
            DESCRIPTION. The default is 0.
        roi : TYPE = Integer, optional
            DESCRIPTION. The default is 0.
        row : TYPE = Integer, optional
            DESCRIPTION. The default is None. In that case the middle row will be chosen if there are multiple.
        **kwargs : TYPE
            DESCRIPTION. keywords used for plt.plot

        Returns
        -------
        Plot

        '''
        x,y = self.get_spectrum( frame, roi, row)
        p = plt.plot(x,y,**kwargs)
        if self.image_mode:
            plt.xlabel('Position X')
        else: 
            plt.xlabel('$\lambda$ (nm)')
        plt.ylabel('Intensity (a.u.)')
        return p
    
    
    def get_image (self, frame=0, roi = 0):
        x = self.wavelength
        if self.central_wavelength == 0 or x is None:
            x=self.xcoord[0]
        z = self.data[frame][roi]
        nrow = z.shape[0]
        y = np.array(range(nrow))
        #Y = np.tile(range(nrow), (len(x),1)).transpose()
        return (x,y,z)

    def plot_image (self, frame=0, roi = 0, cmap='binary_r', levels = 100, cropx=None, cropy=None, **kwargs):
        x,y,z =  self.get_image (frame, roi)
        
        if cropx is not None:
            if len(cropx) == 2:
                x= x[cropx[0]:cropx[1]]
                z= z[:,cropx[0]:cropx[1]]
                
        if cropy is not None:
            if len(cropy) == 2:
                x= x[cropy[0]:cropy[1]]
                z= z[:,cropy[0]:cropy[1]]
        
        plt.contourf(x,y,z, cmap = cmap, levels = levels, **kwargs)
        if self.image_mode:
            plt.xlabel('Position X')
        else: 
            plt.xlabel('$\lambda$ (nm)')
        plt.ylabel('Position Y')
        plt.colorbar()
        
    def plot(self, frame = 0, roi = 0, row=None,  save = True, cropx=None, cropy=None, **kwargs):
        data = self.data[frame][roi]
        lineno = data.shape[0]
        if lineno < 2:
            #print ('Plotting 1D line plot')
            self.plot_spectrum (frame, roi, row, **kwargs)
        else:
            #print ('Plotting image plot')
            self.plot_image (frame, roi, cropx=cropx, cropy=cropy, **kwargs)
    
        if save:
            self.save_plot()
        
    def save_plot(self, extension = '.png'):
        _pathname, _extension = os.path.splitext(os.path.basename(self.filepath))
        _directory = os.path.dirname(self.filepath)
        
        self.customize()
               
        _directory += r'/Plot/'
        isExist = os.path.exists(_directory)
        if not isExist:
            # Create a new directory because it does not exist
            os.makedirs(_directory)
            print("The new directory is created!")
        
        image_filename = _directory+_pathname+extension
        plt.savefig(image_filename, transparent = True, dpi = 300)
        return image_filename
    
    def customize (self):
        pass
    


from .loadfile import *
def load_file(filepath):
    return SpeFile(filepath)


LoadFile.load_function = load_file


    



        
        
        

    