# rfs1000.py
import serial
import time

class RFS1000:
    """
    Serial interface to Berkeley Nucleonics RFS-1000 series signal generator.
    Validated for firmware v8.03 (e.g., RFS-1420, serial 3706).
    """

    def __init__(self, port='COM6', baudrate=115200, timeout=1, verbose=True):
        self.port = port
        self.baudrate = baudrate
        self.timeout = timeout
        self.verbose = verbose
        self.ser = None
        self.connect()

    def open(self):
        self.connect()

    def connect(self):
        self.ser = serial.Serial(self.port, baudrate=self.baudrate, timeout=self.timeout)
        time.sleep(2)  # allow device to stabilize
        if self.verbose:
            print(f"[RFS1000] Connected to {self.port} at {self.baudrate} baud.")

    def disconnect(self):
        self.close()


    def close(self):
        if self.ser and self.ser.is_open:
            self.ser.close()
            if self.verbose:
                print("[RFS1000] Serial port closed.")

    def _send(self, cmd, expect_response=True, delay=0.1):
        """Send a command and return response if expected."""
        full_cmd = cmd.strip() + '\n'
        self.ser.write(full_cmd.encode())
        time.sleep(delay)
        response = self.ser.readline().decode(errors='ignore').strip()
        if self.verbose:
            print(f"> {cmd}")
            if expect_response and response:
                print(f"< {response}")
        return response if expect_response else None

    # Core commands
    def identify(self):
        return self._send('*IDN?')

    def reset(self):
        return self._send('*RST', expect_response=False)

    def save_state(self):
        return self._send('*SAVESTATE', expect_response=False)

    def set_frequency(self, freq_hz):
        """Set CW frequency in Hz."""
        return self._send(f'FREQ:CW {int(freq_hz)}', expect_response=False)

    def set_power(self, power_dbm):
        """Set output power in dBm."""
        return self._send(f'POWER {power_dbm:.1f}', expect_response=False)

    def rf_on(self):
        return self._send('OUTP:STAT ON', expect_response=False)

    def rf_off(self):
        return self._send('OUTP:STAT OFF', expect_response=False)


    # Context manager support
    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()


    # ---------------------------
    # CW frequency
    # ---------------------------
    @property
    def cw_freq(self):
        """Get CW frequency in Hz."""
        resp = self._send("FREQ:CW?", expect_response=True)
        clean = resp.strip().replace("HZ", "").replace("GHZ", "e9").replace("<", "").replace(">", "")
        try:
            return float(clean)
        except ValueError:
            return resp.strip()  # fallback if parsing fails


    @cw_freq.setter
    def cw_freq(self, freq_hz):
        """Set CW frequency in Hz."""
        self._send(f"FREQ:CW {float(freq_hz)}", expect_response=False)

    # ---------------------------
    # Source power
    # ---------------------------
    @property
    def power(self):
        """Get RF output power in dBm."""
        resp = self._send("POWER?", expect_response=True)
        if resp is None:
            return None
        # Clean up: remove units like "dBm" and leading "<"
        clean = resp.strip().replace("dBm", "").replace("<", "").replace(">", "")
        try:
            return float(clean)
        except ValueError:
            return resp.strip()  # fallback: return raw string

    @power.setter
    def power(self, power_dbm):
        return self._send(f'POWER {power_dbm:.1f}', expect_response=False)
    

    def set_cw_frequency(self,f,RF_power):
        self.cw_freq = f
        self.power = RF_power
        time.sleep(0.1)
        return self.cw_freq, self.power


    # ---------------------------
    # Output state (RF ON/OFF)
    # ---------------------------
    

