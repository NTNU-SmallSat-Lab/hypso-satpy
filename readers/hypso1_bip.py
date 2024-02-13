#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""HYPSO-1 File Readers """

import numpy as np
import xarray as xr
from satpy.readers.file_handlers import BaseFileHandler
import os
from shapely.geometry import Polygon
from shapely.wkt import loads
import skimage

from pyproj import CRS
crs = CRS.from_epsg(4326)

#from hypso1_base import HYPSO1FileHandlerBase


class HYPSO1INIFileHandler(BaseFileHandler):
    """HYPSO-1 .ini files."""

    def __init__(self, filename, filename_info, filetype_info, *req_fh, **fh_kwargs):
        super().__init__(filename, filename_info, filetype_info)

        self.filename_info = filename_info
        self.platform_name = 'hypso1'
        self.sensor = "hsi"

        #self.latitude_data = None
        #self.longitude_data = None

        #self.along_track_dim = None
        #self.cross_track_dim = None
        #self.spectral_dim = None

        filename = os.path.join(filename, 'capture_config.ini')

        self.info = {}
        with open(filename, "r") as file:
            for line in file:
                key, value = line.strip().split(' = ')
                key = key.strip()
                if key == 'flags':
                    # If the key is 'flags', interpret the value as hexadecimal
                    value = int(value, 16)
                else:
                    # For other keys, try to convert the value to the appropriate type
                    try:
                        value = int(value)
                    except ValueError:
                        try:
                            value = float(value)
                        except ValueError:
                            pass  # Keep the value as a string if conversion fails

                self.info[key] = value

        self.along_track_dim = self.info['frame_count']
        self.cross_track_dim = self.info['row_count']
        self.spectral_dim = int(self.info['column_count']/self.info['bin_factor'])




class HYPSO1LatDatFileHandler(BaseFileHandler):
    """HYPSO-1 __ files."""

    def __init__(self, filename, filename_info, filetype_info, *req_fh, **fh_kwargs):
        super().__init__(filename, filename_info, filetype_info)
       

        self.filename_info = filename_info
        self.platform_name = 'hypso1'
        self.sensor = "hsi"
       
        self.filename = filename

        self.along_track_dim = req_fh[0].along_track_dim
        self.cross_track_dim = req_fh[0].cross_track_dim
        self.spectral_dim = req_fh[0].spectral_dim

        self.latitude_data = None

        if self.filename.endswith("-latitudes.dat"):
            dtype = np.float32 
            data = np.fromfile(self.filename, dtype=dtype)
            data = data.reshape((self.along_track_dim, self.cross_track_dim))
        else:
            data = None

        self.latitude_data = data

    def get_dataset(self, dataset_id, dataset_info):

        if dataset_id['name'] == 'latitude':
            dataset = xr.DataArray(self.latitude_data, dims=["y", "x"])
            dataset.attrs['standard_name'] = 'latitude'
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






class HYPSO1LonDatFileHandler(BaseFileHandler):
    """HYPSO-1 __ files."""

    def __init__(self, filename, filename_info, filetype_info, *req_fh, **fh_kwargs):
        super().__init__(filename, filename_info, filetype_info)

        self.filename_info = filename_info
        self.platform_name = 'hypso1'
        self.sensor = "hsi"
       
        self.filename = filename

        self.along_track_dim = req_fh[0].along_track_dim
        self.cross_track_dim = req_fh[0].cross_track_dim
        self.spectral_dim = req_fh[0].spectral_dim

        self.longitude_data = None

        if self.filename.endswith("-longitudes.dat"):
            dtype = np.float32 
            data = np.fromfile(self.filename, dtype=dtype)
            data = data.reshape((self.along_track_dim, self.cross_track_dim))
        else:
            data = None

        self.longitude_data = data

    def get_dataset(self, dataset_id, dataset_info):

        if dataset_id['name'] == 'longitude':
            dataset = xr.DataArray(self.longitude_data, dims=["y", "x"])
            dataset.attrs['standard_name'] = 'longitude'
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



class HYPSO1BIPFileHandler(BaseFileHandler):
    """HYPSO-1 .bip files."""

    def __init__(self, filename, filename_info, filetype_info, *req_fh, **fh_kwargs):
        super().__init__(filename, filename_info, filetype_info)

        self.filename_info = filename_info
        self.platform_name = 'hypso1'
        self.sensor = "hypso1"
        self.target = filename_info['target']

        self.along_track_dim = req_fh[0].along_track_dim
        self.cross_track_dim = req_fh[0].cross_track_dim
        self.spectral_dim = req_fh[0].spectral_dim

        #print('Metadata derived from capture_config.ini:')
        #print('Along track dimension: ' + str(along_track_dim))
        #print('Cross track dimension: ' + str(cross_track_dim))
        #print('Spectral dimension: ' + str(spectral_dim))

        # Order of dataset dimensions:
        # First dimension (Y): latitude
        # Second dimension (X): longitude
        # Third dimension (Z): band

        # Load raw datacube from .bip file
        self.datacube = self._read_bip_file(self.filename)
        
        # TODO: swap height and width
        # Note to self: In the calibration code, references to 'height' and 'width' are swapped. For example, whereas in this reader image_width is 120, in the calibration code image_height is 120.
        #Backup: self.datacube = self.datacube.reshape((-1, self.cross_track_dim, self.spectral_dim))[:,:,::-1]
        self.datacube = self.datacube.reshape((-1, self.cross_track_dim, self.spectral_dim))[:,:,::-1]

        # ------ Calibration Hell -------:
        import correction

        # Copy info dict from INI:
        self.info = req_fh[0].info

        self.calibration_info = {}
        self.calibration_info['bin_factor'] = self.info['bin_factor']
        self.calibration_info['bin_x'] = self.info['bin_factor']
        self.calibration_info['background_value'] = 8*self.info['bin_factor']
        self.calibration_info['exp'] = self.info['exposure'] / 1000 # convert to seconds
        self.calibration_info['image_height'] = self.info['row_count']
        self.calibration_info['image_width'] = int(self.info['column_count']/self.info['bin_factor'])
        self.calibration_info['frame_count'] = self.info['frame_count']
        self.calibration_info['column_count'] = self.info['column_count']
        self.calibration_info["x_start"] = self.info["aoi_x"]
        self.calibration_info["x_stop"] = self.info["aoi_x"] + self.info["column_count"]
        self.calibration_info["y_start"] = self.info["aoi_y"]
        self.calibration_info["y_stop"] = self.info["aoi_y"] + self.info["row_count"]

        self.standardDimensions = {
            "nominal": 956,  # Along frame_count
            "wide": 1092  # Along image_height (row_count)
        }

        if self.info['frame_count'] == self.standardDimensions["nominal"]:
            self.calibration_info["capture_type"] = "nominal"

        elif self.info['row_count'] == self.standardDimensions["wide"]:
            self.calibration_info["capture_type"] = "wide"

        else:
            self.calibration_info["capture_type"] = "custom"

        self.calibration_coefficients_dict = correction.get_calibration_coefficients_path(self.calibration_info)

        self.calibration_coefficients = correction.get_coefficients_from_dict(self.calibration_coefficients_dict, 
                                                                              self.calibration_info)

        self.datacube = correction.get_calibrated_and_corrected_cube(self.calibration_info, 
                                                                     self.datacube, 
                                                                     self.calibration_coefficients)


        self.spectral_coefficients_file = correction.get_spectral_coefficients_path()
        
        self.spectral_coefficients = correction.get_coefficients_from_file(self.spectral_coefficients_file)

        self.wavelengths = self.spectral_coefficients

        # Round bands to nearest integer
        self.wavelengths_rounded = []
        for band in self.wavelengths:
            self.wavelengths_rounded.append(round(band))

        # If there are duplicates, round to 1 decimal
        if len(set(self.wavelengths_rounded)) != 120:
            self.wavelengths_rounded = []
            for band in self.wavelengths:
                self.wavelengths_rounded.append(round(band, 1))

        # Check length of wavelengths and wavelenghts_rounded list
        if len(self.wavelengths) != 120:
            # Replace the list with a new list of length 120 starting from 0
            self.wavelengths = [band for band in range(0,120)]
        if len(self.wavelengths_rounded) != 120:
            # Replace the list with a new list of length 120 starting from 0
            self.wavelengths_rounded = [band for band in range(0,120)]

        # Flip or mirror image
        flip = fh_kwargs.get("flip", None)
        if flip is not None: 
            if flip:
                print('[INFO] Flipping capture ' + self.filename + ' in the cross track dimension.')
                self.datacube = self.datacube[:, ::-1, :]

    def __getitem__(self, item):
        """Get item."""
        return getattr(self.calibration_info, item)

    @property
    def start_time(self):
        """Start timestamp of the dataset."""
        return self.filename_info['time']

    @property
    def end_time(self):
        """End timestamp of the dataset."""
        return self.filename_info['time']
    
    @property
    def testing(self):
        """End timestamp of the dataset."""
        return 'test'



    def get_dataset(self, dataset_id, dataset_info):
        
        try:
            if 0 <= int(dataset_id['name']) < 120:
                self.dataset = self.datacube[:,:,int(dataset_id['name'])]
                self.dataset = xr.DataArray(self.dataset, dims=["y", "x"])
                self.dataset.attrs['time'] = self.filename_info['time']
                self.dataset.attrs['calibration_info'] = self.calibration_info
                return self.dataset
            else:
                self.dataset = None
                return self.dataset
        except ValueError:
            self.dataset = None
            return self.dataset

    


    def available_datasets(self, configured_datasets=None):
        #"Add information to configured datasets."
        # pass along existing datasets

        variables = []
        for is_avail, ds_info in (configured_datasets or []):
            #yield is_avail, ds_info
            variables.append(ds_info)

        bands = []
        for band in [number for number in range(0, 120)]:
            ds_info = {
                'file_type': self.filetype_info['file_type'],
                'resolution': None,
                'name': str(band),
                'standard_name': 'sensor_band_identifier',
                'coordinates': ['latitude', 'longitude'],
                'units': "%",
                'wavelength': self.wavelengths_rounded[band]
            }
            #yield True, ds_info
            bands.append(ds_info)


        combined = variables + bands

        for c in combined:
            yield True, c

    def _read_bip_file(self, filename):

        return np.fromfile(filename, dtype='uint16')







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
            return dataset
        elif dataset_id['name'] == 'longitude':
            dataset = xr.DataArray(self.longitude_data, dims=["y", "x"])
            dataset.attrs['standard_name'] = 'longitude'
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
    






