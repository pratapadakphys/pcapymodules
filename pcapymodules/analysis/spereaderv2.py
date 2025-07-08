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
from .. import lanmpprojectv2 as lp

# Install from https://pypi.org/project/spe2py/
import spe_loader as sl
import spe2py as spe


class SpeFile (sl.SpeFile):
    '''
    This is a class that holds an .spe file from a given filepath
    '''
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
        x = self.wavelength
        if self.central_wavelength == 0:
            x=self.xcoord[0]
        y = self.data[frame][roi]
        if row == None:
            row = int(y.shape[0]/2)
        return (x,y[row])
    
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
        if self.central_wavelength == 0:
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
        
    def save_plot(self, extension = '.png', tag = True):
        _pathname, _extension = os.path.splitext(os.path.basename(self.filepath))
        _directory = os.path.dirname(self.filepath)
        
        if tag:
            _tag = lp.get_tag(_pathname)
            plt.gcf().text(0.95,0.01,_tag, size = 'xx-small', color='lightgrey', horizontalalignment = 'right')        
        _directory += r'/../Plot/'
        isExist = os.path.exists(_directory)
        if not isExist:
            # Create a new directory because it does not exist
            os.makedirs(_directory)
            print("The new directory is created!")
        
        image_filename = _directory+_pathname+extension
        plt.savefig(image_filename, transparent = True, dpi = 300)
        return image_filename
    
    
def load_files_by_gui():
    file_paths = spe.get_files(True)
    batch = load_files(file_paths)
    return batch
    
    
def load_files(filepaths=None):
    """
    Allows user to load multiple files at once. Each file is stored as an SpeFile object in the list batch.
    """
    if filepaths is None:
        file_paths = spe.get_files(True)
        batch = load_files(file_paths)
        return batch
    if type(filepaths) is list:
        batch = [[] for _ in range(0, len(filepaths))]
        for file in range(0, len(filepaths)):
            batch[file] = SpeFile(filepaths[file])
        return_type = "list of SpeFile objects"
        if len(batch) == 1:
            batch = batch[0]
            return_type = "SpeFile object"
        print('Successfully loaded %i file(s) in a %s' % (len(filepaths), return_type))
        return batch
    elif os.path.isdir(filepaths):
        files = []
        for f in os.listdir(filepaths):
            if re.search('.spe', f):
                files.append(SpeFile(filepaths + r'//' + f))
        return_type = "list of SpeFile objects"
        print('Successfully loaded %i file(s) in a %s' % (len(files), return_type))
        return files
    else: return SpeFile(filepaths)
        