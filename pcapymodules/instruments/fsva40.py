# FSVA40 helper – robust SCPI for Rohde & Schwarz FSVA series
# v1.1 (2025-09-13)

import pyvisa
import numpy as np

class FSVA40:
    def __init__(self, visa_address='GPIB0::20::INSTR', timeout_ms=100000):
        self.rm = pyvisa.ResourceManager()
        self.inst = self.rm.open_resource(visa_address)
        self.inst.timeout = timeout_ms  # milliseconds
        # Stable, explicit front-end & data format
        self.write('INIT:CONT OFF')          # single-sweep mode
        self.write('DET RMS')                # detector
        self.write('UNIT:POW DBM')           # y-units
        self.write('FORM REAL,32')           # binary float32 for speed/precision
        self.write('FORM:BORD SWAP')         # little-endian to match most hosts

    # --- housekeeping ---
    def close(self):
        try:
            self.inst.close()
        finally:
            try:
                self.rm.close()
            except Exception:
                pass

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        self.close()

    # --- low-level I/O ---
    def query(self, cmd):
        return self.inst.query(cmd).strip()

    def write(self, cmd):
        self.inst.write(cmd)

    # --- id / basic properties ---
    @property
    def idn(self):
        return self.query('*IDN?')

    # Frequency control
    @property
    def center_frequency(self):
        return float(self.query('FREQ:CENT?'))
    @center_frequency.setter
    def center_frequency(self, value_hz):
        self.write(f'FREQ:CENT {value_hz}')

    @property
    def span(self):
        return float(self.query('FREQ:SPAN?'))
    @span.setter
    def span(self, value_hz):
        self.write(f'FREQ:SPAN {value_hz}')

    @property
    def start_freq(self):
        return float(self.query('FREQ:STAR?'))

    @property
    def stop_freq(self):
        return float(self.query('FREQ:STOP?'))

    # Bandwidths
    @property
    def rbw(self):
        return float(self.query('BAND:RES?'))
    @rbw.setter
    def rbw(self, value_hz):
        self.write(f'BAND:RES {value_hz}')

    @property
    def vbw(self):
        return float(self.query('BAND:VID?'))
    @vbw.setter
    def vbw(self, value_hz):
        self.write(f'BAND:VID {value_hz}')

    # Sweep points / time
    @property
    def sweep_points(self):
        return int(float(self.query('SWE:POIN?')))
    @sweep_points.setter
    def sweep_points(self, n):
        self.write(f'SWE:POIN {int(n)}')

    @property
    def sweep_time(self):
        return float(self.query('SWE:TIME?'))
    @sweep_time.setter
    def sweep_time(self, sec):
        self.write(f'SWE:TIME {sec}')

    # Averages (optional)
    def set_averaging(self, enabled=True, count=10):
        self.write(f'AVER:STAT {"ON" if enabled else "OFF"}')
        if enabled:
            self.write(f'AVER:COUN {int(count)}')
            self.write('AVER:CLE')

    # --- acquisition helpers ---
    def acquire_once_and_wait(self):
        # Blocks until sweep (and averaging, if enabled) completes
        return self.query('INIT; *OPC?')  # returns "1" when done

    def fetch_trace(self, trace='TRACE1'):
        """
        Returns numpy array of float32 in dBm (assuming UNIT:POW DBM).
        Uses binary transfer for speed. Assumes FORM REAL,32 and BORD SWAP set.
        """
        # Ask for data; the current FORM governs the transfer format.
        self.write(f'TRAC:DATA? {trace}')
        data = self.inst.read_binary_values(datatype='f', is_big_endian=False, container=np.array)
        return data

    def measure_spectrum(self, trace='TRACE1'):
        """
        Triggers a sweep, waits for completion, returns (freq_Hz, power_dBm).
        X built from current start/stop and ACTUAL returned length.
        """
        self.acquire_once_and_wait()
        y = self.fetch_trace(trace=trace)
        n = len(y)
        start = self.start_freq
        stop  = self.stop_freq
        # Inclusive linspace: n points from start..stop
        x = np.linspace(start, stop, n, dtype=np.float64)
        return x, y

    # --- utilities ---
    def autoscale_ref_level(self):
        self.write('DISP:WIND:TRAC:Y:SCAL:AUTO ONCE')

    def set_ref_level(self, dBm):
        self.write(f'DISP:WIND:TRAC:Y:RLEV {dBm}')

    def get_error(self):
        """Pop one entry from the instrument error queue."""
        return self.query('SYST:ERR?')
