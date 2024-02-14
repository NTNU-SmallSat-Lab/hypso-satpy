#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""HYPSO-1 File Readers """

import numpy as np
import xarray as xr
from satpy.readers.file_handlers import BaseFileHandler
from shapely.geometry import Polygon
from shapely.wkt import loads
import skimage

import correction.correction as correction

from hypso1_ini import HYPSO1INIFileHandler

'''
class HYPSO1INIFileHandler(BaseFileHandler):
    """HYPSO-1 .ini files."""

    def __init__(self, filename, filename_info, filetype_info, *req_fh, **fh_kwargs):
        super().__init__(filename, filename_info, filetype_info)

        self.filename_info = filename_info
        self.platform_name = 'hypso1'
        self.sensor = "hsi"

        filename = os.path.join(filename, 'capture_config.ini')

        self.ini_capture_config = {}
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

                self.ini_capture_config[key] = value

        self.along_track_dim = self.ini_capture_config['frame_count']
        self.cross_track_dim = self.ini_capture_config['row_count']
        self.spectral_dim = int(self.ini_capture_config['column_count']/self.ini_capture_config['bin_factor'])
'''



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

        # Check for the required reader and if it exists, return its index in the req_fh tuple
        #ini_fh_idx = next((index for index, obj in enumerate(req_fh) if isinstance(obj, HYPSO1INIFileHandler)), None)
        
        # Index of HYPSO1INIFileHandler in req_fh
        ini_fh_idx = 0

        # Load ini_capture_config dict from INI file reader:
        self.ini_capture_config = req_fh[ini_fh_idx].ini_capture_config

        # Load dimensions
        self.along_track_dim = req_fh[ini_fh_idx].along_track_dim
        self.cross_track_dim = req_fh[ini_fh_idx].cross_track_dim
        self.spectral_dim = req_fh[ini_fh_idx].spectral_dim

        # Order of dataset dimensions:
        # First dimension (Y): latitude
        # Second dimension (X): longitude
        # Third dimension (Z): band

        # Load raw datacube from .bip file
        datacube = self._read_bip_file(self.filename)
        
        # Reshape datacube
        # TODO: swap height and width. Note to self: In the calibration code, references to 'height' and 'width' are swapped. For example, whereas in this reader image_width is 120, in the calibration code image_height is 120.
        datacube = datacube.reshape((-1, self.cross_track_dim, self.spectral_dim))[:,:,::-1]

        # Construct capture config dictionary
        capture_config = self.construct_capture_config()

        # Apply corrections to datacube
        datacube, wavelengths, capture_config = correction.run_corrections(datacube, capture_config)

        # Mirror image to correct orientation (moved to corrections)
        #datacube = datacube[:, ::-1, :]

        self.datacube = datacube
        self.wavelengths = wavelengths
        self.capture_config = capture_config



    def construct_capture_config(self):

        '''
        flags = 0x00000200
        camera_ID = 1
        frame_count = 956
        exposure = 30.0063
        fps = 22
        row_count = 684
        column_count = 1080
        sample_divisor = 1
        bin_factor = 9
        aoi_x = 428
        aoi_y = 266
        gain = 0
        temp_log_period_ms = 10000
        '''

        capture_config = {}
        capture_config['aoi_x'] = self.ini_capture_config['aoi_x']
        capture_config['aoi_y'] = self.ini_capture_config['aoi_y']
        capture_config['background_value'] = 8*self.ini_capture_config['bin_factor']
        capture_config['bin_factor'] = self.ini_capture_config['bin_factor']
        capture_config['bin_x'] = self.ini_capture_config['bin_factor']
        capture_config['camera_ID'] = self.ini_capture_config['camera_ID']
        capture_config['column_count'] = self.ini_capture_config['column_count']
        capture_config['exp'] = self.ini_capture_config['exposure'] / 1000 # convert to seconds
        capture_config['flags'] = self.ini_capture_config['flags']
        capture_config['format'] = 'ini'
        capture_config['fps'] = self.ini_capture_config['fps']
        capture_config['frame_count'] = self.ini_capture_config['frame_count']
        capture_config['gain'] = self.ini_capture_config['gain']
        capture_config['image_height'] = self.ini_capture_config['row_count']
        capture_config['image_width'] = int(self.ini_capture_config['column_count']/self.ini_capture_config['bin_factor'])
        capture_config['row_count'] = self.ini_capture_config['row_count']
        capture_config['sample_divisor'] = self.ini_capture_config['sample_divisor']
        capture_config['temp_log_period_ms'] = self.ini_capture_config['temp_log_period_ms']
        capture_config["x_start"] = self.ini_capture_config["aoi_x"]
        capture_config["x_stop"] = self.ini_capture_config["aoi_x"] + self.ini_capture_config["column_count"]
        capture_config["y_start"] = self.ini_capture_config["aoi_y"]
        capture_config["y_stop"] = self.ini_capture_config["aoi_y"] + self.ini_capture_config["row_count"]

        standardDimensions = {
            "nominal": 956,  # Along frame_count
            "wide": 1092  # Along image_height (row_count)
        }

        if capture_config['frame_count'] == standardDimensions["nominal"]:
            capture_config["capture_type"] = "nominal"

        elif capture_config['row_count'] == standardDimensions["wide"]:
            capture_config["capture_type"] = "wide"

        else:
            capture_config["capture_type"] = "custom"

        return capture_config







    def __getitem__(self, item):
        """Get item."""
        return getattr(self.capture_config, item)

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
                dataset = self.datacube[:,:,int(dataset_id['name'])]
                
                # TODO: rename dimensions?
                dataset = xr.DataArray(dataset, dims=["y", "x"])

                dataset.attrs['time'] = self.filename_info['time']
                dataset.attrs['capture_config'] = self.capture_config
                
                return dataset
            else:
                return None
        except ValueError:
            return None

    


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
                'wavelength': self.wavelengths[band]
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
    






