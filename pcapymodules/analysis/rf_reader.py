
import os, re
import numpy as np
import pandas as pd
from dataclasses import dataclass
from typing import List, Tuple, Optional
import matplotlib.pyplot as plt

from .loadfile import FileSet



FILENAME_RE = re.compile(r"f\s*=\s*(?P<f>[-+]?\d+(?:\.\d+)?)\s*Hz.*?B\s*=\s*(?P<B>[-+]?\d+(?:\.\d+)?)\s*T", re.IGNORECASE)

@dataclass
class Trace:
    f_GHz: float
    B_T: float
    offset_Hz: np.ndarray
    power_dBm: np.ndarray
    fname: str
class RFSA_file:
    def __init__(self, filepath):
        if filepath is None:
            print("Deprecation Warning: construct via gui has been deprecated in this module. "
                  "Use load() in spe2py instead.")
            return
        assert isinstance(filepath, str), 'Filepath must be a single string'
        self.filepath = filepath

        self.x,self.y = read_csv_flexible(filepath)

    def get_spectrum(self):
        return self.x, self.y
    
    def plot_spectrum (self, save = True, **kwargs):
        '''
        This plots the single spectrum from a SpeFile

        Parameters
        ----------
        **kwargs : TYPE
            DESCRIPTION. keywords used for plt.plot

        Returns
        -------
        Plot

        '''
        x,y = self.get_spectrum()
        p = plt.plot(x,y,**kwargs)
        plt.xlabel('Frequency (Hz)')
        plt.ylabel('Power (dBm)')
        if save:
            self.save_plot()
        return p
        
    def save_plot(self, extension = '.png'):
        _pathname, _extension = os.path.splitext(os.path.basename(self.filepath))
        _directory = os.path.dirname(self.filepath)
        
        self.customize()
               
        _directory += r'/Plot/'
        isExist = os.path.exists(_directory)
        if not isExist:
            # Create a new directory because it does not exist
            os.makedirs(_directory)
            print("The new directory is created!")
        
        image_filename = _directory+_pathname+extension
        plt.savefig(image_filename, transparent = True, dpi = 300)
        return image_filename
    
    def customize (self):
        pass
    
   

def read_csv_flexible( path: str) -> Tuple[np.ndarray, np.ndarray]:
    """
    Reads a CSV and returns (freq_Hz, power_dBm).
    Accepts column names with minor variations.
    """
    df = pd.read_csv(path)
    cols = {c.lower().strip(): c for c in df.columns}
    # Try common variants
    freq_col = None
    for k in ["freq(hz)", "frequency(hz)", "freq", "frequency"]:
        if k in cols:
            freq_col = cols[k]
            break
    if freq_col is None:
        # Try to find a column that has 'hz' in name
        for k,v in cols.items():
            if "hz" in k:
                freq_col = v
                break
    if freq_col is None:
        raise ValueError(f"Could not find frequency column in {path}. Columns: {list(df.columns)}")

    power_col = None
    for k in ["p(dbm)", "power(dbm)", "p", "power"]:
        if k in cols:
            power_col = cols[k]
            break
    if power_col is None:
        # Fallback to any column with 'dbm'
        for k,v in cols.items():
            if "dbm" in k:
                power_col = v
                break
    if power_col is None:
        # Last resort: take the second column
        if len(df.columns) >= 2:
            power_col = df.columns[1]
        else:
            raise ValueError(f"Could not find power column in {path}. Columns: {list(df.columns)}")

    freq = pd.to_numeric(df[freq_col], errors="coerce").to_numpy()
    pow_dbm = pd.to_numeric(df[power_col], errors="coerce").to_numpy()

    mask = np.isfinite(freq) & np.isfinite(pow_dbm)
    freq, pow_dbm = freq[mask], pow_dbm[mask]

    # Ensure sorted by frequency
    order = np.argsort(freq)
    return freq[order], pow_dbm[order]

def _parse_fb_from_name(fname: str) -> Tuple[Optional[float], Optional[float]]:
    m = FILENAME_RE.search(fname)
    if not m:
        return None, None
    f = float(m.group("f"))
    B = float(m.group("B"))
    return f, B

def load_traces(folder: str) -> List[Trace]:
    traces: List[Trace] = []
    for root, _, files in os.walk(folder):
        for fn in files:
            if fn.lower().endswith(".csv"):
                path = os.path.join(root, fn)
                f_GHz, B_T = _parse_fb_from_name(fn)
                # If parsing fails, allow but set None; we will skip those without f
                freq_Hz, pow_dbm = read_csv_flexible(path)
                center = 0.5*(freq_Hz.min() + freq_Hz.max())
                offset = freq_Hz - center
                traces.append(Trace(
                    f_GHz=f_GHz if f_GHz is not None else float("nan"),
                    B_T=B_T if B_T is not None else float("nan"),
                    offset_Hz=offset.astype(float),
                    power_dBm=pow_dbm.astype(float),
                    fname=path
                ))
    if not traces:
        raise FileNotFoundError(f"No CSV files found under {folder}")
    # Filter out traces without a valid f_GHz (since Y axis is magnon frequency)
    valid = [t for t in traces if np.isfinite(t.f_GHz)]
    if not valid:
        raise ValueError("No files with parseable magnon frequency 'f=... Hz' in filename.")
    # Sort by f_GHz
    valid.sort(key=lambda t: t.f_GHz)
    return valid

def build_common_grid(traces: List[Trace]) -> np.ndarray:
    # Determine overlap region across all offsets
    mins = [t.offset_Hz.min() for t in traces]
    maxs = [t.offset_Hz.max() for t in traces]
    grid_min = max(mins)
    grid_max = min(maxs)
    if not np.isfinite(grid_min) or not np.isfinite(grid_max) or grid_max <= grid_min:
        # Fallback to use the first trace grid
        base = traces[0].offset_Hz
        return np.copy(base)
    # Determine a sensible step: median of median step sizes
    steps = []
    for t in traces:
        diffs = np.diff(t.offset_Hz)
        diffs = diffs[np.isfinite(diffs) & (diffs > 0)]
        if len(diffs):
            steps.append(np.median(diffs))
    step = np.median(steps) if steps else (grid_max - grid_min)/max(512, len(traces[0].offset_Hz))
    # Build grid (inclusive of grid_max within one step)
    npts = int(np.floor((grid_max - grid_min)/step)) + 1
    X = grid_min + np.arange(npts)*step
    return X

def interpolate_to_grid(traces: List[Trace], X: np.ndarray) -> Tuple[np.ndarray, np.ndarray, np.ndarray, pd.DataFrame]:
    Y = np.array([t.f_GHz for t in traces], dtype=float)
    Z = np.empty((len(traces), len(X)), dtype=float)
    meta_rows = []
    for i, t in enumerate(traces):
        # Interpolate power to X
        Z[i, :] = np.interp(X, t.offset_Hz, t.power_dBm, left=np.nan, right=np.nan)
        meta_rows.append({
            "index": i,
            "f_GHz": t.f_GHz,
            "B_T": t.B_T,
            "fname": t.fname,
            "offset_min_Hz": float(np.nanmin(t.offset_Hz)),
            "offset_max_Hz": float(np.nanmax(t.offset_Hz)),
        })
    meta = pd.DataFrame(meta_rows).sort_values("f_GHz").reset_index(drop=True)
    return X, Y, Z, meta

def build_2d_map(folder: str, save_prefix: Optional[str] = None):
    traces = load_traces(folder)
    X = build_common_grid(traces)
    X, Y, Z, meta = interpolate_to_grid(traces, X)
    if save_prefix is None:
        save_prefix = os.path.join(folder, "spectra_map")
    np.savez_compressed(f"{save_prefix}.npz", X_offset_Hz=X, Y_magnon_freq_GHz=Y, Z_power_dBm=Z)
    meta.to_csv(f"{save_prefix}_meta.csv", index=False)
    return X, Y, Z, meta




def my_rf_loader(filepath):
    return RFSA_file(filepath)


class RFFileSet(FileSet):
    def __init__(self, files, pattern = None, find_text = '', filename = None):
        super().__init__(files, pattern, find_text, filename, file_type = '.csv', loader= my_rf_loader)
        self._load_data()

    def _load_data(self, col=0, keys = ['x','y']):
        if col in self.df.columns:
            xlist = []; ylist = []
            for file in self.df.iloc[:,col]:
                (x,y) = file.get_spectrum()
                xlist.append(np.array(x)); ylist.append(np.array(y))
            self.df[keys[0]] = xlist; self.df[keys[1]] = ylist 

    def data(self, variable = None, transposed = False, round_lambda = 2):
        if variable is None: variable = self.variable
        l = self.df['x'][0]
        if round_lambda is not None: l = l.round(round_lambda)
            
        if transposed:
            dt = pd.DataFrame(np.stack(self.df['y']).transpose(), columns=self.df[variable], index = l)
        else: 
            dt = pd.DataFrame(np.stack(self.df['y']), index=self.df[variable], columns = l)
        return dt
def ensure_csv_extension(filename):
    # Get the file extension (if any)
    root, ext = os.path.splitext(filename)
    
    # Append '.csv' only if no extension is present
    if not ext:
        return filename + '.csv'
    return filename

def read_s_from_file (filename, S=['S12'], separation =''):
    # Read CSV file into a pandas DataFrame
    filename = ensure_csv_extension(filename)
    df = pd.read_csv(filename)
    S_mag = []
    S_phase = []
    # Extract frequency and S12 magnitude
    frequency = df['Frequency%s(Hz)'%separation].values  # Read frequency only once
    for s in S:
        s_r = df['%s%s(real)'%(s,separation)].values  # Extract S12 magnitude
        s_i = df['%s%s(imag)'%(s,separation)].values  # Extract S12 magnitude
        s_mag = 10*np.log10(s_r**2 + s_i**2)
        s_ph = np.angle(s_r + 1j*s_i)
        S_mag.append (s_mag)
        S_phase.append(s_ph)
        
    return (frequency, S_mag, S_phase)
    
def get_files_by_first_number(folder_path, extension = 'csv'):
    files_dict = {}
    for filename in os.listdir(folder_path):
        if filename.endswith(".%s"%extension):
            match = re.search(r'\d+', filename)
            if match:
                number = int(match.group())
                files_dict[number] = filename
    return files_dict