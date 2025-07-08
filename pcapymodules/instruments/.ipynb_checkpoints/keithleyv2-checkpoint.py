import pyvisa
from pymeasure.instruments.keithley import Keithley2400
from ctypes import util
print(util.find_library("visa"))
from time import sleep
import numpy as np
from ..measurement import measurementv2 as mm


class MySourcemeter(Keithley2400):
    def __init__(self):
        #rm = pyvisa.ResourceManager()
        # ports = rm.list_resources()
        print("Connecting to Keithley Sourcemeter")
        self.keithley = Keithley2400('GPIB::21')
        #self.reset_and_enable_source()
        self.my_source_voltage = mm.WritePort('Voltage', 'V' , self.measure_voltage, self.set_voltage)
        self.my_measure_current = mm.ReadPort('Current', 'A',  self.measure_current)
        self.port_list = {'write':['my_source_voltage'], 'read':['my_measure_current']}
        
        print("Connection to Keithley Sourcemeter established.")
        
    def reset_and_enable_source(self):
        self.keithley.reset()
        self.keithley.use_front_terminals()
        self.keithley.measure_current()
        sleep(0.1)
        self.keithley.enable_source()

    def measure_current(self):
        return self.keithley.current

    def measure_voltage(self):
        return self.keithley.source_voltage

    def set_voltage(self, val): 
        self.keithley.source_voltage = val
        return self.keithley.source_voltage

    def IV_Curve(self,min_voltage, max_voltage, n_steps, wait=1):
        voltages = np.linspace(min_voltage,max_voltage,num=n_steps)
        currents = np.zeros_like(voltages)
        for i in range(n_steps):
            self.keithley.source_voltage = voltages[i]
            sleep(float(wait))
            currents[i] = self.keithley.current
        
        self.keithley.source_voltage = 0
        return currents.tolist()
    
        
    

def main():
    print("Connecting to Keithley Sourcemeter")
    rm = pyvisa.ResourceManager()
    ports = rm.list_resources()
    print(ports)
    a = MySourcemeter()
    dilly = a.IV_Curve(0,10,9)
    print(dilly)


if __name__=="__main__":
    main()

# Oct 19,2021
# Updated February 23, 2022
