#### IMPORT MODULES ###########################################################

# Import the .NET class library
import clr

# Import python sys module
import sys

# Import os module
import os

# Import System.IO for saving and opening files
from System.IO import *

from System.Threading import AutoResetEvent


# Import C compatible List and String
from System import String
from System.Collections.Generic import List

# Add needed dll references
sys.path.append(os.environ['LIGHTFIELD_ROOT'])
sys.path.append(os.environ['LIGHTFIELD_ROOT']+"\\AddInViews")
clr.AddReference('PrincetonInstruments.LightFieldViewV5')
clr.AddReference('PrincetonInstruments.LightField.AutomationV5')
clr.AddReference('PrincetonInstruments.LightFieldAddInSupportServices')
clr.AddReference("System")

# PI imports
from PrincetonInstruments.LightField.Automation import Automation
from PrincetonInstruments.LightField.AddIns import SpectrometerSettings
from PrincetonInstruments.LightField.AddIns import DeviceType
from PrincetonInstruments.LightField.AddIns import ExperimentSettings
from PrincetonInstruments.LightField.AddIns import CameraSettings
from PrincetonInstruments.LightField.AddIns import RegionOfInterest
from PrincetonInstruments.LightField.AddIns import RegionsOfInterestSelection

import matplotlib.pyplot as plt
import numpy as np
import logging
import time
from ctypes import *

import spe_loader as sl

###############################################################################

logger = logging.getLogger(__name__)


class LFApplication:

    # INITIALIZATION
    def __init__(self):
        logger.debug('LFExperiment class initialization started')
        print('LFExperiment class initialization started')
        # Create the LightField Application (true for visible)
        # The 2nd parameter forces LF to load with no experiment
        self.auto = Automation(True, List[String]())
        
        # Get experiment object
        self.application = self.auto.LightFieldApplication
        self.experiment = self.application.Experiment
        
        self.info = MeasurementInfo()
        
        self.file_manager = self.application.FileManager
        self.acquireCompleted = AutoResetEvent(False)
        
        self.experiment.SetValue(
            ExperimentSettings.FileNameGenerationSaveRawData,False)
        
        
        time.sleep(3)
        
        
        logger.debug('LFExperiment class initialization finished')
        print('LFExperiment class initialization finished')
    
        
    # DEVICE MANAGEMENT
    def device_found(self):
        # Find connected device
        for device in self.experiment.ExperimentDevices:
            if device.Type == DeviceType.Camera:
                return True

        # If connected device is not a camera inform the user
        print("Camera not found. Please add a camera and try again.")
        return False
    
    def add_available_devices(self):
        if (self.experiment.AvailableDevices.Count == 0):
            print("Device not found. Please add a device and try again.")
            return None
        else:
            # Add first available device and return
            for device in self.experiment.AvailableDevices:
                print("\n\tAdding a device...")
                self.experiment.Add(device)
                return device
                      
    def remove_all_devices(self):
        i=0
        for device in self.experiment.ExperimentDevices:
            print("\n\tRemoving Device...")
            self.experiment.remove(device)
            i+=1
        return i
        
    # SETTING VALUES

    def set_value(self, setting, value):
        if self.experiment.Exists(setting):
            self.experiment.SetValue(setting, value)
            print(String.Format('{0} {1} = {2}', "\tSet ", str(setting), str(value)))

    def set_exposure_time(self, value):
        logger.debug('Called set_exposure_time directly! Exposure time: ' + str(value))
        self.set_value(CameraSettings.ShutterTimingExposureTime, value*1.0)
        self.info.spctrometer.exposure_time = str(value)+'ms'

    def set_center_wavelength(self, center_wave_length=0):
        logger.debug('Called set_center_wavelength directly! wavelength: ' + str(center_wave_length))
        self.set_value(ExperimentSettings.StepAndGlueEnabled, False)
        self.set_value(SpectrometerSettings.GratingCenterWavelength, center_wave_length*1.0)
        self.info.spctrometer.wavelength = str(center_wave_length)+'nm'
    
    def set_step_and_glue(self, start_wave_length=None, end_wave_length=None): 
        logger.debug('Called set_step_and_glue! start_wave_length: ' + str(start_wave_length) + 'end_wave_length' + str(end_wave_length))
        # Set the spectrometer center wavelength   
        self.set_value(ExperimentSettings.StepAndGlueEnabled, True)
        _wavelength =''
        if start_wave_length != None:
            self.set_value(ExperimentSettings.StepAndGlueStartingWavelength,start_wave_length*1.0)
            _wavelength += str(start_wave_length) +'-'
        if end_wave_length != None:
            self.set_value(ExperimentSettings.StepAndGlueEndingWavelength,end_wave_length*1.0)
            _wavelength += str(end_wave_length) +'nm'
        self.info.spctrometer.wavelength = _wavelength
            
    def set_ROI (self,value=1):
        # 1 = Full sensor
        # 2 = Full sensor binned
        # 3 = Rows binned
        # 4 = Custom ROI
        if 0<value<5:
            self.set_value(CameraSettings.ReadoutControlRegionsOfInterestSelection, RegionsOfInterestSelection(value)) 
            self.info.spctrometer.roi = value
        else:
            print('Provide valid selection for region of interest!')
            
            
    def set_custom_ROI(self):
        #PCA notes: make arguments of region integers - otherwise there will be error
        # Get device full dimensions
        dimensions = self.get_device_dimensions()
            
        regions = []
        
        # Add two ROI to regions
        regions.append(
            RegionOfInterest
            (dimensions.X, dimensions.Y,
             dimensions.Width, dimensions.Height,
             dimensions.XBinning, dimensions.YBinning))
        
        regions.append(
            RegionOfInterest
            (dimensions.X, dimensions.Height,
             dimensions.Width, dimensions.Height,
             dimensions.XBinning, dimensions.YBinning))
    
        # Set both ROI
        self.experiment.SetCustomRegions(regions)
    
        # Display the dimensions for each ROI
        for roi in regions:
            self.print_region(roi)    

    def set_file_name(self, filename):    
        # Set the base file name
        self.experiment.SetValue(
            ExperimentSettings.FileNameGenerationBaseFileName,
            Path.GetFileName(filename))
        
        # Option to Increment, set to false will not increment
        self.experiment.SetValue(
            ExperimentSettings.FileNameGenerationAttachIncrement,
            False)
    
        # Option to add date
        self.experiment.SetValue(
            ExperimentSettings.FileNameGenerationAttachDate,
            False)
    
        # Option to add time
        self.experiment.SetValue(
            ExperimentSettings.FileNameGenerationAttachTime,
            False)
    def set_file_directory(self, directory):    
        # Set the base file directory
        self.experiment.SetValue(
            ExperimentSettings.FileNameGenerationDirectory, Path.GetDirectoryName(directory))
        
    
    # GETTING VALUES
    
    def print_setting(self,setting):
        # Check for existence before
        # getting gain, adc rate, or adc quality
        if self.experiment.Exists(setting):
            print(String.Format('{0} {1} = {2}', "\tReading ", str(setting), self.experiment.GetValue(setting)))
        
    def get_spectrometer_info(self, *args):
        logger.debug('Called get_spectrometer_info directly! Args: ' + str(args))
        print(String.Format("{0} {1}", "Center Wave Length:",
                            str(self.experiment.GetValue(SpectrometerSettings.GratingCenterWavelength))))
        print(String.Format("{0} {1}", "Grating:", str(self.experiment.GetValue(SpectrometerSettings.Grating))))
        return "Function Completed"

    def get_value(self, setting):
        return self.experiment.GetValue(setting)

    def get_grating(self, *args):
        logger.debug('Called get_grating directly! Args: ' + str(args))
        return self.get_value(SpectrometerSettings.GratingSelected)

    def get_center_wavelength(self, *args):
        logger.debug('Called get_center_wavelength directly! Args: ' + str(args))
        return self.get_value(SpectrometerSettings.GratingCenterWavelength)

    def get_exposure_time(self, *args):
        logger.debug('Called get_exposure_time directly! Args: ' + str(args))
        return self.get_value(CameraSettings.ShutterTimingExposureTime)

    def all_methods(self, cls):
        method_list = [func for func in dir(cls) if callable(getattr(cls, func))]
        return method_list
    
    def get_device_dimensions(self):
        return self.experiment.FullSensorRegion
    
    def print_region(self,region):
        print("Custom Region Setting:")
        print(String.Format("{0} {1}", "\tX:", region.X))
        print(String.Format("{0} {1}", "\tY:", region.Y))
        print(String.Format("{0} {1}", "\tWidth:", region.Width))
        print(String.Format("{0} {1}", "\tHeight:", region.Height))
        print(String.Format("{0} {1}", "\tXBinning:", region.XBinning))
        print(String.Format("{0} {1}", "\tYBinning:", region.YBinning))
        
    def get_file_name(self):
        return self.experiment.GetValue(ExperimentSettings.FileNameGenerationBaseFileName)
    
    def get_file_directory(self):
        return self.experiment.GetValue(ExperimentSettings.FileNameGenerationDirectory)
    
    def get_full_file_path(self):
        _file_name=self.get_file_name()
        _file_directory=self.get_file_directory()
        return _file_directory + r'//'+_file_name + '.spe'
    
    
    # DATA MANAGEMENT
    def move_spe(self, *args):
        home_directory = r'C:\Users\PHOTNCS03.LAB\Documents\LightField'
        new_directory = r'C:\Users\PHOTNCS03.LAB\Desktop\LIGHTFIELD SCANS'
        for filename in os.listdir(home_directory):
            if os.path.splitext(filename)[1] == '.spe':
                print('Moving: ' + filename)
                os.rename(os.path.join(home_directory, filename), os.path.join(new_directory, filename))
    
    
    def get_file_description(self):
        _file_description =String.Format("{0} {1}{2}", self.info.spot, self.info.space, self.info.light.type)

            
        if self.info.spctrometer.wavelength != None:
            _file_description += ", " + self.info.spctrometer.wavelength
        
        if self.info.spctrometer.exposure_time != None:
            _file_description += ", " + self.info.spctrometer.exposure_time
            
        if self.info.light.source != None:
            _file_description += ", " + self.info.light.source
            
        if self.info.light.input_path != None:
            _file_description += ", " + self.info.light.input_path
            
        if self.info.light.output_path != None:
            _file_description += ", " + self.info.light.output_path

        if self.info.comment != None:
            _file_description += ', '+ self.info.comment 
        return _file_description
    
    def generate_file_name (self, project):
        _file_code = project.get_file_code()
        _file_description = self.get_file_description()
        return _file_code + ' ' + _file_description  
        
    # ACQUISITION
    
    def acquire(self):
        logger.debug('Called acquire_data directly!')
        self.experiment.ExperimentCompleted += self.experiment_completed
        try:
            self.experiment.Acquire()
            print("Acquiring data...")
            self.acquireCompleted.WaitOne() 
        finally:
            self.experiment.ExperimentCompleted -= self.experiment_completed
            
    def take_k_space(self, project, light, frame=0, roi=0, save = True, cmap='hot'):
        self.set_ROI(1)
       
        self.info.space = 'k'
        self.info.light= light
        
        filename =self.generate_file_name(project) 
        self.set_file_name(filename)    
        
        self.acquire()
        
        print (filename)
        self.plot_image(frame, roi, save, cmap)
        
    def take_r_space(self, project, light, frame=0, roi=0, save = True):
        self.set_ROI(3)
       
        self.info.space = 'r'
        self.info.light= light
        
        filename =self.generate_file_name(project) 
        self.set_file_name(filename)    
        
        self.acquire()
        
        print (filename)
        self.plot_spectrum(frame, roi, save)

    def abort(self, *args):
        logger.debug('Called abort directly! Args: ' + str(args))
        if self.device_found():
            self.experiment.Abort()
  
    def experiment_completed(self, sender, event_args):
        print("Acquisition complete.")
        self.acquireCompleted.Set()
        
    # FILE ACCESS
    def get_spectrum(self, frame=0, roi=0):
        _filename = self.get_full_file_path()
        _file = SpeFile (_filename)
        return _file.get_spectrum(frame, roi)

    def get_image_data(self, frame=0, roi=0):
        _filename = self.get_full_file_path()
        _file = SpeFile (_filename)
        return _file.get_image_data(frame, roi)
    
    # PLOTTING
    def plot_spectrum(self, frame=0, roi=0, save=True):
        _filename = self.get_full_file_path()
        _file = SpeFile (_filename)
        _file.plot_spectrum(frame, roi, save)

    def plot_image(self, frame=0, roi=0, save=True, cmap = 'hot'):
        _filename = self.get_full_file_path()
        _file = SpeFile (_filename)
        _file.plot_image(frame, roi, save, cmap)
        
class SpeFile (sl.SpeFile):

    def get_spectrum(self, frame=0, roi=0):
        _x = self.wavelength.transpose()
        _y = self.data[frame][roi][0].transpose()
        return [_x,_y]
    
    def get_image_data(self, frame=0, roi=0):
        _x = self.wavelength.transpose()
        _z = self.data[frame][roi]
        return [_x,_z]
    
    def plot_spectrum(self, frame=0, roi=0, save=True):
        _pathname, _extension = os.path.splitext(os.path.basename(self.filepath))
        _directory = os.path.dirname(self.filepath)

        [_x,_y]=self.get_spectrum(frame=0, roi=0)
        
        plt.figure(figsize=(6,4))
        plt.plot(_x,_y)
        plt.xlabel('$\lambda$ (nm)')
        plt.ylabel('Intensity (a.u.)')
        
        _directory += r'/Plot/'
        isExist = os.path.exists(_directory)
        if not isExist:
            # Create a new directory because it does not exist
            os.makedirs(_directory)
            print("The new directory is created!")
        if save: plt.savefig(_directory+_pathname+'.png', transparent = True)
    
    def plot_image(self, frame=0, roi=0, save = True, cmap='hot'):
        _pathname, _extension = os.path.splitext(os.path.basename(self.filepath))
        _directory = os.path.dirname(self.filepath)

        [_x,_y]=self.get_image_data()
        
        plt.figure(figsize=(6,4))
        img=plt.imshow(_y, cmap=cmap, aspect='auto', extent=(_x[0],_x[-1], 0, np.shape(_y)[0]))
        
        plt.xlabel('$\lambda$ (nm)')
        plt.ylabel('Row')
        
        _directory += r'/Plot/'
        isExist = os.path.exists(_directory)
        if not isExist:
            # Create a new directory because it does not exist
            os.makedirs(_directory)
            print("The new directory is created!")
        if save: plt.savefig(_directory+_pathname+'.png', transparent = True)
        
        return img
    
        
        


        
class MeasurementInfo:
    def __init__(self):
        self.type = 'Ref'
        self.spctrometer= _SpectrometerInfo()
        self.light = LightInfo()
        self.space ='r'
        self.spot = 'Unknown'
        self.comment = None
        

class _SpectrometerInfo:
    def __init__(self):
        self.exposure_time = None
        self.wavelength = None
        self.frameno=1
        self.roi = 1


        
class LightInfo:
    def __init__(self, source='Unknown', measurement_type='Unknown'):
        self.source = source
        self.input_path = None
        self.output_path = None
        self.type = measurement_type     
    
        
def launch_lightfield ():
    application=LFApplication()
    return application

