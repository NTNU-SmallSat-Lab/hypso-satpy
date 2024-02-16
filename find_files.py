# Run 'source ~/.profile'
import satpy
from satpy import Scene, find_files_and_readers
import sys
import datetime
from glob import glob

sys.path.insert(0,'/home/cameron/Projects/')

# Usage of find_files_and_reader: https://satpy.readthedocs.io/en/stable/api/satpy.readers.html#satpy.readers.find_files_and_readers

# Find files with dates after start_time
filenames = find_files_and_readers(base_dir="/home/cameron/Dokumenter/Data/erie", 
                                 reader='hypso1_l1a_nc', 
                                 start_time=datetime.datetime(2023, 3, 1, 15, 59))

# Find files with dates between start_time and end_time (inclusive)
filenames = find_files_and_readers(base_dir="/home/cameron/Dokumenter/Data/erie", 
                                 reader='hypso1_l1a_nc', 
                                 start_time=datetime.datetime(2023, 3, 1, 15, 0),
                                 end_time=datetime.datetime(2023, 3, 1, 16, 0))

# Find files after start_time, filtering for target
filenames = find_files_and_readers(base_dir="/home/cameron/Dokumenter/Data/erie", 
                                 reader='hypso1_l1a_nc', 
                                 start_time=datetime.datetime(2023, 3, 1, 15, 0),
                                 filter_parameters={'target': 'erie'})

# Single capture file list (includes both .nc and GCP .points files)
filenames = ['/home/cameron/Dokumenter/Data/combined/lakeerie_2023-05-17_1553Z-l1a.nc',
          '/home/cameron/Dokumenter/Data/combined/lakeerie_2023-05-17_1553Z-bin3.points']

# Find files using glob 
filenames=glob('/home/cameron/Dokumenter/Data/svalbardeidembukta/svalbardeidembukta_2023-03-25_*')