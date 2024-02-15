#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""HYPSO-1 .BIP File Reader """

import numpy as np
import xarray as xr
from satpy.readers.file_handlers import BaseFileHandler
import correction.correction as correction
from hypso1_ini import HYPSO1INIFileHandler

class HYPSO1BIPFileHandler(BaseFileHandler):
    """HYPSO-1 .bip files."""

    def __init__(self, filename, filename_info, filetype_info, *req_fh, **fh_kwargs):
        super().__init__(filename, filename_info, filetype_info)

        self.filename_info = filename_info
        self.platform_name = 'hypso1'
        self.sensor = "hypso1"
        self.target = filename_info['target']

        # Get index of HYPSO1INIFileHandler in req_fh
        # Check for the required reader and if it exists, return its index in the req_fh tuple
        #ini_fh_idx = next((index for index, obj in enumerate(req_fh) if isinstance(obj, HYPSO1INIFileHandler)), None)
        #ini_fh_idx = 0

        # Load ini_capture_config dict from INI file reader:
        self.ini_capture_config = req_fh[0].ini_capture_config

        # Construct capture config dictionary
        capture_config = self.construct_capture_config()

        self.lines = capture_config['lines']
        self.samples = capture_config['samples']
        self.bands = capture_config['bands']

        # Load raw datacube from .bip file
        datacube = np.fromfile(self.filename, dtype='uint16')
        
        # Reshape datacube.
        datacube = datacube.reshape((-1, self.samples, self.bands))[:,:,::-1]

        # Apply corrections to datacube
        datacube, wavelengths = correction.run_corrections(datacube, capture_config)

        # Mirror image to correct orientation (moved to corrections)
        #datacube = datacube[:, ::-1, :]

        # Convert datacube from float64 to float16
        #datacube = datacube.astype('float16')

        print(np.info(datacube))
        print('Any NaN?')
        print(np.isnan(datacube).any())

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
        #capture_config['temp_log_period_ms'] = self.ini_capture_config['temp_log_period_ms']
        capture_config["x_start"] = self.ini_capture_config["aoi_x"]
        capture_config["x_stop"] = self.ini_capture_config["aoi_x"] + self.ini_capture_config["column_count"]
        capture_config["y_start"] = self.ini_capture_config["aoi_y"]
        capture_config["y_stop"] = self.ini_capture_config["aoi_y"] + self.ini_capture_config["row_count"]

        # Set dimensions
        capture_config["lines"] = self.ini_capture_config["frame_count"]
        capture_config["samples"] = self.ini_capture_config["row_count"]
        capture_config["bands"] = int(self.ini_capture_config['column_count']/self.ini_capture_config['bin_factor'])

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

    def get_dataset(self, dataset_id, dataset_info):
        try:
            if 0 <= int(dataset_id['name']) < 120:
                dataset = self.datacube[:,:,int(dataset_id['name'])]
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





