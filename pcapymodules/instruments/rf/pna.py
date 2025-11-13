# Version 2: 202509013
# 
# 
import numpy as np
import pyvisa
import time
import os




class PNA:
    def __init__(self, address=None, port1=1, port2=2):
        self.rm = pyvisa.ResourceManager()
        self.pna = None
        self.port1 = port1
        self.port2 = port2
        self.n_trace = 4
        self._start_freq = 1e9
        self._stop_freq  = 40e9
        self._points     = 7801
        self._ifbw       = 1000
        self.cw_frequency = 1e9
        self.s_map = {}
        self.connect(address)
        self.wait_time = 0.5

       

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

    def reset(self):
        """Reset the PNA to a known state."""
        if self.pna is not None:
            self.pna.write("*RST")
            time.sleep(1)  # wait for reset to complete
            self.pna.write("*CLS")  # clear status

    def factory_reset(self):
        """Factory reset the PNA."""
        if self.pna is not None:
            self.pna.write("SYSTem:FPReset")
            time.sleep(2)  # wait for reset to complete
            self.pna.write("*CLS")  # clear status

    def get_s_map(self, n_trace = None, port1=None, port2=None):
        """Get S-parameters from the PNA."""
        if n_trace is not None: self.n_trace = n_trace
        if port1 is not None: self.port1 = port1
        if port2 is not None: self.port2 = port2
        if self.n_trace ==1: self.s_map = {"Meas1":'S%d%d'%(self.port1,self.port2)}
        elif self.n_trace ==2: self.s_map = {"Meas1":'S%d%d'%(self.port1,self.port1), "Meas2":'S%d%d'%(self.port1,self.port2)}
        else: self.s_map = {"Meas1":'S%d%d'%(self.port1,self.port1), "Meas2":'S%d%d'%(self.port1,self.port2), "Meas3":'S%d%d'%(self.port2,self.port1), "Meas4":'S%d%d'%(self.port2,self.port2)}
        return self.s_map

    
    def setup_measurements(self, n_trace = 4, channel = 1, win=1):    
        """
        Define N S-parameter measurements on PNA channel `ch` and
        route each measurement to a visible trace in Window 1.

        Assumes `self.get_s_parameters(trace)` returns an Ordered mapping:
        {"Meas1":"S11", "Meas2":"S21", ...}
        
        """

        self.pna.write("*CLS")
        self.s_map = self.get_s_map(n_trace=n_trace)
        chan = int(channel)
        self.channel = chan  # <-- persist for measure_once()

        self.pna.write(f'DISP:WIND{win}:STATE ON')
        self.pna.write(f'CALC{chan}:PAR:DEL:ALL')
        self.pna.write(f'INIT{chan}:CONT OFF')

        for i, (meas, sparam) in enumerate(self.s_map.items(), start=1):
            self.pna.write(f'CALC{chan}:PAR:DEF:EXT "{meas}","{sparam}"')
            self.pna.write(f'DISP:WIND{win}:TRAC{i}:FEED "{meas}"')
            self.pna.write(f'DISP:WIND{win}:TRAC{i}:STAT ON')
            self.pna.write(f'DISP:WIND{win}:TRAC{i}:Y:SCAL:AUTO')


    def set_sweep_parameters(self, start_freq=None, stop_freq=None, points=None, ifbw=None,
                         sweep_type="LIN", channel=1):
        ch = int(channel)
        self.channel = ch

        # Use local vars; validate
        f_start = self._start_freq if start_freq is None else float(start_freq)
        f_stop  = self._stop_freq  if stop_freq  is None else float(stop_freq)
        n_pts   = self._points     if points     is None else int(points)
        bw_hz   = self._ifbw       if ifbw       is None else float(ifbw)

        if f_start >= f_stop: raise ValueError("start_freq must be < stop_freq")
        if n_pts < 2:         raise ValueError("points must be >= 2")
        if bw_hz <= 0:        raise ValueError("ifbw must be > 0")

        self.pna.write(f"SENS{ch}:SWE:TYPE {sweep_type}")
        self.pna.write(f"SENS{ch}:FREQ:STAR {f_start}")
        self.pna.write(f"SENS{ch}:FREQ:STOP {f_stop}")
        self.pna.write(f"SENS{ch}:SWE:POIN {n_pts}")
        self.pna.write(f"SENS{ch}:BAND {bw_hz}")
        self.pna.write(f"INIT{ch}:CONT OFF")

        _ = self.pna.query("*OPC?")

        # Read back
        rb_start = float(self.pna.query(f"SENS{ch}:FREQ:STAR?"))
        rb_stop  = float(self.pna.query(f"SENS{ch}:FREQ:STOP?"))
        rb_pts   = int(float(self.pna.query(f"SENS{ch}:SWE:POIN?")))
        rb_bw    = float(self.pna.query(f"SENS{ch}:BAND?"))

        if abs(rb_start - f_start) > 0.1 or abs(rb_stop - f_stop) > 0.1:
            raise RuntimeError(f"PNA did not accept start/stop: got {rb_start}, {rb_stop}")
        if rb_pts != n_pts:
            raise RuntimeError(f"PNA points mismatch: set {n_pts}, got {rb_pts}")
        if abs(rb_bw - bw_hz) / bw_hz > 0.05:
            raise RuntimeError(f"PNA IFBW deviates >5%: set {bw_hz}, got {rb_bw}")

        # Cache intended values locally for file headers etc.
        self._start_freq, self._stop_freq, self._points, self._ifbw = f_start, f_stop, n_pts, bw_hz



    def get_spectrum(self):
        ch = getattr(self, "channel", 1)
        self.pna.write('FORM:DATA ASC')  # ensure ASCII for np.fromstring
        self.pna.write(f'INIT{ch}:IMM')
        self.pna.write('*WAI')
        time.sleep(self.wait_time)

        self.results = {}
        for meas, sparam in self.s_map.items():
            self.pna.write(f'CALC{ch}:PAR:SEL "{meas}"')
            data = self.pna.query(f'CALC{ch}:DATA? SDATA')
            arr = np.fromstring(data, sep=',', dtype=float)
            self.results[sparam] = (arr[0::2], arr[1::2])

        # Use cached intended values for the x-axis (matches what we set)
        self.frequencies = np.linspace(self._start_freq, self._stop_freq, self._points)
        return self.results, self.frequencies




    def save_spectrum(self, filename, folder=None):
        results, freqs = self.results, self.frequencies
        n = len(freqs); p1, p2 = self.port1, self.port2

        if folder is not None:
            os.makedirs(folder, exist_ok=True)
            # add .csv if missing
            if not filename.endswith('.csv'):
                filename = filename + '.csv'

            filename = os.path.join(folder, filename)

        with open(filename, 'w') as f:
            if self.n_trace == 1:
                s = f"S{p1}{p2}"
                f.write(f'Frequency(Hz),{s}(real),{s}(imag)\n')
                for i in range(n):
                    f.write(f"{freqs[i]},{results[s][0][i]},{results[s][1][i]}\n")
            elif self.n_trace == 2:
                s11 = f"S{p1}{p1}"; s12 = f"S{p1}{p2}"
                f.write('Frequency(Hz),S11(real),S11(imag),S12(real),S12(imag)\n')
                for i in range(n):
                    f.write(f"{freqs[i]},{results[s11][0][i]},{results[s11][1][i]},"
                            f"{results[s12][0][i]},{results[s12][1][i]}\n")
            else:
                s11 = f"S{p1}{p1}"; s12 = f"S{p1}{p2}"; s21 = f"S{p2}{p1}"; s22 = f"S{p2}{p2}"
                f.write('Frequency(Hz),S11(real),S11(imag),S12(real),S12(imag),S21(real),S21(imag),S22(real),S22(imag)\n')
                for i in range(n):
                    f.write(f"{freqs[i]},{results[s11][0][i]},{results[s11][1][i]},"
                            f"{results[s12][0][i]},{results[s12][1][i]},"
                            f"{results[s21][0][i]},{results[s21][1][i]},"
                            f"{results[s22][0][i]},{results[s22][1][i]}\n")
        print(f"S-parameters data saved to {filename}")
        return filename


    def measure_and_save_spectrum(self, filename, folder=None):
        """Measure S-parameters and save to a file."""
        results, frequencies = self.get_spectrum()
        new_file = self.save_spectrum(filename, folder)
        return results, frequencies, new_file
    def turn_output_on(self, on=True, channel=None):
        ch = self.channel if channel is None else int(channel)
        self.pna.write(f"OUTP{ch} {'ON' if on else 'OFF'}")

    def turn_output_off(self, channel=None):
        ch = self.channel if channel is None else int(channel)
        try:
            if self.pna is not None:
                self.pna.write(f"OUTP{ch} OFF")
        except Exception as e:
            print(f"Error while turning off output: {e}")


    def setup_s_measurement(self, start_freq=None, stop_freq=None, points=None, ifbw=None, channel=1, win=1, n_trace=4, sweep_type="LIN"):    
        """
        Define N S-parameter measurements on PNA channel `ch` and
        route each measurement to a visible trace in Window 1.

        Assumes `self.get_s_parameters(trace)` returns an Ordered mapping:
        {"Meas1":"S11", "Meas2":"S21", ...}
        
        """

        self.pna.write("*CLS")
        self.setup_measurements(n_trace = n_trace, channel = channel, win=win)
        self.set_sweep_parameters(start_freq=start_freq, stop_freq=stop_freq, points=points, ifbw=ifbw, sweep_type=sweep_type, channel = channel)  # Configure sweep settings

    def setup_cw_measurement(self, cw_freq=None, power=None, channel=1, win=1, n_trace=1):
        self.setup_measurements(n_trace=n_trace, channel=channel, win=win)
        ch = int(channel)
        self.channel = ch
        self.pna.write(f"SENS{ch}:SWE:TYPE CW")
        if cw_freq is not None:
            self.pna.write(f"SENS{ch}:FREQ:CW {float(cw_freq)}")
            self.cw_frequency = float(cw_freq)
        if power is not None:
            self.pna.write(f"SOUR{ch}:POW {float(power)}")
        self.pna.write(f"INIT{ch}:CONT OFF")
        self.pna.write("*CLS")
        time.sleep(0.1)


    def clear_errors(self):
        """Clear the PNA error queue."""
        if self.pna is not None:
            self.pna.write("*CLS")
            while True:
                err = self.pna.query("SYST:ERR?")
                if err.startswith("+0"):
                    break
                print(f"PNA Error: {err.strip()}")



    @property
    def sweep_type(self):
        ch = self.channel
        return self.pna.query(f"SENS{ch}:SWE:TYPE?").strip()

    @sweep_type.setter
    def sweep_type(self, mode):
        ch = self.channel
        mode = mode.upper()
        if mode not in ("LIN", "LOG", "CW", "LIST"):
            raise ValueError("sweep_type must be LIN, LOG, CW, or LIST")
        self.pna.write(f"SENS{ch}:SWE:TYPE {mode}")

    # ---------------------------
    # Sweep start / stop
    # ---------------------------
    @property
    def start_freq(self):
        ch = self.channel
        return float(self.pna.query(f"SENS{ch}:FREQ:STAR?"))

    @start_freq.setter
    def start_freq(self, value_hz):
        ch = self.channel
        self.pna.write(f"SENS{ch}:SWE:TYPE LIN")  # ensure linear sweep
        self.pna.write(f"SENS{ch}:FREQ:STAR {float(value_hz)}")

    @property
    def stop_freq(self):
        ch = self.channel
        return float(self.pna.query(f"SENS{ch}:FREQ:STOP?"))

    @stop_freq.setter
    def stop_freq(self, value_hz):
        ch = self.channel
        self.pna.write(f"SENS{ch}:SWE:TYPE LIN")
        self.pna.write(f"SENS{ch}:FREQ:STOP {float(value_hz)}")

    # ---------------------------
    # Sweep points
    # ---------------------------
    @property
    def points(self):
        ch = self.channel
        return int(float(self.pna.query(f"SENS{ch}:SWE:POIN?")))

    @points.setter
    def points(self, n):
        ch = self.channel
        n = int(n)
        if n < 2:
            raise ValueError("points must be >= 2")
        self.pna.write(f"SENS{ch}:SWE:POIN {n}")

    # ---------------------------
    # IF bandwidth
    # ---------------------------
    @property
    def ifbw(self):
        ch = self.channel
        return float(self.pna.query(f"SENS{ch}:BAND?"))

    @ifbw.setter
    def ifbw(self, bw_hz):
        ch = self.channel
        self.pna.write(f"SENS{ch}:BAND {float(bw_hz)}")

    # ---------------------------
    # CW frequency
    # ---------------------------
    @property
    def cw_freq(self):
        ch = self.channel
        return float(self.pna.query(f"SENS{ch}:FREQ:CW?"))

    @cw_freq.setter
    def cw_freq(self, value_hz):
        ch = self.channel
        self.pna.write(f"SENS{ch}:SWE:TYPE CW")
        self.pna.write(f"SENS{ch}:FREQ:CW {float(value_hz)}")

    # ---------------------------
    # Source power
    # ---------------------------
    @property
    def power(self):
        ch = self.channel
        return float(self.pna.query(f"SOUR{ch}:POW?"))

    @power.setter
    def power(self, dbm):
        ch = self.channel
        self.pna.write(f"SOUR{ch}:POW {float(dbm)}")

    # ---------------------------
    # Output state (RF ON/OFF)
    # ---------------------------
    @property
    def output(self):
        ch = self.channel
        return self.pna.query(f"OUTP{ch}?").strip() in ("1", "ON")

    @output.setter
    def output(self, on):
        ch = self.channel
        self.pna.write(f"OUTP{ch} {'ON' if on else 'OFF'}")

    # ---------------------------
    # Continuous sweep
    # ---------------------------
    @property
    def continuous(self):
        ch = self.channel
        return self.pna.query(f"INIT{ch}:CONT?").strip() in ("1", "ON")

    @continuous.setter
    def continuous(self, on):
        ch = self.channel
        self.pna.write(f"INIT{ch}:CONT {'ON' if on else 'OFF'}")


    

    def measure_cw_S(self):
        ch = self.channel
        meas = 'Meas1'

        self.pna.write(f'CALC{ch}:PAR:SEL "{meas}"')
        data = self.pna.query(f"CALC{ch}:DATA? SDATA")
        # For CW there is exactly 1 point → "Re,Im"
        vals = data.split(",")
        re = float(vals[0]); im = float(vals[1])
        return 10*np.log10(re*re + im*im)  # return dB magnitude