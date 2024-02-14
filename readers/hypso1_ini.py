#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""HYPSO-1 File Readers """

from satpy.readers.file_handlers import BaseFileHandler
import os


class HYPSO1INIFileHandler(BaseFileHandler):
    """HYPSO-1 .ini files."""

    def __init__(self, filename, filename_info, filetype_info, *req_fh, **fh_kwargs):
        super().__init__(filename, filename_info, filetype_info)

        self.filename_info = filename_info
        self.platform_name = 'hypso1'
        self.sensor = "hsi"

        filename = os.path.join(filename, 'capture_config.ini')

        self.ini_capture_config = {}
        with open(filename, "r") as file:
            for line in file:
                key, value = line.strip().split(' = ')
                key = key.strip()
                if key == 'flags':
                    # If the key is 'flags', interpret the value as hexadecimal
                    value = int(value, 16)
                else:
                    # For other keys, try to convert the value to the appropriate type
                    try:
                        value = int(value)
                    except ValueError:
                        try:
                            value = float(value)
                        except ValueError:
                            pass  # Keep the value as a string if conversion fails

                self.ini_capture_config[key] = value