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

from glob import glob

sys.path.insert(0,'/home/cameron/Projects/')

#print(satpy.config.to_dict())
#print(satpy.available_readers())


files_1 = find_files_and_readers(base_dir="/home/cameron/Dokumenter/Data/erie/erie_2022-08-27_1605Z-l1a", reader='hypso1_l1a_nc')
files_2 = find_files_and_readers(base_dir="/home/cameron/Dokumenter/Data/erie/erie_2023-03-01_1559Z-l1a", reader='hypso1_l1a_nc')
files_3 = find_files_and_readers(base_dir="/home/cameron/Dokumenter/Data/erie/erie_2023-05-17_1553Z-l1a", reader='hypso1_l1a_nc')
files_3 = glob('/home/cameron/Dokumenter/Data/svalbardeidembukta/svalbardeidembukta_2023-03-14_14*')

scene_1 = Scene(filenames=files_1, reader='hypso1_l1a_nc', reader_kwargs={'flip': True})
scene_2 = Scene(filenames=files_2, reader='hypso1_l1a_nc')
scene_3 = Scene(filenames=files_3, reader='hypso1_l1a_nc', reader_kwargs={'flip': True})
#scene_1 = Scene(filenames=files_1, reader_kwargs={'flip': True})

datasets_1 = scene_1.available_dataset_names()
datasets_2 = scene_2.available_dataset_names()
datasets_3 = scene_3.available_dataset_names()

# Don't need to load all the datasets just for testing
#scene_1.load(datasets_1)
#scene_2.load(datasets_2)

scene_1.load(['latitude', 'longitude', '80', '40', '15'])
scene_2.load(['latitude', 'longitude', '80', '40', '15'])
scene_3.load(['latitude', 'longitude', '80', '40', '15'])


def get_area(scene):

    grid_lats = scene['80'].attrs['area'].lats.data
    grid_lons = scene['80'].attrs['area'].lons.data   

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
    width = 1000
    height = 1000
    area_extent = list(bbox)

    # Define area definition
    area_def = geometry.AreaDefinition(area_id, proj_id, description, projection,  width, height, area_extent)

    return area_def


area_def_1 = get_area(scene_1)
area_def_2 = get_area(scene_2)
area_def_3 = get_area(scene_3)


# Resample to area_def
local_scene_1 = scene_1.resample(area_def_1, resampler='bilinear', fill_value=np.NaN)
local_scene_2 = scene_2.resample(area_def_2, resampler='bilinear', fill_value=np.NaN)
local_scene_3 = scene_3.resample(area_def_3, resampler='bilinear', fill_value=np.NaN)

local_scene_3.save_datasets(writer='geotiff')



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
img.save('./composites/nc_scene_1.png')

s = scene_2
compositor = GenericCompositor("overview")
composite = compositor([s['80'][:,::3], s['40'][:,::3], s['15'][:,::3]]) # Red, Green, Blue
#composite = composite[:,:,::-1] # correct for composite mirroring
img = to_image(composite[:,:,::-1]) 
img.invert([False, False, False])
img.stretch("linear")
img.gamma([gamma, gamma, gamma])
img.save('./composites/nc_scene_2.png')

s = scene_3
compositor = GenericCompositor("overview")
composite = compositor([s['80'][:,::3], s['40'][:,::3], s['15'][:,::3]]) # Red, Green, Blue
#composite = composite[:,:,::-1] # correct for composite mirroring
img = to_image(composite[:,:,::-1]) 
img.invert([False, False, False])
img.stretch("linear")
img.gamma([gamma, gamma, gamma])
img.save('./composites/nc_scene_3.png')


# Resampled capture composites

s = local_scene_1
compositor = GenericCompositor("overview")
composite = compositor([s['80'], s['40'], s['15']]) # Red, Green, Blue
img = to_image(composite)
img.invert([False, False, False])
img.stretch("linear")
img.gamma([gamma, gamma, gamma])
img.save('./composites/nc_resampled_scene_1.png')

s = local_scene_2
compositor = GenericCompositor("overview")
composite = compositor([s['80'], s['40'], s['15']]) # Red, Green, Blue
img = to_image(composite)
img.invert([False, False, False])
img.stretch("linear")
img.gamma([gamma, gamma, gamma])
img.save('./composites/nc_resampled_scene_2.png')

s = local_scene_3
compositor = GenericCompositor("overview")
composite = compositor([s['80'], s['40'], s['15']]) # Red, Green, Blue
img = to_image(composite)
img.invert([False, False, False])
img.stretch("linear")
img.gamma([gamma, gamma, gamma])
img.save('./composites/nc_resampled_scene_3.png')

print('Done.')






