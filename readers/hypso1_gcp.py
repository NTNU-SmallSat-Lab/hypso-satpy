
#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""HYPSO-1 .POINTS File Reader """

import xarray as xr
from satpy.readers.file_handlers import BaseFileHandler
from georeferencing.georeferencing import Georeferencer

class HYPSO1GCPPointsFileHandler(BaseFileHandler):
    """HYPSO-1 GCP .points file reader that does NOT generate latitude and longitude arrays."""

    def __init__(self, filename, filename_info, filetype_info, *req_fh, **fh_kwargs):
        super().__init__(filename, filename_info, filetype_info)
        
        self.filename = filename

        self.filename_info = filename_info
        self.platform_name = 'hypso1'
        self.sensor = "hypso1"

        # Retrieve image_mode from filename pattern
        self.image_mode = self.filename_info['image_mode']

        # TODO: create Georeferencer object from this?
        #self.gcp_list = georeferencing.GCPList(filename)

class HYPSO1GCPPointsLatLonFileHandler(HYPSO1GCPPointsFileHandler):
    """HYPSO-1 GCP .points file reader that generates latitude and longitude arrays."""

    def __init__(self, filename, filename_info, filetype_info, *req_fh, **fh_kwargs):
        super().__init__(filename, filename_info, filetype_info)
        
        # These values are loaded from the required file handler (usually from the l1a reader) automatically passed in the req_fh argument
        self.lines = req_fh[0].lines
        self.samples = req_fh[0].samples
        self.bands = req_fh[0].bands
        
        self.latitude_data = None
        self.longitude_data = None
        
        gr = Georeferencer(self.filename, 
                                          cube_height=self.lines, 
                                          cube_width=self.samples, 
                                          image_mode=self.image_mode,
                                          origin_mode='qgis', #TODO: add support for changing this
                                          crs='epsg:4326' #TODO: add support for changing this
                                          )

        self.latitude_data = gr.latitudes
        self.longitude_data = gr.longitudes

        # Mirror image to correct orientation (moved to georeferencing)
        #latitudes = latitudes[:,::-1]
        #longitudes = longitudes[:,::-1]

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
            dataset.attrs['units'] = 'degrees_north'
            dataset.attrs['resolution'] = -999 # TODO
            dataset.attrs['sensor'] = 'HYPSO-1'
            return dataset
        elif dataset_id['name'] == 'longitude':
            longitude_data = self.longitude_data
            dataset = xr.DataArray(longitude_data, dims=["y", "x"])
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
        return self.filename_info['start_time']

    @property
    def end_time(self):
        """End timestamp of the dataset."""
        return self.filename_info['start_time']



    




