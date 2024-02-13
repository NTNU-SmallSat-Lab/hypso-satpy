import numpy as np
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
        
        
        self.along_track_dim = req_fh[0].along_track_dim
        self.cross_track_dim = req_fh[0].cross_track_dim
        self.spectral_dim = req_fh[0].spectral_dim

        self.filename = filename

        self.latitude_data = None
        self.longitude_data = None

        self.image_height = self.along_track_dim # row_count
        self.image_width = self.cross_track_dim # column_count/bin_factor
        
        gr = georeferencing.Georeferencer(self.filename, self.image_height, self.image_width)

        self.latitude_data = gr.latitudes
        self.longitude_data = gr.longitudes


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




    

    
    def _calculate_poly_geo_coords_skimage(self, X, Y, lat_c, lon_c):
        
        #X = sum[j=0:order]( sum[i=0:j]( a_ji * x**(j - i) * y**i ))

        #x.T = [a00 a10 a11 a20 a21 a22 ... ann
        #   b00 b10 b11 b20 b21 b22 ... bnn c3]

        #X = (( a_00 * x**(0 - 0) * y**0 ))
        #(( a_10 * x**(1 - 0) * y**0 ))  +  (( a_11 * x**(1 - 1) * y**1 ))
        #(( a_20 * x**(2 - 0) * y**0 ))  +  (( a_21 * x**(2 - 1) * y**1 )) 
        #                                +  (( a_22 * x**(2 - 2) * y**2 ))
    
        c = lat_c
        lat = c[0] + c[1]*X + c[2]*Y + c[3]*X**2 + c[4]*X*Y + c[5]*Y**2

        c = lon_c
        lon = c[0] + c[1]*X + c[2]*Y + c[3]*X**2 + c[4]*X*Y + c[5]*Y**2

        return (lat, lon)
    




