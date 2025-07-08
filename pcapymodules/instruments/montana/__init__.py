# -*- coding: utf-8 -*-
"""
Created on Tue Dec 20 13:03:34 2022

@author: prata
"""

import sys
import os


sys.path.append(os.path.dirname(__file__))

import instrument
import cryocore

mycryostat = cryocore.CryoCore('134.74.27.15', tunnel=False)