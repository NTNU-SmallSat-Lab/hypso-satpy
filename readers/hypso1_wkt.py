#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""HYPSO-1 footprint-wkt.txt File Reader """

import numpy as np
import xarray as xr
from satpy.readers.file_handlers import BaseFileHandler
from shapely.geometry import Polygon
from shapely.wkt import loads


class HYPSO1FootprintWKTFileHandler(BaseFileHandler):
    """HYPSO-1 footprint-wkt.txt files."""

    def __init__(self, filename, filename_info, filetype_info, *req_fh, **fh_kwargs):
        super().__init__(filename, filename_info, filetype_info)

        self.filename_info = filename_info
        self.platform_name = 'hypso1'
        self.sensor = "hypso1"
        self.target = filename_info['target']

        self.filename = filename

        self.along_track_dim = req_fh[0].along_track_dim
        self.cross_track_dim = req_fh[0].cross_track_dim
        self.spectral_dim = req_fh[0].spectral_dim

        self.latitude_data = None
        self.longitude_data = None

        file = open(self.filename,'r')
        wkt_footprint = file.read()
        file.close()


        wkt_footprint = loads(wkt_footprint)

        # Parse the WKT to create a Shapely Polygon
        #polygon = Polygon.from_wkt(wkt_footprint)
        polygon = Polygon(wkt_footprint.coords)

        # Extract the coordinates of the vertices
        vertices = list(polygon.exterior.coords)

        # Initialize a dictionary to track extreme vertices
        extreme_vertices_dict = {}

        # Populate the dictionary with extreme vertices
        for vertex in vertices:
            x, y = vertex
            if x == min(vertices, key=lambda v: v[0])[0] or x == max(vertices, key=lambda v: v[0])[0]:
                extreme_vertices_dict[x] = vertex
            elif y == min(vertices, key=lambda v: v[1])[1] or y == max(vertices, key=lambda v: v[1])[1]:
                extreme_vertices_dict[y] = vertex

        # Convert the dictionary values back to a list of extreme vertices
        extreme_vertices = list(extreme_vertices_dict.values())

        # Sort the extreme vertices by x-coordinate
        extreme_vertices.sort(key=lambda v: v[0])
    
        points = extreme_vertices

        # Alternatively, create polygon, get bounds, and find nearest polygon corner points to the bounds corner points (derived from min and max values)

        # Sort the points based on x-coordinate (longitude)
        sorted_by_longitude = sorted(points, key=lambda p: p[0])

        # Identify top left and bottom left points
        bottom_left, bottom_right = sorted_by_longitude[:2]

        # Sort the points based on y-coordinate (latitude)
        sorted_by_latitude = sorted(points, key=lambda p: p[1])

        # Identify top right and bottom right points
        top_right, top_left = sorted_by_latitude[-2:]

        # latitude:
        self.image_height = self.along_track_dim # row_count 

        # longitude:
        self.image_width = self.cross_track_dim # column_count/bin_factor 

        img_coords = np.zeros((4,2))
        geo_coords = np.zeros((4,2))

        # Construct pairs of GCPs from the image corners
        img_coords[0,0] = 0 # row
        img_coords[0,1] = 0 # col
        geo_coords[0,0] = top_left[1]
        geo_coords[0,1] = top_left[0]

        img_coords[1,0] = 0
        img_coords[1,1] = self.image_width
        geo_coords[1,0] = top_right[1]
        geo_coords[1,1] = top_right[0]

        img_coords[2,0] = self.image_height
        img_coords[2,1] = 0
        geo_coords[2,0] = bottom_left[1]
        geo_coords[2,1] = bottom_left[0]

        img_coords[3,0] = self.image_height
        img_coords[3,1] = self.image_width
        geo_coords[3,0] = bottom_right[1]
        geo_coords[3,1] = bottom_right[0]

        # Estimate transform (projective, not polynomial)
        t_projective = skimage.transform.estimate_transform('projective', img_coords, geo_coords)

        # Create transfrom
        tform = skimage.transform.ProjectiveTransform(matrix=t_projective)

        # Create empty arrays to write lat and lon data
        lats = np.empty((self.image_height, self.image_width))
        lons = np.empty((self.image_height, self.image_width))

        # Iterate through coords and calculate lat and lon values
        for Y in range(0,self.image_height):
            for X in range(0,self.image_width):
                coords = tform((Y, X))
                lats[Y,X] = coords[0][0]
                lons[Y,X] = coords[0][1]

        self.latitude_data = lats
        self.longitude_data = lons


    def get_dataset(self, dataset_id, dataset_info):

        if dataset_id['name'] == 'latitude':
            dataset = xr.DataArray(self.latitude_data, dims=["y", "x"])
            dataset.attrs['standard_name'] = 'latitude'
            dataset.attrs['units'] = 'degrees_north'
            dataset.attrs['resolution'] = -999 # TODO
            dataset.attrs['sensor'] = 'HYPSO-1'
            return dataset
        elif dataset_id['name'] == 'longitude':
            dataset = xr.DataArray(self.longitude_data, dims=["y", "x"])
            dataset.attrs['standard_name'] = 'longitude'
            dataset.attrs['units'] = 'degrees_east'
            dataset.attrs['resolution'] = -999 # TODO
            dataset.attrs['sensor'] = 'HYPSO-1'
            return dataset
        else:
            dataset = None
            return dataset

    @property
    def start_time(self):
        """Start timestamp of the dataset."""
        return self.filename_info['time']

    @property
    def end_time(self):
        """End timestamp of the dataset."""
        return self.filename_info['time']
    