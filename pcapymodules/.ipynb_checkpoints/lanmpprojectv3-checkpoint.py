# -*- coding: utf-8 -*-
"""
Created on Thu Dec  8 14:13:33 2022

@author: prata
"""
import os
import re
import datetime

class Project:
    def __init__(self, name, device, fileno, directory= None):
        self.name = name
        self.device = device
        self.fileno = fileno
        self.spot_location = 'Unknown'
        self.directory = directory
        
    
    @property
    def filetag(self):
        _filetag = "[{0}-{1}-{2}]".format(self.name, self.device, self.fileno)
        return _filetag
    
    
    
    @filetag.setter
    def filetag(self, value):
        self.get_project (value)
        
    @property
    def new_filetag(self):
        self.fileno += 1
        return self.filetag
        
    def get_project (self, filename):
        tag = get_tag (filename)
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
    
    def take_note(self, note, topic = None):
        filename = "logbook.txt"
        
        if self.directory is not None:
            filename = os.path.join(self.directory, filename)
        file = open(filename,"a")
        file.write('\n'+str(datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')))
        file.write('\t'+self.filetag)
        if topic is not None:
            file.write('\t'+topic)
        if type(note) == str:
            note = {'note':note}
        for key in note:
            file.write('\n'+'\t'+str(key) + '\t:\t' + str(note[key]) ) 
        file.close()
        
    def get_new_file_name(self, config=None):
        fname = decorate_filename(self.spot_location, config,  file_prefix = self.new_filetag )
        return fname
    
def get_tag(path):
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
        
    print ('No file tag found!')
    return None

def get_fileno(path):
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
    tag = get_tag(path)
    if tag == None: return None
    ss= tag[1:-1].split('-',2)
    try: fileno = int(ss[2])
    except: 
        print("I can not determine the fileno! Set to 0.")
    return fileno
    
    
def get_file_info(path, version = 0, pattern = None, variable = 'Number', whole_search = False):
    filename = os.path.basename(path).split('/')[-1]
    fullname = filename
    tag = get_tag(filename)
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
    def __init__(self, lens, measurement_type, exposure_time = None, wavelength = None, roi = None, light_source = None):
        self.lens = lens
        self.measurement_type = measurement_type
        
        self.exposure_time = exposure_time
        self.wavelength = wavelength
        self.roi = roi      
        
        self.light_source = light_source
        self.input_path = None
        self.output_path = None
        
        self.comment = None
        
    def __str__(self):
        text = self.lens + ' ' + self.measurement_type
        
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
        if self.output_path is not None:
            light_text += ' '+str(self.output_path)
            
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