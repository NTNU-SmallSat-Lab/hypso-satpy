# Run 'source ~/.profile'
import satpy
from satpy import Scene, find_files_and_readers
import sys
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from pyresample import geometry
from pyproj import CRS
from satpy.composites import GenericCompositor
from satpy.writers import to_image
import os

import datetime

sys.path.insert(0,'/home/cameron/Projects/')

files_1 = find_files_and_readers(base_dir="/home/cameron/Dokumenter/Data/erie/combined", reader='hypso1_l1a_nc')# start_time=datetime.datetime(2023, 3, 1, 15, 59))