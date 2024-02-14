
import numpy as np
import xarray as xr
from satpy.readers.file_handlers import BaseFileHandler
from satpy.readers.netcdf_utils import NetCDF4FileHandler

# This reader relies on the satpy netcdf_utils module
# https://satpy.readthedocs.io/en/stable/api/satpy.readers.netcdf_utils.html


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

        #print(type(self.file_content))
        #for key in self.file_content.keys():
        #    print(key)
        #print(self.file_content.keys())
        #print(len(self.file_content.keys()))

        key = 'metadata/capture_config/attr/aoi_x'
        print(type(self.file_content[key]))
        print(self.file_content[key])


        a = self.get_and_cache_npxr('products/Lt')

        print(a.shape)
        print(a)

        # Flip or mirror image
        #datacube = datacube[:, ::-1, :]


        # TODO: set these for GCP reader
        #self.along_track_dim = req_fh[0].along_track_dim
        #self.cross_track_dim = req_fh[0].cross_track_dim
        #self.spectral_dim = req_fh[0].spectral_dim

    def construct_capture_config(self, ini_capture_config: dict):

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

        #TODO: construct this dictionary

        capture_config = {}
        capture_config['aoi_x'] = self.file_content['metadata/capture_config/attr/aoi_x']
        '''
        capture_config['aoi_y'] = ini_capture_config['aoi_y']
        capture_config['background_value'] = 8*ini_capture_config['bin_factor']
        capture_config['bin_factor'] = ini_capture_config['bin_factor']
        capture_config['bin_x'] = ini_capture_config['bin_factor']
        capture_config['camera_ID'] = ini_capture_config['camera_ID']
        capture_config['column_count'] = ini_capture_config['column_count']
        capture_config['exp'] = ini_capture_config['exposure'] / 1000 # convert to seconds
        capture_config['flags'] = ini_capture_config['flags']
        capture_config['format'] = 'ini'
        capture_config['fps'] = ini_capture_config['fps']
        capture_config['frame_count'] = ini_capture_config['frame_count']
        capture_config['gain'] = ini_capture_config['gain']
        capture_config['image_height'] = ini_capture_config['row_count']
        capture_config['image_width'] = int(ini_capture_config['column_count']/ini_capture_config['bin_factor'])
        capture_config['row_count'] = ini_capture_config['row_count']
        capture_config['sample_divisor'] = ini_capture_config['sample_divisor']
        capture_config['temp_log_period_ms'] = ini_capture_config['temp_log_period_ms']
        capture_config["x_start"] = ini_capture_config["aoi_x"]
        capture_config["x_stop"] = ini_capture_config["aoi_x"] + ini_capture_config["column_count"]
        capture_config["y_start"] = ini_capture_config["aoi_y"]
        capture_config["y_stop"] = ini_capture_config["aoi_y"] + ini_capture_config["row_count"]

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

        '''

        return capture_config

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
    
def print_nested_dict(d, indent=0):
    for key, value in d.items():
        if isinstance(value, dict):
            print('  ' * indent + str(key) + ':')
            print_nested_dict(value, indent + 1)
        else:
            print('  ' * indent + str(key) + ': ' + str(value))