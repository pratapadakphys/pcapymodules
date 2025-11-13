
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
class MyFile:
    """Generic wrapper for simple tabular files (default: CSV)."""
    def __init__(self, filepath):
        self.filepath = filepath
        root, ext = os.path.splitext(filepath)
        if ext.lower() == ".csv":
            self.data = pd.read_csv(filepath)
        else:
            raise ValueError(f"Unrecognized file type for MyFile: {filepath}")

def default_loader(filepath):
    """Default loader: use MyFile for CSV."""
    return MyFile(filepath)

    
class FileSet:
    '''
    files: TYPE: String denoting a folderpath or a list of files
        DESCRIPTION: In this case it will load files under the folder using load_function
    pattern: A dictionary of pattern where key is the variable name and pattern is to match and extract values of the variable from the filename.
        DESCRIPTION: The pattern should be compatible to the python package re.
    '''
    def __init__(self, files, pattern=None, find_text='', filenames=None,
                 file_type='.csv', loader=default_loader):
        if isinstance(files, str):
            # Single folder or file
            if os.path.isdir(files):
                files = load_files(files, find_text, file_type=file_type, loader=loader)
            else:
                files = [loader(files)]
        elif is_list_of_strings(files):
            collected = []
            for item in files:
                if os.path.isdir(item):
                    # Treat as folder
                    collected.extend(
                        load_files(item, find_text, file_type=file_type, loader=loader)
                    )
                else:
                    # Treat as single file
                    collected.append(loader(item))
            files = collected

        if not files:
            raise ValueError("No files loaded into the FileSet.")

        self.df = pd.DataFrame({0: files})
        self._update_filename(filenames)
        self.variable = 'no'
        self.df['no'] = range(len(self.df))

        if pattern is not None:
            self._decode_pattern(pattern)
            
    def _update_filename(self, filenames):
        if filenames is None:
            filenames = []
            for file in self.df.iloc[:,0]:
                filename = os.path.basename(file.filepath).split('/')[-1]
                filenames.append(filename)
                
        self.df['filename'] = filenames
        
    '''
    def _match_filename(self,find_text):
        pass
        r=0; del_list = []
            for filename in self.df['filename']:
                res = re.search(find_text, filename)
                if res is None:
                    del_list.append(r)
                r+=1
    '''
        
    def _decode_pattern(self, pattern): 
        i=0
        for key in pattern:
            if i==0: self.variable = key
            val_list =[]
            for filename in self.df['filename']:
                res = re.search(pattern[key], filename)
                res = re.search(r"[-+]?(?:\d*\.*\d+)", res.group())
                number = float(res.group())
                val_list.append(number)
            self.df[key]=val_list
            i+=1
        
    
def get_file_set (folders, **kwargs):
    if isinstance (folders, dict):
        Fs ={}
        for key in folders:
            Fs[key]= FileSet(folders[key],**kwargs)
        
        return Fs
    
    elif isinstance(folders, list):
        Fs = []
        for f in folders:
            Fs.append(FileSet(f, **kwargs))
        
        return Fs
    
    elif isinstance (folders, str):
        return FileSet(folders, **kwargs)
    
    
def is_list_of_strings(obj):
    """
    Returns True if the given object is a list of strings, False otherwise.
    """
    if not isinstance(obj, list):
        return False
    for item in obj:
        if not isinstance(item, str):
            return False
    return True
    
    
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

def load_files(filepaths=None, find_text = '', file_type='.csv', loader = default_loader):
    """
    Allows user to load multiple files at once. Each file is wrapped by the
    provided `loader` callable (default: MyFile for CSV).

    PARAMETERS
    ---------
    filepaths: str | list[str] | dict[str, str] | None
        - None: open a file dialog
        - str (file or folder): load that path
        - list/dict of str: load multiple paths
    """
    # GUI file picker
    if filepaths is None:
        filepaths = get_files(True)
        batch = [loader(fp) for fp in filepaths]
        return_type = "list of %s File objects" % file_type
        if len(batch) == 1:
            batch = batch[0]
            return_type = "%s File object" % file_type
        print('Successfully loaded %i file(s) in a %s' % (len(filepaths), return_type))
        return batch

    # List of paths
    elif isinstance(filepaths, list):
        batch = []
        for fp in filepaths:
            fname = os.path.basename(fp)
            if find_text in fp and re.search(file_type, fname):
                batch.append(loader(fp))

        count = len(batch)
        return_type = "list of %s File objects" % file_type
        if count == 1:
            batch = batch[0]
            return_type = "%s File object" % file_type

        print('Successfully loaded %i file(s) in a %s' % (count, return_type))
        return batch


    # Dict of paths
    elif isinstance(filepaths, dict):
        batch = {}
        for key, fp in filepaths.items():
            if find_text in fp:
                batch[key] = loader(fp)
        return_type = "dictionary of %s File objects" % file_type
        print('Successfully loaded %i file(s) in a %s' % (len(batch), return_type))
        return batch

    # Folder path
    elif os.path.isdir(filepaths):
        files = []
        for f in os.listdir(filepaths):
            if f.lower().endswith(file_type.lower()) and re.search(find_text, f):
                full = os.path.join(filepaths, f)
                files.append(loader(full))
        return_type = "list of %s File objects" % file_type
        print('Successfully loaded %i file(s) in a %s' % (len(files), return_type))
        return files

    # Single file path
    else:
        return loader(filepaths)
