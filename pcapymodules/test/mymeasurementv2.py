import numpy as np
import time
import random


class WritePort:
    ## WritePort is a wrapper of an instrument port to set a value and measure.
    # It requires four inputs:
        # (i) The quantity name, for example, voltage, current, temperature, magnetic field, etc.
        # (ii) The unit of the quantity (Optional)
        # (iii) A function of the instrument class that performs the measurement and return the measured value.
        # (iV) A function that perform the set/write operation in the instrument and return the set value.
    def __init__(self, name, unit,  measure_function, set_function):
        self.name = name
        self.unit = unit
        self.measure = measure_function
        self._set_value = set_function
        self.rate = 0.0
        self.step = 0.0
        self.precision = 0.0
        self.min = None
        self.max = None
        self.timeout = 10
        
    
    def get_info(self):
        print ('Name: {}, Unit: {}, \nPresent level: {}, Rate: {}/min, Step: {}, \nMin: {}, Max: {}, \nPrecision: {}, Timeout: {}'
               .format(self.name, self.unit, self.measure(), self.rate, self.step, self.min, self.max, self.precision, self.timeout))
    
    def check_parameter(self, full=True):
        comment = ''
        if self.min == None: 
            comment += '\nMin is not set!'
        elif self.max == None: 
            comment += '\nMax is not set!'
        elif self.min >= self.max: comment += '\nCheck min amd max are set correctly!'
        
        if full:
            if self.rate ==0.0: comment += '\nSet an appropriate rate!'
            if self.step == 0.0: comment += '\nSet an appropriate step value!'
        
        if comment == '':
            return True
        
        else:
            print (comment + '\nPlease rectify and try again.')
            return False
            
        
    def ramp_to(self, target, present = None):
        if present ==None:
            present = self.measure()
            
        if self.check_parameter():
           
            if self.min <= target <= self.max:
                _diff = abs(target-present)
                _rate = abs (self.rate)
                _step = abs (self.step)
                _precision = abs (self.precision)
                
                if _precision == 0.0:
                    _precision = _step/1000.0
                    
                if _precision > _step:
                    _precision = _step
                
                if _diff < _precision:
                    return self._set_value(target)
                
                else: 
                    _time = _diff/ (_rate)
                    if _time >= self.timeout :
                        print ('Setting {} will take long time. Select appropriate rate or change the timeout and try again.'.format(self.name))
                        return present
                    
                    else:
                        _wait = (_step/_rate)*60.0
    
                        if target<present:
                            _step = _step * -1.0
                           
                        _levels = np.arange(present,target,_step)
                        _levels=np.append(_levels, target)
                        
                        for l in _levels[1:]:
                            self._set_value(l)
                            time.sleep(_wait)
                    
                        return target
                    
            else:
                print ('Target {} is out of range! Check min/max and try again.'.format(self.name))
                return present
        else:
            return present
        
    def set_to(self, target, present = None):
        if present ==None:
            present = self.measure()
        if self.check_parameter(False):
            if self.min <= target <= self.max:
               self._set_value(target)
               return target
                    
            else:
                print ('Target {} is out of range! Check min/max and try again.'.format(self.name))
                return present
        else:
            return present
            
class ReadPort:
    """
    ReadPort is a wrapper of an instrument port to read/measure a value from the instrument.
    It requires three inputs:
        (i)     The quantity name, for example, voltage, current, temperature, magnetic field, etc.
        (ii)    The unit of the quantity (Optional)
        (iii)   A function of the instrument class that performs the measurement and return the measured value.
        
    """
    
    def __init__(self, name, unit, measure_function):
        self.name = name
        self.unit = unit
        self.measure = measure_function
        self.inform = False
        
    
    def get_info(self):
        print ('Name: {}, Unit: {}, \nPresent level: {}'
               .format(self.name, self.unit, self.measure()))               


class TestInstrument:
    def __init__(self, name):
         self.name = name  
         print ('Connection to instrument:{} is established.'.format(self.name))
         
         self.output = WritePort('Output', None , self.measure_value, self.set_value)
         self.input = ReadPort('Input', None,  self.measure_random)
         self.port_list = {'write':['output'], 'read':['input']}
         
         self._value = 0.0
         
    def measure_value(self):
        _value = self._value
        print ('At instrument:{} present output = {}'.format(self.name, _value))
        return _value
    
    def set_value(self, value):
        self._value = value
        print ('At instrument:{} setting output  = {}'.format(self.name, value))
        return value    
    
    def measure_random(self):
        _value = random.random()
        print ('At instrument:{} measured input = {}'.format(self.name, _value))
        return _value
         
                
        