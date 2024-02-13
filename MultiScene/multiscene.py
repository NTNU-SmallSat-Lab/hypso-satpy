# Run 'source ~/.profile'
import satpy
from satpy import Scene, find_files_and_readers
import sys
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from pyresample import geometry
from pyproj import CRS
from satpy import Scene, MultiScene
from satpy.multiscene import timeseries, temporal_rgb, stack
from satpy.writers import to_image
from satpy.composites import GenericCompositor

sys.path.insert(0,'/home/cameron/Projects/')
#print(sys.path)

#print(satpy.config.to_dict())
#print(satpy.available_readers())

files_1 = find_files_and_readers(base_dir="/home/cameron/Dropbox/Data/20220827_CaptureDL_00_erie_2022_08_27T16_05_36/", reader='hypso1_bip')
#files = find_files_and_readers(base_dir="/home/cameron/Nedlastinger/20231215_CaptureDL_erie_2023-12-14_1543Z/", reader='hypso1_bip')
#files = find_files_and_readers(base_dir="/home/cameron/Dropbox/Data/20231215_CaptureDL_erie_2023-12-14_1543Z/", reader='hypso1_bip')
#files = find_files_and_readers(base_dir="/home/cameron/Nedlastinger/20230821_CaptureDL_erie_2023-08-20_1538Z/", reader='hypso1_bip')
#files = find_files_and_readers(base_dir="/home/cameron/Nedlastinger/20230519_CaptureDL_erie_2023-05-17_1553Z/", reader='hypso1_bip')

files_2 = find_files_and_readers(base_dir="/home/cameron/Nedlastinger/20230519_CaptureDL_erie_2023-05-17_1553Z/", reader='hypso1_bip')


scene_1 = Scene(filenames=files_1, reader_kwargs={'flip': True})
scene_2 = Scene(filenames=files_2)

datasets_1 = scene_1.available_dataset_names()
datasets_2 = scene_2.available_dataset_names()

#scene_1.load(datasets_1)
#scene_2.load(datasets_2)

scene_1.load(['latitude', 'longitude', '80', '40', '15'])
scene_2.load(['latitude', 'longitude', '80', '40', '15'])


if True:
    scene_1['latitude'].attrs['area'] = scene_1['80'].attrs['area']
    scene_1['longitude'].attrs['area'] = scene_1['80'].attrs['area']

    scene_2['latitude'].attrs['area'] = scene_2['80'].attrs['area']
    scene_2['longitude'].attrs['area'] = scene_2['80'].attrs['area']

grid_lats = scene_1['80'].attrs['area'].lats.data
grid_lons = scene_1['80'].attrs['area'].lons.data

lon_min = grid_lons.min()
lon_max = grid_lons.max()
lat_min = grid_lats.min()
lat_max = grid_lats.max()

bbox = (lon_min,lat_min,lon_max,lat_max)

area_id = 'roi'
proj_id = 'roi'
description = 'roi'
projection = CRS.from_epsg(4326)
width = 1000
height = 1000
area_extent = list(bbox)

area_def = geometry.AreaDefinition(area_id, proj_id, description, projection,  width, height, area_extent)

local_scene_1 = scene_1.resample(area_def, resampler='bilinear', fill_value=np.NaN)
local_scene_2 = scene_2.resample(area_def, resampler='bilinear', fill_value=np.NaN)

scenes = [local_scene_1, local_scene_2]
mscn = MultiScene(scenes)
mscn.load(['latitude', 'longitude', '80', '40', '15'])
new_mscn = mscn.resample(area_def)
#new_mscn = mscn
#blended_scene = new_mscn.blend()

blended_scene = new_mscn.blend(blend_function=timeseries)

blended_scene.load(['latitude', 'longitude', '80', '40', '15'])

#blended_scene.to_xarray()
blended_scene.to_xarray_dataset()

print('Done.')
