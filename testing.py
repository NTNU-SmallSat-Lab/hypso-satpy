# Run 'source ~/.profile'
import satpy
from satpy import Scene, find_files_and_readers
import sys
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

sys.path.insert(0,'/home/cameron/Projects/')

#print(satpy.config.to_dict())
#print(satpy.available_readers())

files_1 = find_files_and_readers(base_dir="/home/cameron/Dokumenter/Data/erie_2023-03-01_1559Z-l1a", reader='hypso1_l1a_nc')
#files_1 = find_files_and_readers(base_dir="/home/cameron/Nedlastinger/erie_2023-03-01_1559Z-l1a.nc", reader='hypso1_l1a_nc')

scene_1 = Scene(filenames=files_1)

datasets_1 = scene_1.available_dataset_names()

# Don't need to load all the datasets just for testing
#scene_1.load(datasets_1)

scene_1.load(['latitude', 'longitude', '80', '40', '15'])

