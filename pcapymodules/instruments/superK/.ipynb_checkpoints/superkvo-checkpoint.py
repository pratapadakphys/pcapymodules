from NKTP_DLL import *


class SuperK:

    def __init__(self, port = 'COM5', rf_module = 18):
        '''
        To switch from Visible to NIR range switch rf_nodule no from 18 to 22 or vice versa
        For Montana PC port is 'COM5', for Olympus pc it is 'COM17'
        '''
        self.port = port
        self.rf_module = rf_module
        
    def turn_emission_on(self, silent=False):
        result = registerWriteU8(self.port, 15, 0x30, 0x03, -1)
        r=RegisterResultTypes(result)
        if not silent: print('Setting emission ON - Extreme:', r)
        return r
        
    def turn_emission_off(self, silent=False):
        result = registerWriteU8(self.port, 15, 0x30, 0x0, -1)
        r=RegisterResultTypes(result)
        if not silent: print('Setting emission OFF - Extreme:', r)
        return r
        
    def set_operation_mode(self, mode=1, silent=False):
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
        if not silent: print('Setting operation mode - Extreme:', r)
        return r
        
        

    #turn_emission_on()
    #reg=registerReadU8('COM17', 22, 0x65, -1)
    #r=RegisterResultTypes(reg)
    #print(reg)


    def set_power_level(self, value=0, silent=False):
        p=(int(value*10))
        result = registerWriteU16(self.port, 15, 0x37, p, -1)
        r=RegisterResultTypes(result)
        if not silent: print('Setting power level - Extreme:', r)
        return r

    def set_rf_on(self, silent=False):
        result = registerWriteU8(self.port, self.rf_module, 0x30, 0x01, -1)
        r=RegisterResultTypes(result)
        if not silent: print('Setting RF power ON - SuperK SELECT:', result, r)
        return r
        
    def set_rf_off(self, silent=False):
        result = registerWriteU8(self.port, self.rf_module, 0x30, 0, -1)
        r=RegisterResultTypes(result)
        if not silent: print('Setting RF power OFF - SuperK SELECT:', result, r)
        return r
        
    def set_rf_amplitude(self, value=0, silent=False):
        p=(int(value*10))
        result = registerWriteU16(self.port, self.rf_module, 0xB0, p, -1)
        r=RegisterResultTypes(result)
        if not silent: print('Setting amplitude level - SuperK SELECT:', result, r)
        return r
        
    def set_wavelength(self, value=0, silent=False):
        p=(int(value*1000))
        result = registerWriteU32(self.port, self.rf_module, 0x90, p, -1)
        r=RegisterResultTypes(result)
        if not silent: print('Setting amplitude level - SuperK SELECT:', result, r)
        return r


#addResult = pointToPointPortAdd('SuperKPort1', pointToPointPortData(myIp, 'COM17' , myIp,1, 1, 100))
#print('Creating ethernet port', P2PPortResultTypes(addResult))


#set_rf_on()
#turn_emission_on()
#set_rf_on()
#set_rf_amplitude(10)
#set_rf_wavelength(550)
#set_power_level(11)
#reg=registerReadU8('COM17', 18, 0x75, -1)
#print(reg)
