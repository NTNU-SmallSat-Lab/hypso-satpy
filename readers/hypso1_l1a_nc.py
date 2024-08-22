#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""HYPSO-1 NetCDF File Reader """

# This reader relies on the satpy netcdf_utils module
# https://satpy.readthedocs.io/en/stable/api/satpy.readers.netcdf_utils.html


import math as m
import numpy as np
import xarray as xr
from satpy.readers.file_handlers import BaseFileHandler
from satpy.readers.netcdf_utils import NetCDF4FileHandler
from satpy.dataset.dataid import WavelengthRange

#import correction.correction as correction

#from hypso import Hypso


class HYPSO1L1aNCFileHandler(NetCDF4FileHandler):
    """HYPSO-1 L1a NetCDF files."""

    def __init__(self, filename, filename_info, filetype_info, *req_fh, **fh_kwargs):
        super().__init__(filename, filename_info, filetype_info)

        self.filename_info = filename_info
        self.platform_name = 'hypso1'
        self.sensor = "hypso1"
        self.target = filename_info['target']

        fh = self._get_file_handle()

        self.collect_metadata(None, fh)

        # Construct capture config dictionary
        capture_config = self.construct_capture_config()

        use_hypso_package = False


        # Load datacube as xarray
        datacube = self.get_and_cache_npxr('products/Lt')

        # Convert xarray datacube to numpy datacube
        datacube = datacube.to_numpy()

        # Convert type
        datacube = datacube.astype('uint16')

        # Apply corrections to datacube
        #datacube, wavelengths = correction.run_corrections(datacube, capture_config)

        wavelengths = list(range(1,121))

        # Mirror image to correct orientation (moved to corrections)
        datacube = datacube[:, ::-1, :]
        
        # Flip or mirror image
        #flip = fh_kwargs.get("flip", None)

        # Code copied from https://github.com/NTNU-SmallSat-Lab/ground_systems/blob/4c41925f5fbf6161a60d273cfee82bce22cfeffc/scripts/capture_processing/adcs-tm-strip.py#L152

        samples_total = self.file_content['/dimension/adcssamples']

        st_quaternion_s = self.get_and_cache_npxr('metadata/adcs/quaternion_s')
        st_quaternion_x = self.get_and_cache_npxr('metadata/adcs/quaternion_x')
        st_quaternion_y = self.get_and_cache_npxr('metadata/adcs/quaternion_y')
        st_quaternion_z = self.get_and_cache_npxr('metadata/adcs/quaternion_z')

        #quat_len = len(st_quaternion_s)
        quat = np.empty((samples_total,4))
        quat[:,0] = st_quaternion_s
        quat[:,1] = st_quaternion_x
        quat[:,2] = st_quaternion_y
        quat[:,3] = st_quaternion_z

        velocity_x = self.get_and_cache_npxr('metadata/adcs/velocity_x')
        velocity_y = self.get_and_cache_npxr('metadata/adcs/velocity_y')
        velocity_z = self.get_and_cache_npxr('metadata/adcs/velocity_z')
        #velocity_len = len(velocity_x)
        velocity = np.empty((samples_total,3))
        velocity[:,0] = velocity_x
        velocity[:,1] = velocity_y
        velocity[:,2] = velocity_z

        st_vel_angle = np.zeros([samples_total,1])

        for i in range(samples_total):
            st_vel_angle[i] = compute_st_vel_angles(quat[i,:], velocity[i,:])

        if st_vel_angle.mean() > 90.0:
            # was pointing away from velocity direction --> don't flip 
            flip = False
        else: 
            # was pointing in velocity direction --> do flip
            flip = True

        if flip is not None and flip: 
            datacube = datacube[:, ::-1, :]

        # Convert datacube from float64 to float32
        datacube = datacube.astype('float32')

        self.lines = capture_config['lines']
        self.samples = capture_config['samples']
        self.bands = capture_config['bands']

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
        capture_config['aoi_x'] = self.file_content['metadata/capture_config/attr/aoi_x']
        capture_config['aoi_y'] = self.file_content['metadata/capture_config/attr/aoi_y']
        capture_config['background_value'] = 8*self.file_content['metadata/capture_config/attr/bin_factor']
        capture_config['bin_factor'] = self.file_content['metadata/capture_config/attr/bin_factor']
        capture_config['bin_x'] = self.file_content['metadata/capture_config/attr/bin_factor']
        capture_config['camera_ID'] = self.file_content['metadata/capture_config/attr/camID']
        capture_config['column_count'] = self.file_content['metadata/capture_config/attr/column_count']
        capture_config['exp'] = self.file_content['metadata/capture_config/attr/exposure'] / 1000 # convert to seconds
        capture_config['flags'] = self.file_content['metadata/capture_config/attr/flags']
        capture_config['format'] = self.file_content['metadata/capture_config/attr/format']
        capture_config['fps'] = self.file_content['metadata/capture_config/attr/fps']
        capture_config['frame_count'] = self.file_content['metadata/capture_config/attr/frame_count']
        capture_config['gain'] = self.file_content['metadata/capture_config/attr/gain']
        capture_config['image_height'] = self.file_content['metadata/capture_config/attr/row_count']
        capture_config['image_width'] = int(self.file_content['metadata/capture_config/attr/column_count']/self.file_content['metadata/capture_config/attr/bin_factor'])
        capture_config['row_count'] = self.file_content['metadata/capture_config/attr/row_count']
        capture_config['sample_divisor'] = self.file_content['metadata/capture_config/attr/sample_div']
        #capture_config['temp_log_period_ms'] = 
        capture_config["x_start"] = self.file_content["metadata/capture_config/attr/aoi_x"]
        capture_config["x_stop"] = self.file_content["metadata/capture_config/attr/aoi_x"] + self.file_content["metadata/capture_config/attr/column_count"]
        capture_config["y_start"] = self.file_content["metadata/capture_config/attr/aoi_y"]
        capture_config["y_stop"] = self.file_content["metadata/capture_config/attr/aoi_y"] + self.file_content["metadata/capture_config/attr/row_count"]

        # Set dimensions
        capture_config["lines"] = self.file_content["metadata/capture_config/attr/frame_count"]
        capture_config["samples"] = self.file_content["metadata/capture_config/attr/row_count"]
        capture_config["bands"] = int(self.file_content['metadata/capture_config/attr/column_count']/self.file_content['metadata/capture_config/attr/bin_factor'])

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
        return self.filename_info['start_time']

    @property
    def end_time(self):
        """End timestamp of the dataset."""
        return self.filename_info['start_time']

    def get_dataset(self, dataset_id, dataset_info):
        try:
            name = dataset_id['name']
            band_str = name.split('_')[-1]
            band_num = int(band_str)
            if 0 <= band_num < 120:
                dataset = self.datacube[:,:,band_num]
                dataset = xr.DataArray(dataset, dims=["y", "x"])
                dataset.attrs['start_time'] = self.filename_info['start_time']
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
                'name': 'band_' + str(band),
                'standard_name': 'sensor_band_identifier',
                'coordinates': ['latitude', 'longitude'],
                'units': "%",
                #'wavelength': self.wavelengths[band],
                'wavelength': WavelengthRange(min=self.wavelengths[band], central=self.wavelengths[band], max=self.wavelengths[band], unit="nm")
            }
            #yield True, ds_info
            bands.append(ds_info)

        combined = variables + bands

        for c in combined:
            yield True, c


    






def compute_st_vel_angles(quat, vel):

    # Checks which direction the star tracker is pointing relative to velocity vector
    # Return true if the star tracker is pointing in velocity direction
    # Return false if the star tracker is pointing away from velocity direction

    # code from https://github.com/NTNU-SmallSat-Lab/ground_systems/blob/8e73a02055e3ebf935f306ac927c12674cb434dc/scripts/capture_processing/adcs-tm-strip.py#L72
    # code from https://github.com/NTNU-SmallSat-Lab/hypso-package/blob/bf9b3464137211278584ad0064afddf3a01d0c11/hypso/georeference/georef/geometric.py#L73

    body_x_body = np.array([1.0, 0.0, 0.0]) # this is star tracker direction
    #body_z_body = np.array([0.0, 0.0, 1.0])

    '''
    quat must be a four element list of numbers or 4 element nump array
    returns a 3x3 numpy array containing the rotation matrix
    '''
    mag = m.sqrt(quat[0]**2 + quat[1]**2 + quat[2]**2 + quat[3]**2)
    quat[0] /= mag
    quat[1] /= mag
    quat[2] /= mag
    quat[3] /= mag
 
    w2 = quat[0]*quat[0]
    x2 = quat[1]*quat[1]
    y2 = quat[2]*quat[2]
    z2 = quat[3]*quat[3]

    wx = quat[0]*quat[1]
    wy = quat[0]*quat[2]
    wz = quat[0]*quat[3]
    xy = quat[1]*quat[2]
    xz = quat[1]*quat[3]
    zy = quat[3]*quat[2]

    mat = np.zeros([3,3])

    mat[0,0] = w2+x2-y2-z2
    mat[1,0] = 2.0*(xy+wz)
    mat[2,0] = 2.0*(xz-wy)
    mat[0,1] = 2.0*(xy-wz)
    mat[1,1] = w2-x2+y2-z2
    mat[2,1] = 2.0*(zy+wx)
    mat[0,2] = 2.0*(xz+wy)
    mat[1,2] = 2.0*(zy-wx)
    mat[2,2] = w2-x2-y2+z2
    body_x_teme = np.matmul(mat,body_x_body)
    #body_z_teme = np.matmul(mat,body_z_body)
    
    vellen = m.sqrt(vel[0]**2 + vel[1]**2 + vel[2]**2)
    cos_vel_angle = (vel[0]*body_x_teme[0] + vel[1]*body_x_teme[1] + vel[2]*body_x_teme[2]) / vellen
    velocity_angle = m.acos(cos_vel_angle)*180.0/m.pi

    return velocity_angle

