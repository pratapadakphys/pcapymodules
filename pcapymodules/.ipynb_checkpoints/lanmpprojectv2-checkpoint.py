# -*- coding: utf-8 -*-
"""
Created on Thu Dec  8 14:13:33 2022

@author: prata
"""
import os
import re
import datetime

class Project:
    def __init__(self, name, device, fileno):
        self.name = name
        self.device = device
        self.fileno = fileno
        
    
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
    
    def take_note(self, note, topic = None, directory = None):
        filename = "logbook.txt"
        if directory is not None:
            filename = os.path.join(directory, filename)
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
    
    
def get_file_info(path, version = 0, pattern = None, variable = 'Number'):
    filename = os.path.basename(path).split('/')[-1]
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
        
