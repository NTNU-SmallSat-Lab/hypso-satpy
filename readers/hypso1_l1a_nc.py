
import numpy as np
import xarray as xr
from satpy.readers.file_handlers import BaseFileHandler
from satpy.readers.netcdf_utils import NetCDF4FileHandler

# This reader relies on the satpy netcdf_utils module
# https://satpy.readthedocs.io/en/stable/api/satpy.readers.netcdf_utils.html


from georeferencing import calculate_poly_geo_coords_skimage



class HYPSO1L1ANCFileHandler(NetCDF4FileHandler):
    """HYPSO-1 L1a NetCDF files."""

    def __init__(self, filename, filename_info, filetype_info, *req_fh, **fh_kwargs):
        super().__init__(filename, filename_info, filetype_info)

        self.filename_info = filename_info
        self.platform_name = 'hypso1'
        self.sensor = "hypso1"
        self.target = filename_info['target']

        fh = self._get_file_handle()

        self.collect_metadata(None, fh)

        print(type(self.file_content))
        print(self.file_content.keys())

        a = self.get_and_cache_npxr('products/Lt')

        print(a.shape)
        print(a)

        # TODO: set these for GCP reader
        #self.along_track_dim = req_fh[0].along_track_dim
        #self.cross_track_dim = req_fh[0].cross_track_dim
        #self.spectral_dim = req_fh[0].spectral_dim

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
                'wavelength': 1 #self.wavelengths_rounded[band]
            }
            #yield True, ds_info
            bands.append(ds_info)


        combined = variables + bands

        for c in combined:
            yield True, c

    def _read_bip_file(self, filename):

        return np.fromfile(filename, dtype='uint16')