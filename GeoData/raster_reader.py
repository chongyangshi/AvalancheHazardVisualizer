from __future__ import division, print_function

import struct
import sys
from osgeo import gdal

DEFAULT_RASTER = "/mnt/Shared/OS5/Full/WGS.tif"

class RasterReader:
    ''' Interface for GDAL access of external
        raster files, in order to read raster without 
        loading them in full in memory. '''

    def __init__(self, raster_file=DEFAULT_RASTER):
        
        self.__raster_file = raster_file
        self._raster = gdal.Open(self.__raster_file)

        if (type(self._raster) is not gdal.Dataset):
            self.log_error("Error, raster data from " + self.__raster_file + " is not valid.")
            sys.exit()
        
        # Try to read the upper left corners to make sure that the rasters are not empty.
        test_read = self._raster.ReadRaster(0,0,1,1,buf_type=gdal.GDT_Float32)
        if (not self.validate_read(test_read)):
            self.log_error("Error, the " + self.__raster_file + " raster is empty, cannot use that.")
            sys.exit()

        # Compute the corners of the raster.
        self.__corners = {}
        for raster_map in [self._raster]:

            # Initialise.
            object_id = id(raster_map) 
            self.__corners[object_id] = {}

            # Obtain corner information from raster.
            corner_info = raster_map.GetGeoTransform()
            self.__corners[object_id]['corner_info'] = corner_info

            # Work out the corner coordinates based on raster size and resolution.
            # See GDAL manual for more details on calculations.
            self.__corners[object_id]['upper_left_corner'] = [corner_info[0], corner_info[3]]
            self.__corners[object_id]['upper_right_corner'] = [corner_info[0] + raster_map.RasterXSize * corner_info[1], corner_info[3]]
            self.__corners[object_id]['lower_left_corner'] = [corner_info[0], corner_info[3] + raster_map.RasterYSize * corner_info[5]]
            self.__corners[object_id]['lower_right_corner'] = [corner_info[0] + raster_map.RasterXSize * corner_info[1], corner_info[3] + raster_map.RasterYSize * corner_info[5]]
            self.__corners[object_id]['center'] = [sum(e)/len(e) for e in zip(*[self.__corners[object_id]['upper_left_corner'], self.__corners[object_id]['lower_right_corner']])]


    def read_point(self, coord_x, coord_y):
        ''' Get data of a single point from the raster,
            return False if invalid coordinate read.'''
        
        if not self.check_access_window(id(self._raster), coord_x, coord_y):
            return False

        index_x, index_y = self.coordinate_to_index(id(self._raster), coord_x, coord_y)
        data = self._raster.ReadRaster(index_x, index_y, 1, 1, buf_type=gdal.GDT_Float32)
        
        if (self.validate_read(data)):
            return struct.unpack('f', data)[0]
        else:
            return False

    
    def read_points(self, initial_x, initial_y, end_x, end_y):
        ''' Read an area of the raster, with top left corner coordinates
            (initial_x, initial_y) and bottom right corner coordinates
            (end_x, end_y) for values. Return False if request invalid. '''
        
        if not self.check_access_window(id(self._raster), initial_x, initial_y):
            return False
        
        if not self.check_access_window(id(self._raster), end_x, end_y):
            return False
        
        # Calculate the indices for the two corners, and validate them.
        x1, y1 = self.coordinate_to_index(id(self._raster), initial_x, initial_y)
        xn, yn = self.coordinate_to_index(id(self._raster), end_x, end_y)
        
        if (not yn >= y1) or (not xn >= x1):
            return False
        
        # Calculate the number of data points to fetch.
        Nx = xn - x1 + 1
        Ny = yn - y1 + 1
        
        # If request too large, return empty.
        if (Nx > 9999) or (Ny > 9999):
            return []
        
        data = self._raster.ReadAsArray(x1, y1, Nx, Ny)
        
        return data # Two-dimensional array, rows of data.


    def coordinate_to_index(self, raster_id, coord_x, coord_y):
        ''' Convert WGS84 coordinates into raster indices. '''
        
        transform_info = self.__corners[raster_id]['corner_info']
        x = int(round((coord_x - transform_info[0]) / transform_info[1]))
        y = int(round((coord_y - transform_info[3]) / transform_info[5]))

        return x, y

    
    def check_access_window(self, raster_id, coord_x, coord_y):
        ''' Check whether a coordinate is within the acceptable
            access window, if not, return False; else, return 
            True. '''
        
        try:
            # If coordinate outside boundary, return False.
            # Note that latitude is larger for smaller y's, and longitude is large for larger x's.
            if (coord_x < self.__corners[raster_id]['upper_left_corner'][0]) or (coord_x > self.__corners[raster_id]['upper_right_corner'][0]):
                return False
            if (coord_y > self.__corners[raster_id]['upper_left_corner'][1]) or (coord_y < self.__corners[raster_id]['lower_left_corner'][1]):
                return False
            
            return True

        except KeyError:
            return False # The raster_id may not be valid.
    
    
    def get_limits(self, raster_id):
        ''' Return the limits ([x1, y1], [xn, yn]) for the given
            raster, in coordinates. '''

        return ((self.__corners[raster_id]['upper_left_corner'],
        self.__corners[raster_id]['lower_right_corner']))


    @classmethod
    def validate_read(self, data):
        ''' Check if a returned data (type str) is valid, as GDAL does 
            not implement Python exceptions.'''
        if type(data) is not str:
            return False
        else:
            return True


    @classmethod
    def log_error(self, error_message):
        ''' Utilities function for logging error messages. '''
        caller_name = str(sys._getframe(1).f_code.co_name)

        try:
            # If we cannot write to the directory or file, not making a fuss.
            log_file = open('raster.log', 'w+')
            log_file.write(caller_name + ": " + str(error_message) + "\n")
        except:
            pass

        print(caller_name + ": " + error_message)
    

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python raster_reader.py RASTER_FILE")
        print("Loading default raster...")
        reader = RasterReader(DEFAULT_RASTER)
    else:
        reader = RasterReader(sys.argv[1])
        # Simple tests.
    print(reader.read_point(-4.0385629, 57.1513943))
    print(reader.read_points(-4.0385629, 57.1513943, -3.9985629, 57.1213943))
