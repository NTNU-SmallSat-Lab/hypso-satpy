
#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""HYPSO-1 .POINTS File Reader """

import xarray as xr
from satpy.readers.file_handlers import BaseFileHandler
import georeferencing.georeferencing as georeferencing

class HYPSO1GCPPointsFileHandler(BaseFileHandler):
    """HYPSO-1 GCP .points file reader that does NOT generate latitude and longitude arrays."""

    def __init__(self, filename, filename_info, filetype_info, *req_fh, **fh_kwargs):
        super().__init__(filename, filename_info, filetype_info)
        
        self.filename_info = filename_info
        self.platform_name = 'hypso1'
        self.sensor = "hypso1"

        self.gcp_list = georeferencing.GCPList(filename)

class HYPSO1GCPPointsLatLonFileHandler(HYPSO1GCPPointsFileHandler):
    """HYPSO-1 GCP .points file reader that generates latitude and longitude arrays."""

    def __init__(self, filename, filename_info, filetype_info, *req_fh, **fh_kwargs):
        super().__init__(filename, filename_info, filetype_info)
        
        self.filename = filename

        self.lines = req_fh[0].lines
        self.samples = req_fh[0].samples
        self.bands = req_fh[0].bands
        
        self.latitude_data = None
        self.longitude_data = None
        
        gr = georeferencing.Georeferencer(self.filename, self.lines, self.samples)

        latitudes = gr.latitudes
        longitudes = gr.longitudes

        # Mirror image to correct orientation (moved to georeferencing)
        #latitudes = latitudes[:,::-1]
        #longitudes = longitudes[:,::-1]

        self.latitude_data = latitudes
        self.longitude_data = longitudes

        # Flip or mirror image
        #flip = fh_kwargs.get("flip", None)
        #if flip is not None and flip: 
        #    self.latitude_data = self.latitude_data[:, ::-1]
        #    self.longitude_data = self.longitude_data[:, ::-1]

    def get_dataset(self, dataset_id, dataset_info):

        if dataset_id['name'] == 'latitude':
            latitude_data = self.latitude_data
            dataset = xr.DataArray(latitude_data, dims=["y", "x"])
            dataset.attrs['standard_name'] = 'latitude'
            return dataset
        elif dataset_id['name'] == 'longitude':
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
        return self.filename_info['start_time']

    @property
    def end_time(self):
        """End timestamp of the dataset."""
        return self.filename_info['start_time']



    




