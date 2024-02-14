#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""HYPSO-1 latitude.dat File Reader """

import numpy as np
import xarray as xr
from satpy.readers.file_handlers import BaseFileHandler

class HYPSO1LatDatFileHandler(BaseFileHandler):
    """HYPSO-1 latitude.dat files."""

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