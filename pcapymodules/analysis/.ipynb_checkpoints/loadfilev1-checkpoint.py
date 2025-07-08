import os
import re
import pandas as pd
import tkinter as tk
from tkinter import filedialog as fdialog

'''
This is a package to load single or multiple files into list, or dictionary in a smarter way.
The return type dynamically depends on the input type.
The package also provides way to create panda dataframe from a set of files.
'''
def load_function(filepath):
    return filepath

def get_files(mult=False):
    """
    Uses tkinter to allow UI source file selection
    Adapted from: http://stackoverflow.com/a/7090747
    """
    root = tk.Tk()
    root.withdraw()
    filepaths = fdialog.askopenfilenames()
    if not mult:
        filepaths = filepaths[0]
    root.destroy()
    return filepaths

def load_files(filepaths=None):
    """
    Allows user to load multiple files at once. Each file is stored as an SpeFile object in the list batch.
    
    PARAMETERS
    ---------
    filepaths: TYPE = String (Filepath or folder path), list/dictionary of strings (Multiple filepaths), or None (Prompt user to select files using a dialog box)
        
    RETURN
    -------
        If the input is a filepath,  return a SpeFile object.
        If the input is a folderpath, return a list of SpeFile objects corresponding to all the .spe files sitting inside the folder (not subfolders).
        If the input is a list of multiple filepaths, return a list of SpeFile objects of the provided filepaths.
        If the input is a dictionary of multiple filepaths, return a dictionary of SpeFile objects of the provided filepaths identified with same keys.
            
    """
    if filepaths is None:
        filepaths = get_files(True)
        batch = [[] for _ in range(0, len(filepaths))]
        for file in range(0, len(filepaths)):
            batch[file] = load_function(filepaths[file])
        return_type = "list of SpeFile objects"
        if len(batch) == 1:
            batch = batch[0]
            return_type = "SpeFile object"
        print('Successfully loaded %i file(s) in a %s' % (len(filepaths), return_type))
        return batch
    elif isinstance ( filepaths, list):
        batch = [[] for _ in range(0, len(filepaths))]
        for file in range(0, len(filepaths)):
            batch[file] = load_function(filepaths[file])
        return_type = "list of SpeFile objects"
        if len(batch) == 1:
            batch = batch[0]
            return_type = "SpeFile object"
        print('Successfully loaded %i file(s) in a %s' % (len(filepaths), return_type))
        return batch
    
    elif isinstance ( filepaths, dict):
        batch = {}
        for key in filepaths:
            batch[key] = load_function(filepaths[key])
        return_type = "dictionary of SpeFile objects"
        print('Successfully loaded %i file(s) in a %s' % (len(filepaths), return_type))
        return batch
    
    elif os.path.isdir(filepaths):
        files = []
        for f in os.listdir(filepaths):
            if re.search('.spe', f):
                files.append(load_function(filepaths + r'//' + f))
        return_type = "list of SpeFile objects"
        print('Successfully loaded %i file(s) in a %s' % (len(files), return_type))
        return files
    else: 
        return load_function(filepaths)
    
    
class FileSet:
    def __init__(self, files, ref_files = None, pattern = None):
        '''
        files: TYPE: String denoting a folderpath or a list of files
            DESCRIPTION: In this case it will load files under the folder using load_function
        pattern: A dictionary of pattern where key is the variable name and pattern is to match and extract values of the variable from the filename.
            DESCRIPTION: The pattern should be compatible to the python package re.
        '''
        if isinstance(files, str):
            self.files = load_files(files)
            
        else: self.files = files
        self.df = pd.DataFrame(self.files, columns = ['files'])
        
        self.ref_files = None
        if ref_files is not None:
            if isinstance(bgfiles, str):
                self.ref_files = load_files(ref_files)
            else: self.ref_files = ref_files
            self.df['ref_files'] = ref_files
        
        self.variables = []
        self.size = len(self.files)
        if pattern is not None: 
            self._decode_pattern(pattern)
        
    def _decode_pattern(self, pattern): 
        for key in pattern:
            val_list =[]
            for file in self.files:
                filename = os.path.basename(file.filepath).split('/')[-1]
                res = re.search(pattern[key], filename)
                res = re.search(r"[-+]?(?:\d*\.*\d+)", res.group())
                number = float(res.group())
                val_list.append(number)
            self.df[key]=val_list
            self.variables.append(key)
        
    
def get_file_set (folders, **kwargs):
    if isinstance (folders, dict):
        Fs ={}
        for key in folders:
            Fs[key]= FileSet(folders[key],**kwargs)
        
        return Fs
    
    elif isinstance(folders, list):
        Fs = []
        for f in folders:
            Fs.append(FileSet(f), **kwargs)
        
        return Fs
    
    elif isinstance (folders, str):
        return FileSet(folders, **kwargs)
    