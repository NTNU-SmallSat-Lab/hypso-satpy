#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""HYPSO-1 longitudes.dat File Reader """

import numpy as np
import xarray as xr
from satpy.readers.file_handlers import BaseFileHandler

class HYPSO1LonDatFileHandler(BaseFileHandler):
    """HYPSO-1 longitudes.dat files."""

    def __init__(self, filename, filename_info, filetype_info, *req_fh, **fh_kwargs):
        super().__init__(filename, filename_info, filetype_info)

        self.filename_info = filename_info
        self.platform_name = 'hypso1'
        self.sensor = "hsi"
       
        self.filename = filename

        self.lines = req_fh[0].lines
        self.samples = req_fh[0].samples
        self.bands = req_fh[0].bands

        self.longitude_data = None

        if self.filename.endswith("-longitudes.dat"):
            dtype = np.float32 
            data = np.fromfile(self.filename, dtype=dtype)
            data = data.reshape((self.lines, self.samples))
            data = data[:,::-1] # correctly mirror capture
        else:
            data = None

        self.longitude_data = data

    def get_dataset(self, dataset_id, dataset_info):

        if dataset_id['name'] == 'longitude':
            longitude_data = self.longitude_data
            dataset = xr.DataArray(longitude_data, dims=["y", "x"])
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