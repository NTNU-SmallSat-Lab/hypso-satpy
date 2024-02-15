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

from glob import glob

scene_1 = Scene(filenames=glob('/home/cameron/Dokumenter/Data/svalbardeidembukta/svalbardeidembukta_2023-03-25_*'), reader='hypso1_l1a_nc')


