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
import warnings
import matplotlib.colors as mcolors
import colorsys
import pdfkit


TAG = False
from scipy.signal import savgol_filter
from scipy.signal import find_peaks

'''
# data frame from kspace matrix
NAMax = 0.8
NA = np.linspace(-NAMax - 0.08, NAMax - 0.08, datum.shape[0])
df = pd.DataFrame(np.round(datum, 5), columns= np.round(energy, 4), index = np.round(NA, 3))
plt.pcolormesh(df.index, np.flipud(df.columns), np.flipud(np.transpose(df.values)),  vmin = -0.35, vmax = 0.35, cmap='inferno')  #ref derivative plot
plt.show()
'''



def save_webpage_as_pdf(url, output_pdf, path_to_wkhtmltopdf='/usr/local/bin/wkhtmltopdf'):
    """
    Save a webpage as a PDF.

    Parameters:
    - url: The URL of the webpage to save.
    - output_pdf: The file name for the output PDF.
    - path_to_wkhtmltopdf: The path to the wkhtmltopdf executable. Default is for Homebrew installation on macOS.
    """
    # Configuration for pdfkit with the path to wkhtmltopdf
    config = pdfkit.configuration(wkhtmltopdf=path_to_wkhtmltopdf)

    # PDF options to ensure the PDF matches the webpage layout
    options = {
        'page-size': 'A4',
        'margin-top': '0in',
        'margin-right': '0in',
        'margin-bottom': '0in',
        'margin-left': '0in',
        'encoding': "UTF-8",
        'no-outline': None
    }

    # Save the webpage as a PDF
    pdfkit.from_url(url, output_pdf, configuration=config, options=options)

# Example usage:
url = "https://physics.umbc.edu/home/events/event/126822/"
output_pdf = "UMBC_Event.pdf"
path_to_wkhtmltopdf = '/usr/local/bin/wkhtmltopdf'  # Adjust this path if necessary

save_webpage_as_pdf(url, output_pdf, path_to_wkhtmltopdf)


def lighten_color(color, amount=0.5):
    """
    Lighten the given color by a certain amount.
    Amount should be a value between 0 (no change) and 1 (white).
    """
    try:
        c = mcolors.cnames[color]
    except KeyError:
        c = color
    rgb = mcolors.to_rgb(c)
    hls = colorsys.rgb_to_hls(*rgb)
    lighter_hls = (hls[0], 1 - amount * (1 - hls[1]), hls[2])
    return colorsys.hls_to_rgb(*lighter_hls)


def single_lorentzian(x, c, a1, x01, w1):
    return c + (a1 / np.pi) * (w1 / ((x - x01)**2 + w1**2))

def double_lorentzian(x, a1, x01, w1, a2, x02, w2):
    return (a1 / np.pi) * (w1 / ((x - x01)**2 + w1**2)) + (a2 / np.pi) * (w2 / ((x - x02)**2 + w2**2))

def my_surfacePlot_in3D(B_index_list, B_list, X, Y, Z_list, YZ_min_max = None, vmin_vmax= None, aspect=[3, 2, 2], Y_ticks = None, Z_ticks = None, font_size = 10, xlabel="B (T)", ylabel=r"$k_{||}/k_0$", zlabel="Energy (eV)"):
    # Your function implementation here
    
    from mpl_toolkits.mplot3d import Axes3D
    from matplotlib.colors import Normalize
    
    plt.rcParams['font.size'] = font_size; plt.rcParams['font.family'] = 'Arial'
    # Set the figure size for a two-column layout
    fig_width_inches = 10 #6.5
    fig_height_inches = fig_width_inches * 0.7  # Adjust the aspect ratio as needed
    

    
    if vmin_vmax is None:
        vmin_vmax = [Z_list[0].min(), Z_list[0].max()]
          
 
    X = X; Y = Y; B_index_list = B_index_list; B_list = B_list; Z_list = Z_list; 
    vmin_vmax = vmin_vmax; aspect = aspect;  xlabel = xlabel; ylabel = ylabel; zlabel = zlabel
    # Create color normalization based on vmin and vmax
    norm = Normalize(vmin=vmin_vmax[0], vmax=vmin_vmax[1])

    # Plotting in 3D
    fig = plt.figure(figsize=(fig_width_inches, fig_height_inches))
    ax = fig.add_subplot(111, projection='3d')

    # Plot each heatmap
    for i, B_index in enumerate(B_index_list):

        #ax.plot_surface(B_list[B_index], Y, X, rstride=1, cstride=1, facecolors = plt.cm.jet(Z_list[i]), vmin=vmin_vmax[0], vmax=vmin_vmax[1], shade=False, alpha=0.5)
        # Plot surface with normalized color array and explicit vmin/vmax order
        ax.plot_surface(B_list[B_index], Y, X, rstride=1, cstride=1, 
                facecolors=plt.cm.inferno(norm(Z_list[i])), vmin=vmin_vmax[0], vmax=vmin_vmax[1], 
                shade=False, alpha=0.5)
        

    ax.set_ylabel(ylabel)
    ax.set_xlabel(xlabel)
    ax.set_zlabel(zlabel)
    ax.view_init(elev=20, azim=-45)
    ax.xaxis.labelpad = 20
    ax.yaxis.labelpad = 10
    
    if YZ_min_max is not None:  # xlim and ylim not working for some reason
       ax.set_ylim(YZ_min_max[0], YZ_min_max[1])
       ax.set_zlim(YZ_min_max[2], YZ_min_max[3])
    
    if Y_ticks is not None:  # xlim and ylim not working for some reason
       ax.set_yticks(Y_ticks)
       
    if Z_ticks is not None:  # xlim and ylim not working for some reason
        ax.set_zticks(Z_ticks)
    
    
    # Create colorbar
    sm = plt.cm.ScalarMappable(cmap='inferno', norm=norm)
    sm.set_array([])
    cbar = fig.colorbar(sm, ax=ax)
    
    # Set position of colorbar
    cbar.ax.set_position([0.9, 0.35, 0.1, 0.3])  # [left, bottom, width, height]

    # Control aspect ratio of x, y, and z axes separately
    ax.set_box_aspect(aspect)  # Aspect ratio for x-axis, y-axis, and z-axis respectively
    

    
    plt.show()
    return(fig, plt)
    
    #To call this function
    
    # x = energy; dx = 0.001; y = NA; dy = 0.02; YZ_min_max = [-0.7, 0.7, 1.6, 1.8]
    # B_list = np.array([0.00, 0.25, 0.50, 0.75, 1.00, 1.25, 1.50, 1.55, 1.60, 1.65, 1.70, 1.75, 1.80, 1.90, 2.00, 2.10, 2.20, 2.50])
    # B_index_list = [0, 5, 15]; 
    # X = an.my_2Dinterp_dx_dy(x, y, dx, dy, DiffRef[B_index_list[0]], YZ_min_max)[0] #interpolated x axis
    # Y = an.my_2Dinterp_dx_dy(x, y, dx, dy, DiffRef[B_index_list[0]], YZ_min_max)[1] #interpolated Y axis
    # Z_list = [an.my_2Dinterp_dx_dy(x, y, dx, dy, DiffRef[B_index], YZ_min_max)[2] for B_index in B_index_list] #interpolated list of data for all field values
    
    # aspect=[1, 0.3, 0.2]
    # vmin_vmax = [-0.4, 0.45]
    # an.my_surfacePlot_in3D(B_index_list, B_list, X, Y, Z_list, vmin_vmax, aspect)



def my_2Dinterp_dx_dy(x, y, dx, dy, z, XY_min_max = None): 
    #Returns an interpolated matrix in an user defined grid
    from scipy.interpolate import interp2d
    
    interpolator = interp2d(x, y, z, kind='linear') #x, y list and z is a matrix
    
    # Define the desired grid size
    grid_size_x = dx #0.0002
    grid_size_y = dy  #0.01
    
    interpolator = interp2d(x, y, z, kind='linear') 
    
    if XY_min_max is not None:
    # Create the regular grid using meshgrid
        X, Y = np.meshgrid(np.arange(XY_min_max[2], XY_min_max[3], grid_size_x), 
                       np.arange(XY_min_max[0], XY_min_max[1], grid_size_y))
    else:
        X, Y = np.meshgrid(np.arange(round(x.min(), 4), round(x.max(), 4), grid_size_x), 
                           np.arange(round(y.min(), 4), round(y.max(), 4), grid_size_y))
            
    # Create an empty matrix to store interpolated values
    interpolated_matrix = np.zeros((X.shape[0], X.shape[1]))

    # Loop through each point in the meshgrid and use interpolated_value
    for i in range(X.shape[0]):
        for j in range(X.shape[1]):
            new_x = X[i, j]
            new_y = Y[i, j]
            interpolated_value = interpolator(new_x, new_y)
            interpolated_matrix[i, j] = interpolated_value
            
    warnings.filterwarnings("ignore", category=DeprecationWarning)        
    return(X, Y, interpolated_matrix)

def my_2Dinterp(x, y, z): 
    #Returns an interpolated matrix with the dimension same as the original
    from scipy.interpolate import interp2d
    
    interpolator = interp2d(x, y, z, kind='linear') #x, y list and z is a matrix
    # Define the desired grid size
    grid_size_x = len(x)
    grid_size_y = len(y)
    
    interpolator = interp2d(x, y, z, kind='linear') 

    # Create the regular grid using meshgrid
    X, Y = np.meshgrid(np.linspace(x.min(), x.max(), grid_size_x), 
                       np.linspace(y.min(), y.max(), grid_size_y))

    # Create an empty matrix to store interpolated values
    interpolated_matrix = np.zeros((grid_size_y, grid_size_x))

    # Loop through each point in the meshgrid and use interpolated_value
    for i in range(grid_size_y):
        for j in range(grid_size_x):
            new_x = X[i, j]
            new_y = Y[i, j]
            interpolated_value = interpolator(new_x, new_y)
            interpolated_matrix[i, j] = interpolated_value
    
    warnings.filterwarnings("ignore", category=DeprecationWarning)        
    return(X, Y, interpolated_matrix)

def my_TiltCorrection(x, y, degree):
    # Perform tilt correction using polynomial fitting
    # degree of the polynomial for fitting (adjust as needed)
    coefficients = np.polyfit(x, y, degree)

    # Generate the fitted curve
    fitted_curve = np.polyval(coefficients, x)

    # Subtract the fitted curve from the original data to correct for tilt
    tilt_corrected_data = y - fitted_curve
    return (tilt_corrected_data, fitted_curve)

def Pol_OneCav_OneExc(Eex, Ecav0, g, n, NAMax, NokPoint):
    kpar = np.linspace(-NAMax, NAMax, NokPoint) #also define in the proggram it is called from
    Eexc = Eex * np.ones(len(kpar)) #also define in the proggram it is called from  
    h = 6.626*10**(-34)
    c = 3.0*10**(8)
    e = 1.602*10**(-19)
    Ecav =  Ecav0 * np.sqrt(n**2 + kpar**2) *h*c/(e*n*1240*10**(-9))

    EUP = 0.5 * (Eex + Ecav + np.sqrt(4*g**2 + (Eex - Ecav)**2))
    ELP = 0.5 * (Eex + Ecav - np.sqrt(4*g**2 + (Eex - Ecav)**2))
    return(Ecav, ELP, EUP)


def my_FFTSmooth(x, y, cutoff):
    # Perform Fourier Transform
    fft_result = np.fft.fft(y)
    # Identify the frequencies corresponding to each component in the Fourier Transform
    frequencies = np.fft.fftfreq(len(y), x[1] - x[0])

    # Create a low-pass filter (set frequencies above cutoff to zero)
    lowpass_filter = np.abs(frequencies) < cutoff

    # Apply the low-pass filter
    fft_result_filtered = fft_result * lowpass_filter

    # Perform Inverse Fourier Transform to get the smoothed data
    smoothed_data = np.fft.ifft(fft_result_filtered).real
        
    return (smoothed_data)


def _put_tag (self):
        _pathname, _extension = os.path.splitext(os.path.basename(self.filepath))
        if TAG: 
            _tag = _pathname
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

def get_flat_norm(y):
    y = get_flat(y)
    y = get_norm(y)
    return y


    
def put_tag(text):
    plt.figtext(0.99, 0.01, text, ha = 'right', color = 'lightgray', fontsize = 'xx-small')


def pixel_to_um (p):
    return 24*p/163

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

def find_fwhm(wavelength, intensity):
    half_max = np.max(intensity) / 2
    indices = np.where(intensity >= half_max)[0]
    fwhm = wavelength[indices[-1]] - wavelength[indices[0]]
    return fwhm
 
def find_highest_peak(x, y, filter_args= {'window_length':9, 'polyorder':2}, find_peak_args={'prominence':0.005, 'height':0.01}, plot =True, cmap =plt.cm.rainbow):
    y_n = (y-min(y))/max((y-min(y)))
    
    y_filter = savgol_filter(y_n, **filter_args)
    
    peaks = find_peaks(y_filter, **find_peak_args)[0]
    peaks = np.append(0,peaks)
    if plot :
        plt.figure(figsize=(16,4))
        plt.plot(x,y_n)
        plt.plot(x, y_filter)
        plt.plot(x[peaks], y[peaks], 'o', label='all peaks', color='lightgrey', zorder=-2)
            
    highest_peak = 0
    y_h = min(y_n)
    for peak in peaks:
        if y_n[peak]>y_h:
            y_h = y_n[peak]
            highest_peak = peak
    return (highest_peak, x[highest_peak], y[highest_peak])
    
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
    
    
class SpeFileSet(FileSet):
    def __init__(self, files, pattern = None, find_text = '', filename = None):
        super().__init__(files, pattern, find_text, filename)
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
    

    
def load_filesets (folders, pattern = None, find_text = ''):
    if isinstance(folders, dict):
        result = {}
        for key in folders:
            result [key] = SpeFileSet(folders[key], pattern = pattern, find_text = find_text)
    elif isinstance(folders, list):
        result = []
        for file in folder:
            result.append = SpeFileSet(file, pattern = pattern, find_text = find_text)
            
    else: raise ValueError('Input must be a list or dictionary of foders.')
            
    return result

def get_colors(List,cmap,start=0):
    n=len(List)
    if start==0:return cmap(np.linspace(0,1,n))
    else:return cmap(np.linspace(1,0,n))
        
def my_FFTSmooth(x, y, cutoff):
    # Perform Fourier Transform
    fft_result = np.fft.fft(y)
    # Identify the frequencies corresponding to each component in the Fourier Transform
    frequencies = np.fft.fftfreq(len(y), x[1] - x[0])

    # Create a low-pass filter (set frequencies above cutoff to zero)
    lowpass_filter = np.abs(frequencies) < cutoff

    # Apply the low-pass filter
    fft_result_filtered = fft_result * lowpass_filter

    # Perform Inverse Fourier Transform to get the smoothed data
    smoothed_data = np.fft.ifft(fft_result_filtered).real
        
    return (smoothed_data)