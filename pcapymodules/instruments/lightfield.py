#### IMPORT MODULES ###########################################################

# Import the .NET class library
# To install follow https://pypi.org/project/pythonnet/
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
from PrincetonInstruments.LightField.AddIns import RegionsOfInterestSelection

import time
from ctypes import *
#import types
import re

###############################################################################
class LFConfig:
    def __init__(self, exposure_time, wavelength, roi = 1, average = 1, grating=None, grating_list = ['[500nm,1200][0][0]','[500nm,600][1][0]','[500nm,300][2][0]']):
        self.exposure_time = exposure_time
        self.wavelength = wavelength
        self.roi = roi     
        self.average = average
        self.grating_list = grating_list
        self.grating = grating

        

class LFApplication:
    NumberTypes = (int,float)
    # INITIALIZATION
    def __init__(self):
        print('LFExperiment class initialization started')
        # Create the LightField Application (true for visible)
        # The 2nd parameter forces LF to load with no experiment
        self.auto = Automation(True, List[String]())
        
        # Get experiment object
        self.application = self.auto.LightFieldApplication
        self.experiment = self.application.Experiment
        
        self.silent = True
        self.config = None
        
        #self.file_manager = self.application.FileManager
        self.acquireCompleted = AutoResetEvent(False)
        
        time.sleep(3)
        
        print('LFExperiment class initialization finished')
        
    # EXPERIMENTS PARAMETERS
    @property
    def exposure_time(self):
        return self.get_value(CameraSettings.ShutterTimingExposureTime)
    
    @exposure_time.setter
    def exposure_time(self, value):
        self.set_value(CameraSettings.ShutterTimingExposureTime, value*1.0)
        
    @property
    def average(self):
        return self.get_value(ExperimentSettings.OnlineProcessingFrameCombinationFramesCombined)
    @average.setter
    def average(self,value):
        if isinstance(value, self.NumberTypes):
            self.set_value(ExperimentSettings.OnlineProcessingFrameCombinationFramesCombined, str(value))
            
    @property
    def grating(self):
        return self.get_value(SpectrometerSettings.GratingSelected)
    @grating.setter
    def grating(self,value):
        if isinstance(value, self.NumberTypes):
            for s in self.grating_list:
                numbers = re.findall(r'\d+',s)
                numbers = [int(num) for num in numbers]
                g = numbers[1]
                print (g)
                if g==value:
                    self.set_value(SpectrometerSettings.GratingSelected, s)
                    break
       
        
    @property
    def region_of_interest(self):
        return self.get_value(CameraSettings.ReadoutControlRegionsOfInterestSelection)
    @region_of_interest.setter
    def region_of_interest(self,value):
        # 1 = Full sensor
        # 2 = Full sensor binned
        # 3 = Rows binned
        # 4 = Custom ROI
        if 0<value<5:
            self.set_value(CameraSettings.ReadoutControlRegionsOfInterestSelection, RegionsOfInterestSelection(value)) 
        else:
            print('Provide valid selection for region of interest!')
        
    @property
    def wavelength(self):
        if self.get_value(ExperimentSettings.StepAndGlueEnabled):
            _start =self.get_value(ExperimentSettings.StepAndGlueStartingWavelength)
            _end=self.get_value(ExperimentSettings.StepAndGlueEndingWavelength)
            return (_start, _end)
        
        else:
            return self.get_value(SpectrometerSettings.GratingCenterWavelength)
    
    @wavelength.setter
    def wavelength(self, value):
        if isinstance(value, self.NumberTypes):
            self.set_center_wavelength(value)
            
        elif isinstance(value, tuple):
            self.set_step_and_glue(value[0], value[1])
            self.set_value(ExperimentSettings.FileNameGenerationSaveRawData,False)
    
    @property
    def file_name(self):
        return self.experiment.GetValue(ExperimentSettings.FileNameGenerationBaseFileName)
    
    @file_name.setter
    def file_name(self, filename):
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
          
    @property
    def file_directory(self):
        return self.experiment.GetValue(ExperimentSettings.FileNameGenerationDirectory)
         
    @file_directory.setter      
    def file_directory(self, directory):    
        # Set the base file directory
        self.experiment.SetValue(
            ExperimentSettings.FileNameGenerationDirectory, directory)
    
    @property
    def file_path(self):
        _file_name=self.file_name
        _file_directory=self.file_directory
        return _file_directory + r'\\'+_file_name + '.spe'
    
    @file_path.setter
    def file_path(self, filepath):
        (directory, filename) = os.path.split (filepath)
        print(directory)
        self.file_name =filename
        if directory != '':
            self.file_directory = directory
    
        
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
    
            
    
    # GETTING VALUES
    
    def print_setting(self,setting):
        # Check for existence before
        # getting gain, adc rate, or adc quality
        if self.experiment.Exists(setting):
            print(String.Format('{0} {1} = {2}', "\tReading ", str(setting), self.experiment.GetValue(setting)))

    def get_value(self, setting):
        return self.experiment.GetValue(setting)

    def get_grating(self, *args):
        return self.get_value(SpectrometerSettings.GratingSelected)

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
       
    
    # SETTING VALUES

    def set_value(self, setting, value):
        if self.experiment.Exists(setting):
            self.experiment.SetValue(setting, value)
            if not self.silent: print(String.Format('{0} {1} = {2}', "\tSet ", str(setting), str(value)))

    def set_center_wavelength(self, center_wave_length):
        self.set_value(ExperimentSettings.StepAndGlueEnabled, False)
        self.set_value(SpectrometerSettings.GratingCenterWavelength, center_wave_length*1.0)
           
    def set_step_and_glue(self, start_wave_length=None, end_wave_length=None): 
        # Set the spectrometer center wavelength   
        self.set_value(ExperimentSettings.StepAndGlueEnabled, True)
        if start_wave_length != None:
            self.set_value(ExperimentSettings.StepAndGlueStartingWavelength,start_wave_length*1.0)
        if end_wave_length != None:
            self.set_value(ExperimentSettings.StepAndGlueEndingWavelength,end_wave_length*1.0)
        
    def set_configuration(self, config = None):
        if config is not None: 
            self.config = config
        if config.exposure_time is not None:
            self.exposure_time = config.exposure_time
        if config.roi is not None:
            self.region_of_interest = config.roi
        if config.wavelength is not None:
            self.wavelength = config.wavelength
        if config.average is not None:
            self.average = config.average
        if config.grating_list is not None:
            self.grating_list = config.grating_list
        if config.grating is not None:
            self.grating = config.grating
        
    # ACQUISITION

    def _acquire_new(self, timeout=30000): 
        ## Changes to avoid stalling on acquisition       
        self._handler_delegate = self.experiment_completed  # protect from GC
        self.experiment.ExperimentCompleted += self._handler_delegate
        try:
            if not self.experiment.IsReadyToRun:
                print("Experiment not ready. Skipping acquisition.")
                return

            print("Acquiring data...")
            self.experiment.Acquire()

            acquired = self.acquireCompleted.WaitOne(timeout)  # timeout after 30s
            if not acquired:
                for i in range (3):
                    print("Acquisition timeout. Wait more and try again - %d."%i)
                    time.sleep(3)
                    self.experiment.Acquire()
                    acquired = self.acquireCompleted.WaitOne(timeout)  # timeout after 30s
                    if acquired:
                        print("Acquisition completed after retry.")
                        break

        finally:
            self.experiment.ExperimentCompleted -= self._handler_delegate

        print(self.file_name)

    
    def _acquire (self, timeout=30000):        
        self.experiment.ExperimentCompleted += self.experiment_completed
        try:
            self.experiment.Acquire()
            print("Acquiring data...")
            self.acquireCompleted.WaitOne(timeout) 
        finally:
            self.experiment.ExperimentCompleted -= self.experiment_completed
            
        print (self.file_name)

    
    def acquire(self,  filepath=None, config = None, timeout = 30000):
        if config is not None:
            self.set_configuration(config)
            
        if filepath is not None:
            self.file_path = filepath
        
        self._acquire_new(timeout)
        
        return filepath


    def abort(self, *args):
        if self.device_found():
            self.experiment.Abort()
  
    def experiment_completed(self, sender, event_args):
        print("Acquisition complete.")
        self.acquireCompleted.Set()
        
    

