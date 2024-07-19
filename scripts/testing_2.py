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

sys.path.insert(0,'/home/cameron/Projects/')
#satpy.config.set(config_path=['/home/cameron/Projects/'])

#print(satpy.config.to_dict())
#print(satpy.available_readers())


nc_file = '/home/cameron/Dokumenter/Data/erie/erie_2023-03-01_1559Z-l1a.nc'
points_file = '/home/cameron/Dokumenter/Data/erie/erie_2023-03-01_1559Z-bin3.points'
scene_1 = Scene(filenames=[nc_file, points_file], reader='hypso1_l1a_nc')

print(points_file)

#scene_1 = Scene(filenames=[points_file, nc_file], reader='hypso1_l1a_nc')