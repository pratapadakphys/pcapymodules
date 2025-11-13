import numpy as np
import pyvisa
import time

class PNA:
    def __init__(self, port1=1, port2 = 2, address=None):
        self.rm = pyvisa.ResourceManager()
        self.pna = None
        self.port1 = port1
        self.port2 = port2
        self.channel = 4  # Default channel, can be changed later
        self.start_freq = 1e9  # Default start frequency in Hz
        self.stop_freq = 40e9  # Default stop frequency in Hz
        self.points = 7801  # Default number of points
        self.ifbw = 1000  # Default IF bandwidth in Hz
        self.get_s_parameters()  # Initialize S-parameters
        self.connect(address)  # Attempt to connect to the PNA
        self.wait_time = 0.5  # Default wait time after measurement
       

    def get_resource_list(self):
        """Get the address of the PNA."""
        return self.rm.list_resources()

    def connect(self, address = None):
        """Automatically connect to the PNA."""
        if address==None: address = 0
        if isinstance(address, int):
            resources = self.get_resource_list()
            if len(resources) == 0:
                raise ValueError("No PNA found. Please check the connection.")
            if address >= len(resources):
                raise ValueError(f"Address {address} is out of range. Available addresses: {resources}")
            address = resources[address]

        try:
            self.pna = self.rm.open_resource(address)
            # Optional: set timeout or termination characters if needed
            self.pna.timeout = 5000  # ms
            idn = self.pna.query("*IDN?")
            print(f"Connected successfully. Device ID: {idn.strip()}")
            return True
        except Exception as e:
            print(f"Failed to connect to PNA: {e}")
            self.pna = None
            return False

    def disconnect(self):
        """Disconnect from the PNA."""
        if self.pna is not None:
            try:  self.pna.close()
            except Exception as e:
                print(f"Error while disconnecting: {e}")

    def get_s_parameters(self, channel = None, port1=None, port2=None):
        """Get S-parameters from the PNA."""
        if channel is not None: self.channel = channel
        if port1 is not None: self.port1 = port1
        if port2 is not None: self.port2 = port2
        if self.channel ==1: self.s_parameters = {"Meas1":'S%d%d'%(self.port1,self.port2)}
        if self.channel ==2: self.s_parameters = {"Meas1":'S%d%d'%(self.port1,self.port1), "Meas2":'S%d%d'%(self.port1,self.port2)}
        else: self.s_parameters = {"Meas1":'S%d%d'%(self.port1,self.port1), "Meas2":'S%d%d'%(self.port1,self.port2), "Meas3":'S%d%d'%(self.port2,self.port1), "Meas4":'S%d%d'%(self.port2,self.port2)}
        return self.s_parameters

    def configure_sweep_settings(self, start_freq=None, stop_freq=None, points=None, ifbw=None):
        # Configure sweep settings
        if start_freq is not None: self.start_freq = start_freq
        if stop_freq is not None: self.stop_freq = stop_freq
        if points is not None: self.points = points
        if ifbw is not None: self.ifbw = ifbw
        self.pna.write(f'SENSe1:FREQuency:STARt {self.start_freq}')  # Set start frequency
        self.pna.write(f'SENSe1:FREQuency:STOP {self.stop_freq}')  # Set stop frequency
        self.pna.write(f'SENS1:SWE:POIN {self.points_num}')  # Set number of sweep points
        self.pna.write('SENSe1:BANDwidth %d'%self.ifbw)  # Set IF bandwidth

    def set_multichannel(self, channel = 4):    
        """Set the PNA to multichannel mode."""
        self.s_parameters = self.get_s_parameters(channel = channel)
        # Reset and configure the PNA
        self.pna.write('SYSTem:FPReset')  # Factory preset
        #pna.write('CALCulate1:PARameter:DEFine:EXT "Meas1","S13"')  # Define S11 measurement
        self.pna.write('DISPlay:WINDow1:STATE ON')  # Ensure display window is on
        #pna.write('DISPlay:WINDow1:TRACe1:FEED "Meas1"')  # Assign Meas1 to Trace 1 in Window 1
        self.pna.write('INITiate:CONTinuous OFF')  # Disable continuous sweep

        for meas, param in s_parameters.items():
            self.pna.write('CALCulate1:PARameter:DEFine:EXT "%s","%s"'%(meas, param))  # Define S11 measurement
            self.pna.write('DISPlay:WINDow1:TRACe%d:FEED "%s"'%(list(s_parameters.keys()).index(meas)+1,meas))  # Assign Meas1 to Trace 1 in Window 1

        conigure_sweep_settings()  # Configure sweep settings

    def measure_once(self):
        # Trigger the sweep and wait for completion
        self.pna.write('INITiate1:IMMediate')  # Start sweep
        self.pna.write('*WAI')  # Wait for the operation to complete

        time.sleep(self.wait_time)
        
        # Retrieve measurement data
        self.pna.write('FORM:DATA ASC')  # Set data format to ASCII

        self.results ={}
        
        for meas, param in s_parameters.items():
            self.pna.write(f'CALCulate1:PARameter:SELect "{meas}"')  # Select the correct S-parameter before querying
            data = self.pna.query(f'CALCulate1:DATA? SDATA')  # Query S-parameter data
            data_points = np.array([float(x) for x in data.split(',')])
            real_part = data_points[0::2]  # Extract real part
            imag_part = data_points[1::2]  # Extract imaginary part
            
            self.results[param] = (real_part, imag_part)  # Store magnitude and phase
        
        # Generate frequency array
        self.frequencies = np.linspace(start_freq, stop_freq, points_num)

        return self.results, self.frequencies

    def save_results(self, filename, folder=None ):
        results, frequencies = self.results, self.frequencies
        points_num = len(frequencies)
        port1, port2 = self.port1, self.port2
        if folder is not None: filename =folder+'%s.csv'%filename
        # Save data to a CSV file
        
        with open(filename, 'w') as file:
            if self.channel ==1:
                file.write('Frequency(Hz),S12(real),S12(imag)\n')
                for i in range(points_num):
                    file.write(f"{frequencies[i]},{results['S%d%d'%(port1,port2)][0][i]},{results['S%d%d'%(port1,port2)][1][i]}\n")
            if self.channel ==2:
                file.write('Frequency(Hz),S11(real),S11(imag),S12(real),S12(imag)\n')
                for i in range(points_num):
                    file.write(f"{frequencies[i]},{results['S%d%d'%(port1,port1)][0][i]},{results['S%d%d'%(port1,port1)][1][i]},"
                            f"{results['S%d%d'%(port1,port2)][0][i]},{results['S%d%d'%(port1,port2)][1][i]}\n")
            else:     
                file.write('Frequency(Hz),S11(real),S11(imag),S12(real),S12(imag),S21(real),S21(imag),S22(real),S22(imag)\n')
                for i in range(points_num):
                    file.write(f"{frequencies[i]},{results['S%d%d'%(port1,port1)][0][i]},{results['S%d%d'%(port1,port1)][1][i]},"
                            f"{results['S%d%d'%(port1,port2)][0][i]},{results['S%d%d'%(port1,port2)][1][i]},"
                            f"{results['S%d%d'%(port2,port1)][0][i]},{results['S%d%d'%(port2,port1)][1][i]},"
                            f"{results['S%d%d'%(port2,port2)][0][i]},{results['S%d%d'%(port2,port2)][1][i]}\n")
        
            print(f"S-parameters data saved to {filename}")
            return filename

    def measure_and_save(self, filename, folder=None):
        """Measure S-parameters and save to a file."""
        results, frequencies = self.measure_once()
        self.save_results(filename, folder)
        return results, frequencies




