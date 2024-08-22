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
from pyresample import load_area
import os

import datetime

sys.path.insert(0,'/home/cameron/Projects/')

nc_file = '/home/cameron/Dokumenter/Data/svalbardeidembukta/svalbardeidembukta_2023-03-16_1214Z-l1a.nc'
points_file = '/home/cameron/Dokumenter/Data/svalbardeidembukta/svalbardeidembukta_2023-03-16_1214Z-bin3.points'


files = [points_file, nc_file]

scene = Scene(filenames=files, reader="hypso1_l1a_nc")
#scene = Scene(filenames=files, reader='hypso1_l1a_nc', reader_kwargs={'flip': True})
datasets = scene.available_dataset_names()

#scene.load(datasets)
scene.load(['band_80', 'band_40', 'band_15', 'rgb'])
#scene.load(['rgb'])

#area_def = get_area(scene, bbox=bbox, resolution=resolution)

area_def = load_area('../areas/van_mijenfjorden.yaml', 'vanmijenfjorden')
#area_def='sval2'

resampled_scene = scene.resample(area_def, resampler='bilinear', fill_value=np.NaN)