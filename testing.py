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

#print(satpy.config.to_dict())
#print(satpy.available_readers())

files_1 = find_files_and_readers(base_dir="/home/cameron/Dokumenter/Data/erie_2023-03-01_1559Z-l1a", reader='hypso1_l1a_nc')
#files_1 = find_files_and_readers(base_dir="/home/cameron/Nedlastinger/erie_2023-03-01_1559Z-l1a.nc", reader='hypso1_l1a_nc')

scene_1 = Scene(filenames=files_1)
#scene_1 = Scene(filenames=files_1, reader_kwargs={'flip': True})

datasets_1 = scene_1.available_dataset_names()

# Don't need to load all the datasets just for testing
#scene_1.load(datasets_1)

scene_1.load(['latitude', 'longitude', '80', '40', '15'])

grid_lats = scene_1['80'].attrs['area'].lats.data
grid_lons = scene_1['80'].attrs['area'].lons.data

# Is there a function that can do this? Possibly in pyresample.
lon_min = grid_lons.min()
lon_max = grid_lons.max()
lat_min = grid_lats.min()
lat_max = grid_lats.max()

bbox = (lon_min,lat_min,lon_max,lat_max)
#bbox = (-83.534546,41.356196,-82.359009,42.706660) # W. Lake Erie
#bbox = (-83.534546,41.356196,-81.359009,42.706660) # W. Lake Erie

print(bbox)

area_id = 'western_lake_erie'
proj_id = 'roi'
description = 'roi'
projection = CRS.from_epsg(4326)
width = 500
height = 1000
area_extent = list(bbox)

# Define area definition
area_def = geometry.AreaDefinition(area_id, proj_id, description, projection,  width, height, area_extent)


# Reading Area Definitions: https://satpy.readthedocs.io/en/stable/resample.html#store-area-definitions
#from pyresample import load_area
#area_def_loaded = load_area(filename)

# Resample to area_def
local_scene_1 = scene_1.resample(area_def, resampler='bilinear', fill_value=np.NaN)



print('Writing composites...')

gamma = 2

# Original capture composites

s = scene_1
compositor = GenericCompositor("overview")
composite = compositor([s['80'][:,::3], s['40'][:,::3], s['15'][:,::3]]) # Red, Green, Blue
#composite = composite[:,:,::-1] # correct for composite mirroring
img = to_image(composite[:,:,::-1]) 
img.invert([False, False, False])
img.stretch("linear")
img.gamma([gamma, gamma, gamma])
img.save('./composites/nc_scene1.png')


# Resampled capture composites

s = local_scene_1
compositor = GenericCompositor("overview")
composite = compositor([s['80'], s['40'], s['15']]) # Red, Green, Blue
img = to_image(composite)
img.invert([False, False, False])
img.stretch("linear")
img.gamma([gamma, gamma, gamma])
img.save('./composites/nc_resampled_scene1.png')


print('Done.')






