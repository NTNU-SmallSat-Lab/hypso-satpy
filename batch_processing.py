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


# ====== Configuration =======

# Place .nc and .points (GCPs) files in the capture_directory. 
# NB: Filenames should match the same pattern. For example: erie_2022-07-19_1550Z-l1a.nc and erie_2022-07-19_1550Z-bin3.points.
capture_directory = '/home/cameron/Dokumenter/Data/erie'

# Define area of interest
bbox = (-83.534546,41.356196,-81.359009,42.706660) # W. Lake Erie

# Specified resample image resolution:
resolution = (500,500)


# ====== Functions =======

def process_capture(nc_file, points_file, name, bbox, resolution):

    files = [nc_file, points_file]

    scene = Scene(filenames=files, reader='hypso1_l1a_nc')
    datasets = scene.available_dataset_names()
    scene.load(datasets)
    #scene.load(['latitude', 'longitude', '80', '40', '15'])

    area_def = get_area(scene, bbox=bbox, resolution=resolution)

    resampled_scene = scene.resample(area_def, resampler='bilinear', fill_value=np.NaN)

    write_composites(scene, resampled_scene, name, gamma=2)

def get_area(scene, bbox=None, resolution=(500,500)):

    if bbox == None:
        grid_lats = scene['80'].attrs['area'].lats.data
        grid_lons = scene['80'].attrs['area'].lons.data   

        # Is there a function that can do this? Possibly in pyresample.
        lon_min = grid_lons.min()
        lon_max = grid_lons.max()
        lat_min = grid_lats.min()
        lat_max = grid_lats.max()

        bbox = (lon_min,lat_min,lon_max,lat_max)

    area_id = 'roi'
    proj_id = 'roi'
    description = 'roi'
    projection = CRS.from_epsg(4326)
    width = resolution[0]
    height = resolution[1]
    area_extent = list(bbox)

    # Define area definition
    area_def = geometry.AreaDefinition(area_id, proj_id, description, projection,  width, height, area_extent)

    return area_def

def write_composites(scene, resampled_scene, name, gamma=2):

    # Original capture composite
    s = scene
    compositor = GenericCompositor("overview")
    composite = compositor([s['80'][:,::3], s['40'][:,::3], s['15'][:,::3]]) # Red, Green, Blue
    #composite = composite[:,:,::-1] # correct for composite mirroring
    img = to_image(composite[:,:,::-1]) 
    img.invert([False, False, False])
    img.stretch("linear")
    img.gamma([gamma, gamma, gamma])
    img.save('./composites/' + name + '.png')

    # Resampled capture composites
    s = resampled_scene
    compositor = GenericCompositor("overview")
    composite = compositor([s['80'], s['40'], s['15']]) # Red, Green, Blue
    img = to_image(composite)
    img.invert([False, False, False])
    img.stretch("linear")
    img.gamma([gamma, gamma, gamma])
    img.save('./composites/resampled_' + name + '.png')



# ====== Script =======

# Filter files ending in '-l1a.nc' or '-bin3.points'
l1a_files = [os.path.join(capture_directory, file) for file in os.listdir(capture_directory) if file.endswith('l1a.nc')]
bin3_files = [os.path.join(capture_directory, file) for file in os.listdir(capture_directory) if file.endswith('bin3.points')]

# Match pairs of files based on the first part of their file names
matched_pairs = []
for l1a_file in l1a_files:
    l1a_prefix = l1a_file.rsplit('-', maxsplit=1)[0]
    for bin3_file in bin3_files:
        bin3_prefix = bin3_file.rsplit('-', maxsplit=1)[0]
        if l1a_prefix == bin3_prefix:
            l1a_file_prefix = l1a_prefix.split('/')[-1]
            matched_pairs.append((l1a_file, bin3_file, l1a_file_prefix))
            bin3_files.remove(bin3_file)  # Avoid duplicate matches


for pair in matched_pairs:

    nc_file = pair[0]
    points_file = pair[1]
    name = pair[2]

    process_capture(nc_file=nc_file, 
                    points_file=points_file, 
                    name=name, 
                    bbox=bbox, 
                    resolution=resolution)






