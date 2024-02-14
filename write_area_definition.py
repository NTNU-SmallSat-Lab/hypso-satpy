#!/usr/bin/env python
# -*- coding: utf-8 -*-

from pyproj import CRS
from pyresample import geometry
import os

bbox = (-83.534546,41.356196,-82.359009,42.706660) # W. Lake Erie
bbox = (13.364868,77.401491,17.265015,77.915669) # Van Mijenfjorden

print(bbox)

area_id = 'van_mijenfjorden'
proj_id = 'roi'
description = 'roi'
projection = CRS.from_epsg(4326)
width = 500
height = 1000
area_extent = list(bbox)

area_def = geometry.AreaDefinition(area_id, proj_id, description, projection,  width, height, area_extent)

# Writing Area Definitions: https://pyresample.readthedocs.io/en/stable/howtos/geometry_utils.html#writing-to-disk
filename = os.path.join('.', 'areas', area_id + '.yaml')
with open(filename, 'w') as file:
    file.write(area_def.dump())
