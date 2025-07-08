import pyvisa
from pymeasure.instruments.keithley import Keithley2400
#from ctypes import util
#print(util.find_library("visa"))
from time import sleep
from pcapymodules import mymeasurementv2 as mm


class MyKeithley2400(Keithley2400):
    
    def __init__(self, adapter, **kwargs):
        super().__init__(adapter, **kwargs)
        self._open_my_ports()
    
    
    def _open_my_ports(self):
        self.my_source_voltage = mm.WritePort('Voltage', 'V' , self._measure_my_voltage, self._set_my_voltage)
        self.my_measure_current = mm.ReadPort('Current', 'A',  self._measure_my_current)
        self.port_list = {'write':['my_source_voltage'], 'read':['my_measure_current']}
        
        
    def reset_and_enable_source(self):
        self.reset()
        self.use_front_terminals()
        self.measure_current()
        sleep(0.1)
        self.enable_source()

    def _measure_my_current(self):
        return self.current

    def _measure_my_voltage(self):
        return self.source_voltage

    def _set_my_voltage(self, val): 
        self.source_voltage = val
        return self.source_voltage

    
        
    

def main():
    print("Connecting to Keithley Sourcemeter")
    rm = pyvisa.ResourceManager()
    ports = rm.list_resources()
    print(ports)
    a = MySourcemeter('GPIB::21')
    dilly = a.IV_Curve(0,10,9)
    print(dilly)


if __name__=="__main__":
    main()


