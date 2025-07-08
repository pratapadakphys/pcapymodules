import os
import pandas as pd
import numpy as np
import re


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
        S_mag.append (s_mag)
        
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