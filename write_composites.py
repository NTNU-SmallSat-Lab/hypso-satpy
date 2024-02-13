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

sys.path.insert(0,'/home/cameron/Projects/')

files_1 = find_files_and_readers(base_dir="/home/cameron/Dropbox/Data/20220827_CaptureDL_00_erie_2022_08_27T16_05_36/", reader='hypso1_bip')
files_2 = find_files_and_readers(base_dir="/home/cameron/Nedlastinger/20230519_CaptureDL_erie_2023-05-17_1553Z/", reader='hypso1_bip')

scene_1 = Scene(filenames=files_1)
scene_2 = Scene(filenames=files_2, reader_kwargs={'flip': True})

datasets_1 = scene_1.available_dataset_names()
datasets_2 = scene_2.available_dataset_names()

#scene_1.load(datasets_1)
#scene_2.load(datasets_2)

scene_1.load(['latitude', 'longitude', '80', '40', '15'])
scene_2.load(['latitude', 'longitude', '80', '40', '15'])

gamma = 2

s = scene_1
compositor = GenericCompositor("overview")
composite = compositor([s['80'][:,::3], s['40'][:,::3], s['15'][:,::3]]) # Red, Green, Blue
img = to_image(composite)
img.invert([False, False, False])
img.stretch("linear")
img.gamma([gamma, gamma, gamma])
img.save('scene1.png')

s = scene_2
compositor = GenericCompositor("overview")
composite = compositor([s['80'][:,::3], s['40'][:,::3], s['15'][:,::3]]) # Red, Green, Blue
img = to_image(composite)
img.invert([False, False, False])
img.stretch("linear")
img.gamma([gamma, gamma, gamma])
img.save('scene2.png')


