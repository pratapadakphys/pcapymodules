from datetime import datetime
from ctypes import cdll,c_long, c_ulong, c_uint32,byref,create_string_buffer,c_bool,c_char_p,c_int,c_int16,c_double, sizeof, c_voidp
import time
from ..measurement import measurement as mm
from .TLPMmontana import TLPM

class MyTLPM(TLPM):
    def __init__(self):
        super().__init__()
        deviceCount = c_uint32()
        self.findRsrc(byref(deviceCount))

        print("devices found: " + str(deviceCount.value))

        resourceName = create_string_buffer(1024)
        for i in range(0, deviceCount.value):
            self.getRsrcName(c_int(i), resourceName)
            print(c_char_p(resourceName.raw).value)
            break

        #self.close()

        self.open(resourceName, c_bool(True), c_bool(True))
        message = create_string_buffer(1024)
        self.getCalibrationMsg(message)
        print(c_char_p(message.raw).value)

        time.sleep(5)
        
        self.my_measure_power = mm.ReadPort('Power', 'W',  self._my_measure)
        
    def _my_measure(self):
        power =  c_double()
        self.measPower(byref(power))
        return power.value


