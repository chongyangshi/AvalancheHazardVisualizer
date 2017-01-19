from __future__ import division, print_function

import struct
import sys
from osgeo import gdal

HEIGHT_MAP_RASTER = "/mnt/Shared/OS5/Full/WGS.tif"
ASPECT_MAP_RASTER = "/mnt/Shared/OS5/Full/WGSAspects.tif"
CONTOUR_MAP_RASTER = "/mnt/Shared/OS5/Full/WGSContours.tif"

class RasterReader:
    ''' Interface for GDAL access of height map and aspect 
        raster files, in order to read raster without 
        loading them in full in memory. '''

    def __init__(self, height_map=HEIGHT_MAP_RASTER, aspect_map=ASPECT_MAP_RASTER, contour_map=COUNTER_MAP_RASTER):
        
        self.__height_map_raster = height_map
        self.__aspect_map_raster = aspect_map
        self.__contour_map_raster = contour_map

        # Test to see if both rasters can be read.
        self._height_map = gdal.Open(self.__height_map_raster)
        self._aspect_map = gdal.Open(self.__aspect_map_raster)
        self._contour_map = gdal.Open(self.__contour_map_raster)

        if (type(self._height_map) is not gdal.Dataset) or (type(self._aspect_map) is not gdal.Dataset) or (type(self._contour_map) is not gdal.Dataset):
            self.log_error("Error, either height map or aspect map raster is not valid.")
            sys.exit()
        
        # Try to read the upper left corners to make sure that the rasters are not empty.
        test_read_height = self._height_map.ReadRaster(0,0,1,1,buf_type=gdal.GDT_Float32)
        test_read_aspect = self._aspect_map.ReadRaster(0,0,1,1,buf_type=gdal.GDT_Float32)
        test_read_contour = self._contour_map.ReadRaster(0,0,1,1,buf_type=gdal.GDT_Float32)
        if (not self.validate_read(test_read_height)) or (not self.validate_read(test_read_aspect)) or (not self.validate_read(test_read_contour)):
            self.log_error("Error, either height map or aspect map raster is empty, cannot use that.")
            sys.exit()

        # Compute the corners of the raster.
        self.__corners = {}
        for raster_map in [self._height_map, self._aspect_map, self._contour_map]:

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
        
        # Warn the user if corners do not match.
        if not (self.__corners[id(self._height_map)] == self.__corners[id(self._aspect_map)] == self.__corners[id(self._aspect_map)]):
            self.log_error("Warning, the height map raster does not have identical corners to the aspect map's, this may or may not be a problem.")


    def read_height(self, coord_x, coord_y):
        ''' Get a single height from the height map raster, 
            return False if invalid coordinate read.'''
        
        if not self.check_access_window(id(self._height_map), coord_x, coord_y):
            return False

        index_x, index_y = self.coordinate_to_index(id(self._height_map), coord_x, coord_y)
        height = self._height_map.ReadRaster(index_x, index_y, 1, 1, buf_type=gdal.GDT_Float32)
        
        if (self.validate_read(height)):
            return struct.unpack('f', height)[0]
        else:
            return False


    def read_aspect(self, coord_x, coord_y):
        ''' Get a single aspect from the height map raster, 
            return False if invalid coordinate read.'''
        
        if not self.check_access_window(id(self._aspect_map), coord_x, coord_y):
            return False

        index_x, index_y = self.coordinate_to_index(id(self._aspect_map), coord_x, coord_y)
        aspect = self._aspect_map.ReadRaster(index_x, index_y, 1, 1, buf_type=gdal.GDT_Float32)
        
        if (self.validate_read(aspect)):
            return struct.unpack('f', aspect)[0]
        else:
            return False

    
    def read_heights(self, initial_x, initial_y, end_x, end_y):
        ''' Read an area of the raster, with top left corner coordinates
            (initial_x, initial_y) and bottom right corner coordinates
            (end_x, end_y) for heights. Return False if request invalid. '''
        
        if not self.check_access_window(id(self._height_map), initial_x, initial_y):
            return False
        
        if not self.check_access_window(id(self._height_map), end_x, end_y):
            return False
        
        # Calculate the indices for the two corners, and validate them.
        x1, y1 = self.coordinate_to_index(id(self._height_map), initial_x, initial_y)
        xn, yn = self.coordinate_to_index(id(self._height_map), end_x, end_y)
        
        if (not yn >= y1) or (not xn >= x1):
            return False
        
        # Calculate the number of data points to fetch.
        Nx = xn - x1 + 1
        Ny = yn - y1 + 1
        
        # If request too large, return empty.
        if (Nx > 9999) or (Ny > 9999):
            return []
        
        heights = self._height_map.ReadAsArray(x1, y1, Nx, Ny)
        
        return heights # Two-dimensional array, rows of data.

    
    def read_aspects(self, initial_x, initial_y, end_x, end_y):
        ''' Read an area of the raster, with top left corner coordinates
            (initial_x, initial_y) and bottom right corner coordinates
            (end_x, end_y) for aspects. Return False if request invalid. '''
        
        if not self.check_access_window(id(self._aspect_map), initial_x, initial_y):
            return False
        
        if not self.check_access_window(id(self._aspect_map), end_x, end_y):
            return False

        # Calculate the indices for the two corners, and validate them.
        x1, y1 = self.coordinate_to_index(id(self._aspect_map), initial_x, initial_y)
        xn, yn = self.coordinate_to_index(id(self._aspect_map), end_x, end_y)

        if (not yn >= y1) or (not xn >= x1):
            return False
        
        # Calculate the number of data points to fetch.
        Nx = xn - x1 + 1
        Ny = yn - y1 + 1

        # If request too large, return empty.
        if (Nx > 9999) or (Ny > 9999):
            return []
        
        aspects = self._aspect_map.ReadAsArray(x1, y1, Nx, Ny)
        
        return aspects # Two-dimensional array, rows of data.


    def read_contours(self, initial_x, initial_y, end_x, end_y):
        ''' Read an area of the raster, with top left corner coordinates
            (initial_x, initial_y) and bottom right corner coordinates
            (end_x, end_y) for contours. Return False if request invalid. '''
        
        if not self.check_access_window(id(self._contour_map), initial_x, initial_y):
            return False
        
        if not self.check_access_window(id(self._contour_map), end_x, end_y):
            return False

        # Calculate the indices for the two corners, and validate them.
        x1, y1 = self.coordinate_to_index(id(self._contour_map), initial_x, initial_y)
        xn, yn = self.coordinate_to_index(id(self._contour_map), end_x, end_y)

        if (not yn >= y1) or (not xn >= x1):
            return False
        
        # Calculate the number of data points to fetch.
        Nx = xn - x1 + 1
        Ny = yn - y1 + 1

        # If request too large, return empty.
        if (Nx > 9999) or (Ny > 9999):
            return []
        
        contours = self._contour_map.ReadAsArray(x1, y1, Nx, Ny)
        
        return contours # Two-dimensional array, rows of data.


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
            raster ('heights' or 'aspects'), in coordinates. '''

        return ((self.__corners[raster_id]['upper_left_corner'],\
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
    if 2 < len(sys.argv) < 4:
        print("Usage: python raster_reader.py {{HEIGHT_MAP_RASTER} {ASPECT_MAP_RASTER} {CONTOUR_MAP_RASTER}}") 
    elif len(sys.argv) == 4:
        reader = RasterReader(height_map=sys.argv[1], aspect_map=sys.argv[2], contour_map=sys.argv[3])
    else:
        reader = RasterReader()
    # Simple tests.
    print(reader.read_height(-4.0385629, 57.1513943))
    print(reader.read_aspect(-4.0385629, 57.1513943))
    print(reader.read_heights(-4.0385629, 57.1513943, -3.9985629, 57.1213943))
    print(reader.read_aspects(-4.0385629, 57.1513943, -3.9985629, 57.1213943))
    print(reader.read_contours(-4.0385629, 57.1513943, -3.9985629, 57.1213943))
