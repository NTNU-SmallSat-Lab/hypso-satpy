import numpy as np
from scipy import interpolate
import os

'''
# type in the relevant path the the calibration coeffs on your 
coeff_path = '/Users/cameron/Projects/cal-char-corr/FM-calibration/Coefficients/'
spectral_coeffs = np.genfromtxt(coeff_path+'spectral_coeffs_FM_order2.csv', delimiter=',')
rad_coeffs = np.genfromtxt(coeff_path + 'rad_coeffs_FM_binx9_2022_08_06_Finnmark_recal_a.csv', delimiter=',')

# this is just a bunch of calibration stuff that shouldn't change much
# you do need to check the exposure (exp) in the capture config.ini file

bin_x = 9 # binning factor
background_value = 8*bin_x
x_start = 428 # aoi_x
x_stop = 1508 # aoi_x + column_count 
y_start = 266 # aoi_y
y_stop = 950 # aoi_y + row_count
exp = 50/1000 # convert ms to s

image_height = 684 # row_count
image_width = 120 # column_count/bin_factor
im_size = image_height*image_width

metad = [exp, image_height, image_width, x_start, x_stop, y_start, y_stop, bin_x]
cube = cube.reshape((-1,image_height,image_width))
'''






def run_corrections(datacube, capture_config: dict):


    calibration_coefficients_dict = get_calibration_coefficients_path(capture_config)

    calibration_coefficients = get_coefficients_from_dict(calibration_coefficients_dict, 
                                                                    capture_config)

    datacube = get_calibrated_and_corrected_cube(capture_config, 
                                                            datacube, 
                                                            calibration_coefficients)


    spectral_coefficients_file = get_spectral_coefficients_path()
    
    spectral_coefficients = get_coefficients_from_file(spectral_coefficients_file)


    wavelengths = get_wavelength_list(spectral_coefficients)


    # Mirror image to correct orientation
    datacube = datacube[:, ::-1, :]

    return datacube, wavelengths, capture_config






def get_wavelength_list(spectral_coefficients):
    wavelengths = spectral_coefficients

    # Round bands to nearest integer
    wavelengths_rounded = []
    for band in wavelengths:
        wavelengths_rounded.append(round(band))

    # If there are duplicates, round to 1 decimal
    if len(set(wavelengths_rounded)) != 120:
        wavelengths_rounded = []
        for band in wavelengths:
            wavelengths_rounded.append(round(band, 1))

    # Fall back to naming sequentially
    if len(wavelengths_rounded) != 120:
        return [band for band in range(0,120)]

    return wavelengths_rounded





#a few functions copied from Marie's calibration code, should update to just use as a library

def pixel_to_wavelength(x, spectral_coeffs):
    if len(spectral_coeffs) == 2:
        w = spectral_coeffs[1] + spectral_coeffs[0]*x
    elif len(spectral_coeffs) == 3:
        w = spectral_coeffs[2] + spectral_coeffs[1]*x + spectral_coeffs[0]*x*x
    elif len(spectral_coeffs) == 4:
        w = spectral_coeffs[3] + spectral_coeffs[2]*x + spectral_coeffs[1]*x*x + spectral_coeffs[0]*x*x*x
    elif len(spectral_coeffs) == 5:
        w = spectral_coeffs[4] + spectral_coeffs[3]*x + spectral_coeffs[2]*x*x + spectral_coeffs[1]*x*x*x + spectral_coeffs[0]*x*x*x*x
    else: 
        print('Please update spectrally_calibrate function to include this polynomial.')
        print('Returning 0.')
        w = 0
    return w

def apply_spectral_calibration(x_start, x_stop, image_width, spectral_coeffs):  
    x = np.linspace(x_start,x_stop,image_width) 
    w = pixel_to_wavelength(x, spectral_coeffs)
    return w

def apply_radiometric_calibration(frame, exp, background_value, radiometric_calibration_coefficients):
    ''' Assumes input is 12-bit values, and that the radiometric calibration
    coefficients are the same size as the input image.
    
    Note: radiometric calibration coefficients have original size (684,1080),
    matching the "normal" AOI of the HYPSO-1 data (with no binning).'''
    
    frame = frame - background_value
    frame_calibrated = frame * radiometric_calibration_coefficients / exp
    
    return frame_calibrated

'''
def calibrate_cube(cube, metadata, spectral_coeffs, rad_coeffs, background_value):
    
    [exp, image_height, image_width, x_start, x_stop, y_start, y_stop, bin_x] = metadata
    
    ## Spectral calibration
    w = apply_spectral_calibration(x_start, x_stop, image_width, spectral_coeffs)
    # x = np.linspace(x_start,x_stop,image_width) 
    # w = util.pixel_to_wavelength(x, spectral_coeffs)
    
    ## Radiometric calibration
    num_frames = cube.shape[0]
    cube_calibrated = np.zeros([num_frames, image_height, image_width])
    for i in range(num_frames):
        frame = cube[i,:,:]
        frame_calibrated = apply_radiometric_calibration(frame, exp, background_value, rad_coeffs)
        cube_calibrated[i,:,:] = frame_calibrated
    
    ## Smile and keystone correction
    # TODO
    
    return cube_calibrated, w, metadata
'''





def get_calibration_coefficients_path(info: dict) -> dict:
    csv_file_radiometric = None
    csv_file_smile = None
    csv_file_destriping = None

    if info["capture_type"] == "custom":

        # Radiometric ---------------------------------
        full_rad_coeff_file = "./data/radiometric_calibration_matrix_HYPSO-1_full_v1.csv"

        # Smile ---------------------------------
        full_smile_coeff_file = "./data/spectral_calibration_matrix_HYPSO-1_full_v1.csv"

        # Destriping (not available for custom)
        full_destripig_coeff_file = None

        return {"radiometric": full_rad_coeff_file,
                "smile": full_smile_coeff_file,
                "destriping": full_destripig_coeff_file}

    elif info["capture_type"] == "nominal":
        csv_file_radiometric = "radiometric_calibration_matrix_HYPSO-1_nominal_v1.csv"
        csv_file_smile = "smile_correction_matrix_HYPSO-1_nominal_v1.csv"
        csv_file_destriping = "destriping_matrix_HYPSO-1_nominal_v1.csv"

    elif info["capture_type"] == "wide":
        csv_file_radiometric = "radiometric_calibration_matrix_HYPSO-1_wide_v1.csv"
        csv_file_smile = "smile_correction_matrix_HYPSO-1_wide_v1.csv"
        csv_file_destriping = "destriping_matrix_HYPSO-1_wide_v1.csv"

    rad_coeff_file = csv_file_radiometric
    smile_coeff_file = csv_file_smile
    destriping_coeff_file = csv_file_destriping

    coeff_dict = {"radiometric": os.path.join(os.path.dirname(__file__), 'data', rad_coeff_file),
                    "smile": os.path.join(os.path.dirname(__file__), 'data', smile_coeff_file),
                    "destriping": os.path.join(os.path.dirname(__file__), 'data', destriping_coeff_file)
                    }

    return coeff_dict




def get_calibrated_and_corrected_cube(info: dict, raw_cube: np.ndarray, calibration_coefficients_dict: dict):
    """ Calibrate cube.

    Includes:
    - Radiometric calibration
    - Smile correction
    - Destriping

    Assumes all coefficients has been adjusted to the frame size (cropped and
    binned), and that the data cube contains 12-bit values.
    """

    # Radiometric calibration
    # TODO: The factor by 10 is to fix a bug in which the coeff have a factor of 10
    cube_calibrated = calibrate_cube(info, 
                                     raw_cube, 
                                     calibration_coefficients_dict) / 10

    # Smile correction
    #cube_smile_corrected = smile_correct_cube(cube_calibrated, 
    #                                          calibration_coefficients_dict)

    # Destriping
    cube_calibrated = destriping_correct_cube(cube_calibrated, 
                                             calibration_coefficients_dict)

    return cube_calibrated





def crop_and_bin_matrix(matrix, x_start, x_stop, y_start, y_stop, bin_x=1, bin_y=1):
    """ Crops matrix to AOI. Bins matrix so that the average value in the bin_x
    number of pixels is stored.
    """
    # Crop to selected AOI
    width_binned = None
    new_matrix = matrix[y_start:y_stop, x_start:x_stop]
    height, width = new_matrix.shape

    # If bin is set to 0 or negative we assume this means no binning, aka bin=1
    if bin_x < 1:
        bin_x = 1
    if bin_y < 1:
        bin_y = 1

    # Bin spectral direction
    if bin_x != 1:
        width_binned = int(width / bin_x)
        matrix_cropped_and_binned = np.zeros((height, width_binned))
        for i in range(width_binned):
            this_pixel_sum = 0
            for j in range(bin_x):
                this_pixel_value = new_matrix[:, i * bin_x + j]
                this_pixel_sum += this_pixel_value
            average_pixel_value = this_pixel_sum / bin_x
            matrix_cropped_and_binned[:, i] = average_pixel_value
        new_matrix = matrix_cropped_and_binned

    # Bin spatial direction
    if bin_y != 1:
        height_binned = int(height / bin_y)
        matrix_binned_spatial = np.zeros((height_binned, width_binned))
        for i in range(height_binned):
            this_pixel_sum = 0
            for j in range(bin_y):
                this_pixel_value = new_matrix[i * bin_y + j, :]
                this_pixel_sum += this_pixel_value
            average_pixel_value = this_pixel_sum / bin_y
            matrix_binned_spatial[i, :] = average_pixel_value / bin_y
        new_matrix = matrix_binned_spatial

    return new_matrix


def get_coefficients_from_file(coeff_path: str) -> np.ndarray:
    coefficients = None
    try:
        # Processing should be Float 32
        coefficients = np.genfromtxt(
            coeff_path, delimiter=',', dtype="float64")
        # coefficients = readCsvFile(coeff_path)
    except BaseException:
        coefficients = None
        raise ValueError("Could not read coefficients file.")

    return coefficients


def get_coefficients_from_dict(coeff_dict: dict, info:dict) -> dict:
    coeffs = coeff_dict.copy()
    for k in coeff_dict:
        # Coefficients Custom (needs trimming)
        if "full" in str(coeff_dict[k]):
            bin_x = info["bin_factor"]
            full_coeff = get_coefficients_from_file(coeff_dict[k])
            coeffs[k] = crop_and_bin_matrix(
                full_coeff,
                info["x_start"],
                info["x_stop"],
                info["y_start"],
                info["y_stop"],
                bin_x)
        # Just read coefficients
        elif "nominal" in str(coeff_dict[k]) or "wide" in str(coeff_dict[k]):
            coeffs[k] = get_coefficients_from_file(coeff_dict[k])

        else:
            coeff_dict[k] = None

    return coeffs















def calibrate_cube(info_sat: dict, raw_cube: np.ndarray, correction_coefficients_dict: dict) -> np.ndarray:
    """Calibrate the raw data cube."""
    DEBUG = False

    if correction_coefficients_dict["radiometric"] is None:
        return raw_cube.copy()

    #print("Radiometric Correction Ongoing")

    background_value = info_sat['background_value']
    exp = info_sat['exp']
    image_height = info_sat['image_height']
    image_width = info_sat['image_width']

    # Radiometric calibration
    num_frames = info_sat["frame_count"]
    #cube_calibrated = np.zeros([num_frames, image_width, image_height]) # TODO swap image_width and height back to original order
    cube_calibrated = np.zeros([num_frames, image_height, image_width]) 

    if DEBUG:
        print("F:", num_frames, "H:", image_height, "W:", image_width)
        print("Radioshape: ",
              correction_coefficients_dict["radiometric"].shape)

    for i in range(num_frames):
        frame = raw_cube[i, :, :]
        # Radiometric Calibration
        frame_calibrated = apply_radiometric_calibration(frame, 
                                                         exp, 
                                                         background_value, 
                                                         correction_coefficients_dict["radiometric"])

        cube_calibrated[i, :, :] = frame_calibrated

    l1b_cube = cube_calibrated

    return l1b_cube


def apply_radiometric_calibration(
        frame,
        exp,
        background_value,
        radiometric_calibration_coefficients):
    ''' Assumes input is 12-bit values, and that the radiometric calibration
    coefficients are the same size as the input image.

    Note: radiometric calibration coefficients have original size (684,1080),
    matching the "normal" AOI of the HYPSO-1 data (with no binning).'''

    frame = frame - background_value
    frame_calibrated = frame * radiometric_calibration_coefficients / exp

    return frame_calibrated


def smile_correction_one_row(row, w, w_ref):
    ''' Use cubic spline interpolation to resample one row onto the correct
    wavelengths/bands from a reference wavelength/band array to correct for
    the smile effect.
    '''
    row_interpolated = interpolate.splrep(w, row)
    row_corrected = interpolate.splev(w_ref, row_interpolated)
    # Set values for wavelengths below 400 nm to zero
    for i in range(len(w_ref)):
        w = w_ref[i]
        if w < 400:
            row_corrected[i] = 0
        else:
            break
    return row_corrected


def smile_correction_one_frame(frame, spectral_band_matrix):
    ''' Run smile correction on each row in a frame, using the center row as 
    the reference wavelength/band for smile correction.
    '''
    image_height, image_width = frame.shape
    center_row_no = int(image_height / 2)
    w_ref = spectral_band_matrix[center_row_no]
    frame_smile_corrected = np.zeros([image_height, image_width])
    for i in range(image_height):  # For each row
        this_w = spectral_band_matrix[i]
        this_row = frame[i]
        # Correct row
        row_corrected = smile_correction_one_row(this_row, this_w, w_ref)
        frame_smile_corrected[i, :] = row_corrected
    return frame_smile_corrected


def smile_correct_cube(cube, correction_coefficients_dict: dict):
    ''' Run smile correction on each frame in a cube, using the center row in 
    the frame as the reference wavelength/band for smile correction.
    '''

    if correction_coefficients_dict["smile"] is None:
        return cube.copy()

    #print("Smile Correction Ongoing")

    spectral_band_matrix = correction_coefficients_dict["smile"]
    num_frames, image_height, image_width = cube.shape
    cube_smile_corrected = np.zeros([num_frames, image_height, image_width])
    for i in range(num_frames):
        this_frame = cube[i, :, :]
        frame_smile_corrected = smile_correction_one_frame(
            this_frame, spectral_band_matrix)
        cube_smile_corrected[i, :, :] = frame_smile_corrected
    return cube_smile_corrected


def destriping_correct_cube(cube, correction_coefficients_dict):
    ''' Apply destriping correction matrix. '''

    if correction_coefficients_dict["destriping"] is None:
        return cube.copy()

    #print("Destriping Correction Ongoing")

    destriping_correction_matrix = correction_coefficients_dict["destriping"]
    # print(destriping_correction_matrix.shape)
    # print(cube.shape)
    # cube_delined = copy.deepcopy(cube)
    # cube_delined[:, 1:] -= destriping_correction_matrix[:-1]
    cube_delined = cube * destriping_correction_matrix
    return cube_delined






def get_spectral_coefficients_path():
    rad_coeff_file = "spectral_bands_HYPSO-1_v1.csv"
    return os.path.join(os.path.dirname(__file__), 'data', rad_coeff_file)