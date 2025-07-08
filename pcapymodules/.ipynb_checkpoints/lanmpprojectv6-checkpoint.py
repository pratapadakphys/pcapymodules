# -*- coding: utf-8 -*-
"""
Created on Thu Dec  8 14:13:33 2022

@author: prata

version 6
last modified on 2023-04-24
"""
import os
import re
import datetime
import json


config_path = os.path.expanduser('~\Documents\pca_py_files')
if not os.path.exists(config_path):
    os.makedirs(config_path)
CONFIG_FILE = os.path.join(config_path, 'project_info.json')   
    
if not os.path.exists(CONFIG_FILE):
    with open(CONFIG_FILE, 'w') as fp: 
        json.dump({},fp)

class Project:
    '''
    A class to hold project information, implement convention, etc.
    
    Parameters
        ---------
        name : String (should not contain '-')
            The shorthand name of the project
        device: Integer
            The number assigned to the device under test
        fileno: Integer. Default is None (In that case it automatically searches the integer assigned to the last file of the DUT with same project and device no.
            An unique integer assigned to each data file. It is automatatically incremented.
        folder: String (Folder path). Default is the current working directory.
            The master folder where the subfolders and data files will be stored. 
            Also a logbook (note file) will be created for storing note.
            If folder does not exists, it is created automatically.
    '''
    def __init__(self, name, device, fileno=None, folder=os.getcwd()):
        self.name = name
        self.device = device
        self.fileno = fileno
        self.root_name = ''
        self.folder = folder
        self.subfolder = ''
    
        
    @property 
    def fileno(self):
        return self._fileno
    
    @fileno.setter
    def fileno(self, value):
        info = json.load(open(CONFIG_FILE)) 
        key = self.name + '-' + str(self.device)
        if value is None:
            if key in info:
                self._fileno = info[key]
                return
            else:
                value = 0
                print ('PCA WARNING: Fileno is starting from zero. If already file exists for this device, please update the correct file number.')
        
        info[key] = value
        with open(CONFIG_FILE, 'w') as fp: json.dump(info, fp)
        self._fileno = value   
            
            
    @property 
    def folder(self):
        return self._folder
    
    @folder.setter
    def folder(self, value):
        '''
        '''
        if not os.path.exists(value):
            os.makedirs(value)
        self._folder = value
        
    @property 
    def subfolder(self):
        '''
        Set a subfolder under the project folder.
        The subfolder is created if it does not exist already.
        '''
        return self._subfolder
    
    @subfolder.setter
    def subfolder(self, value):
        fullpath = os.path.join(self.folder,value)
        if not os.path.exists(fullpath):
            os.makedirs(fullpath)
        self._subfolder = value
    
    @property
    def filetag(self):
        '''
        A unique tag assigned to each data file.
        The tag encode the information of project name, device number, and file number.
        The format is '[%s-%d-%d]'.
        '''
        _filetag = "[{0}-{1}-{2}]".format(self.name, self.device, self.fileno)
        return _filetag
    
    
    
    @filetag.setter
    def filetag(self, value):
        self.decode_tag (value)
        
    '''
    @property
    def new_filetag(self):
        
        Generates a new file tag by incrementing the file number.
        
        self.fileno += 1
        return self.filetag
    '''
        
    def decode_tag (self, filename):
        '''
        Extract the project information from a filename.
        '''
        tag = Tag.read (filename)
        if tag is not None:
            self._tag_to_project(tag)
        return self
        
    def _tag_to_project(self, tag):
        ss= tag[1:-1].split('-',2)
        self.name = ss[0]
        self.device = ss[1]
        try: self.fileno = int(ss[2])
        except: 
            self.fileno =0
            print("I can not determine the fileno! Set to 0.")
        return self
    
    def __str__ (self):
        return self.filetag
    
    def take_note(self, note, category = None):
        '''
        Take note in a more streamlined way.
        Automatically notes down the date and time, latest file tag so that the context of the note can be understood easily.
        
        Parameter
        ---------
        note: String or a dictioanry storing information
            The text to store as a note.
            Dictionary form can be useful to stored information in 'key : value' format.
        category: String. Default is None
            To categorize the note types. Example: Setup change, Note, Naming Error, etc.
        
        '''
        
        filename = "logbook.txt"
        
        if self.folder is not None:
            filename = os.path.join(self.folder, filename)
        file = open(filename,"a")
        file.write('\n'+str(datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')))
        file.write('\t'+self.filetag)
        if category is not None:
            file.write('\t'+category)
        if type(note) == str:
            note = {'note':note}
        for key in note:
            file.write('\n'+'\t'+str(key) + '\t:\t' + str(note[key]) ) 
        file.close()
        
    def get_new_file_name(self, config=None):
        self.fileno +=1
        fname = decorate_filename(self.root_name, config,  file_prefix = self.filetag )
        return os.path.join(self.folder, self.subfolder,fname)
    
class Tag:
    def read(cls, path):
        '''
        Determines the tag from a file path if the tag exists.

        Prameter
        --------
        path: File path
            Path from which the tag to be determined.  It can be any string as well.
        return
        ------
        String: the tag in format '[%s-%d-%d]'
        '''
        filename = os.path.basename(path).split('/')[-1]
        #print (filename)
        if filename[0] == '[':
            if filename.find(']')>0:
                s= filename[1:].split(']', 1)[0]
                if len(s.split('-',6))==3:
                    return '['+s+']'
                else:
                    print ('Incorrect file tag format!')
                    return None

        print ('Warning: No file tag found!')
        return None


    def split(cls, path):
        '''
        Parameters
        ----------
        path : TYPE = String
            DESCRIPTION. Filename or filepath or tag

        Returns
        -------
        fileno : TYPE = Integer
            DESCRIPTION.

        '''
        fileno = 0
        tag = cls.read(path)
        if tag is None: return (None, None, None)
        ss= tag[1:-1].split('-',2)
        p = ss[0]; d = ss[1]
        try: fileno = int(ss[2])
        except: 
            print("I can not determine the fileno! Set to 0.")
        return (p,d,fileno)

    def combine(cls, filenames):
        filenos = []
        for fname in filenames:
            (p,d,fno)=cls.split(fname)
            if p is None:
                return (None, None)
            filenos.append(fno)
        tag =  r'[%s-%s-%d_%d]'%(p, d, min(filenos),max(filenos))
        return (tag, filenos)

    
def get_file_info(path, version = 0, pattern = None, variable = 'Number', whole_search = False):
    filename = os.path.basename(path).split('/')[-1]
    fullname = filename
    tag = Tag.read(filename)
    fileno = get_fileno (tag)
    filename = os.path.splitext(filename)[0]
    info = {}
    name = filename.split('] ')[1]
    parts = name.split(', ')
    offset = 0
    filename = parts[offset+0]
    lens = parts[offset+1].split(' ')[0]
    measurement_type = parts[offset+1].split(' ')[1]
    spe_settings = parts[offset+2].split(' ')
    (_wavelength, _exposure_time, _roi) = spe_settings
    light = parts [offset+3]
    if len(parts)>4:comment = parts[offset+4]
    else: comment = None
    info['tag']= tag
    info['fileno']=fileno
    info['name']=filename
    info['lens']=lens
    info['measurement type']=measurement_type
    info['wavelength']=_wavelength
    info['exposure time'] = _exposure_time
    info['roi'] = _roi
    info['light'] = light
    info['comment'] = comment
    
    if pattern != None:
        if whole_search:
            res = re.search(pattern, fullname)
        else:
            res = re.search(pattern, info['name'])
        res = re.search(r"[-+]?(?:\d*\.*\d+)", res.group())
        #print(res.group())
        number = float(res.group())
        info[variable] = number
    
    return info

class User:
    def __init__(self, name):
        self.name = name
        self.email = None
        
class LightSource:
    def __init__(self, name, wavelength = None, power = None, aperture = None, input_filter = None, info = None):
        self.name = name
        self.wavelength = wavelength
        self.aperture = aperture
        self.power = power
        self.input_filter = input_filter
        self.info = info
        
    def __str__(self):
        text = self.name
        if self.wavelength is not None:
            text += ' '
            if isinstance (self.wavelength, tuple): 
                text += '{}-{}nm'.format(self.wavelength[0],self.wavelength[1])
            elif isinstance (self.wavelength, int): 
                text += '{}nm'.format(self.wavelength)
            else:
                text += self.wavelength
        if self.power is not None:
            text += ' ' 
            if isinstance (self.power, int): 
                text += '{}uW'.format(self.power)
            else:
                text += self.power
        if self.aperture is not None:
            text += ' ' 
            if isinstance (self.aperture, int): 
                text += '{}um'.format(self.aperture)
            else:
                text += self.aperture
                
        if self.input_filter is not None:
            text += ' %s'%self.input_filter
            
        if self.info is not None:
            text += ' %s'%self.info
            
        return text
            
        
class MeasurementConfiguration:
    def __init__(self, lens, measurement_type, exposure_time = None, wavelength = None, roi = None, light_source = None, input_path = None, output_path = None):
        self.lens = lens
        self.measurement_type = measurement_type
        
        self.exposure_time = exposure_time
        self.wavelength = wavelength
        self.roi = roi      
        
        self.light_source = light_source
        self.input_path = input_path
        self.output_path = output_path
        
        self.comment = None
        
    def __str__(self):
        text = self.lens + ' ' + self.measurement_type
        if self.output_path is not None:
            text += ' '+str(self.output_path)
            
            
        spe_text = ''
        if self.wavelength is not None:
            if isinstance (self.wavelength, tuple): 
                spe_text += '{}-{}nm'.format(self.wavelength[0],self.wavelength[1])
            else: 
                spe_text += '{}nm'.format(self.wavelength)
        if self.exposure_time is not None:
            spe_text += ' ' + str(self.exposure_time) + 'ms'
        if self.roi is not None:
            spe_text += ' r' + str(self.roi)
            
        if spe_text != '':
            text += ', ' + spe_text
            
        light_text = ''
        if self.light_source is not None:
            light_text += str(self.light_source)
        if self.input_path is not None:
            light_text += ' '+str(self.input_path)
        
            
        if light_text != '':
            text += ', ' + light_text
            
        if self.comment is not None: 
            text += ', ' + self.comment
            
        return text
            
    
def decorate_filename(filename, config = None,  file_prefix = None, file_suffix = None ):
    _text = ''
    if config is not None:
        _text = str(config)
            
    if file_prefix is not None: filename = file_prefix + ' ' + filename    
    if _text != '': filename += ', ' + _text
    if file_suffix is not None: filename += ' ['+file_suffix+']'
    return filename


class Flake:
    def __init__(self, name, material):
        self.name = name
        self.thickness = None
        self.material = material