from NKTP_DLL import *
import types
import numpy as np

NumberTypes = (int, float)
ListTypes = (list,np.ndarray)

class SuperK:

    def __init__(self, port = 'COM5', rf_module = 18, silent=False):
        '''
        To switch from Visible to NIR range switch rf_nodule number from 18 to 22 or vice versa.
        For Montana PC port is 'COM5', for Olympus PC it is 'COM17'.
        '''
        self.port = port
        self.rf_module = rf_module
        self.silent = silent
        
    def turn_emission_on(self):
        result = registerWriteU8(self.port, 15, 0x30, 0x03, -1)
        r=RegisterResultTypes(result)
        if not self.silent: print('Setting emission ON - Extreme:', r)
        return r
        
    def turn_emission_off(self):
        result = registerWriteU8(self.port, 15, 0x30, 0x0, -1)
        r=RegisterResultTypes(result)
        if not self.silent: print('Setting emission OFF - Extreme:', r)
        return r
        
    def set_operation_mode(self, mode=1):
        '''
        0: Constant current mode
        1: Constant power mode
        2: Externally modulated current mode
        3: Externally modulated power mode
        4: External feedback mode (Power Lock)
        '''
        
        m=0x0
        if mode==1:
            m=0x01
        result = registerWriteU8(self.port, 15, 0x31, m, -1)
        r=RegisterResultTypes(result)
        if not self.silent: print('Setting operation mode - Extreme:', r)
        return r
        


    def set_power_level(self, value=0):
        p=(int(value*10))
        result = registerWriteU16(self.port, 15, 0x37, p, -1)
        r=RegisterResultTypes(result)
        if not self.silent: print('Setting power level - Extreme:', r)
        return r

    def set_rf_on(self):
        result = registerWriteU8(self.port, self.rf_module, 0x30, 0x01, -1)
        r=RegisterResultTypes(result)
        if not self.silent: print('Setting RF power ON - SuperK SELECT:', result, r)
        return r
        
    def set_rf_off(self):
        result = registerWriteU8(self.port, self.rf_module, 0x30, 0, -1)
        r=RegisterResultTypes(result)
        if not self.silent: print('Setting RF power OFF - SuperK SELECT:', result, r)
        return r
        
    def set_rf_amplitude(self, value=0):
        if isinstance (value, NumberTypes):
            p=(int(value*10))
            result = registerWriteU16(self.port, self.rf_module, 0xB0, p, -1)
            r=RegisterResultTypes(result)
            if not self.silent: print('Setting amplitude level - SuperK SELECT:', r)
            return r
        elif isinstance (value, ListTypes):
            i= 0; r=[]
            for v in value:
                if i>7: break
                p=(int(v*10))
                result = registerWriteU16(self.port, self.rf_module, 0xB0+i, p, -1)
                r.append(RegisterResultTypes(result))
                i+=1
                
            if not self.silent: print('Setting amplitude level - SuperK SELECT:', r)
            return r
        
    def set_wavelength(self, value=0):
        
        if isinstance (value, NumberTypes):
            l=(int(value*1000))
            result = registerWriteU32(self.port, self.rf_module, 0x90, l, -1)
            r=RegisterResultTypes(result)
            if not self.silent: print('Setting wavelength - SuperK SELECT:', r)
            return r
        
        elif isinstance (value, ListTypes):
            i= 0; r=[]
            for v in value:
                if i>7: break
                l=(int(v*1000))
                result = registerWriteU32(self.port, self.rf_module, 0x90+i, l, -1)
                i+=1
                r.append(RegisterResultTypes(result))
            if not self.silent: print('Setting wavelength level - SuperK SELECT:', r)
            return r
            
    def set_band(self, center, bw=10):
        l=center
        dbw=bw/6
        self.set_wavelength([l-3*dbw,l-2*dbw,l-dbw,l, l+dbw, l+2*dbw, l+3*dbw,l])
        self.set_rf_amplitude([100,100,100,100,100,100,100,100])
        
    def set_band_power(self, center, power=100, bw=10):
        l=center
        dbw=bw/6
        self.set_wavelength([l-3*dbw,l-2*dbw,l-dbw,l, l+dbw, l+2*dbw, l+3*dbw,l])
        self.set_rf_amplitude([power,power,power,power,power,power,power,power])