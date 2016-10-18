import sys
import pymongo
from convertbng.util import convert_lonlat

from mongodb_manager import MongoDBManager


class TerrainReader:
    ''' Class for the terrain reader, which reads in a aspect raster
         (converted by GDAL from a terrain raster) in ASC format and
         British National Grid spatial system, converts it into
         WGS84 coordinates, and store it in the aspect database. '''
    
    def __init__(self, raster_file):

        #Set up database manager.
        self.__database = MongoDBManager()

        # Attempt to open raster file.
        try:
            self.__raster_file = open(raster_file, 'r')
        except:
            print("Error: error opening raster file " + raster_file + ".")
            raise

        # Check raster file to be in the correct format.
        # Read meta information in order.
        try:
            self.__raster_ncols = int(self.__raster_file.readline().split(" ")[-1])
            self.__raster_nrows = int(self.__raster_file.readline().split(" ")[-1])
            self.__raster_xllcorner = float(self.__raster_file.readline().split(" ")[-1])
            self.__raster_yllcorner = float(self.__raster_file.readline().split(" ")[-1])
            self.__raster_cellsize = float(self.__raster_file.readline().split(" ")[-1])
        except ValueError:
            print("Error: the raster file is not in a valid ASC (llcorner-based) form.")
            raise

        # Initialise coordinate tracking, we only need the current northing and latitude.
        self._current_bng_easting = self.__raster_xllcorner # National Grid Easting
        self._current_bng_northing = self.__raster_yllcorner # National Grid Northing
        #self._current_wgs_longitude = convert_lonlat([self._current_bng_easting], [self._current_bng_northing])[0][0] # Coordinate Longitude
        #self._current_wgs_latitude = convert_lonlat([self._current_bng_easting], [self._current_bng_northing])[1][0] # Coordinate Latitude
        self._current_line_count = 0
    
    def read_all_aspects(self):
        ''' Read all aspect values, line-by-line from the raster. 
            Each line has the same northing/latitude, but incrementing 
            longitude. '''

        end_of_file = False
        
        while not end_of_file:
            
            file_line = self.__raster_file.readline()
            
            # EOF check.
            if file_line == "":
                end_of_file = True
                continue
            
            self._current_line_count += 1
            print("Reading Data Line: " + str(self._current_line_count))
            
            aspects = file_line.split()
            aspects_length = len(aspects)
            if aspects_length != self.__raster_ncols: # Could be missing things, we don't give up but log and warn about the error.
                print("  Warning: Length of Data Line " + str(self._current_line_count) + " does not match file's number of columns.")
            converted_coordinates = convert_lonlat([self._current_bng_easting + self.__raster_cellsize * i for i in range(0, aspects_length)], [self._current_bng_northing] * aspects_length)

            # Save data in database.
            self.__database.add_aspects((converted_coordinates[1], converted_coordinates[0], aspects)) # Latitude first

            # Increment northing for next line.
            self._current_bng_northing = self._current_bng_northing + self.__raster_cellsize
            self._current_bng_easting = self.__raster_xllcorner
            
        if self._current_line_count != self.__raster_nrows:
            print("  Warning: Number of Data Lines does not match file's number of rows, extrapolated.")

    def close_and_exit(self):
        ''' Close the raster file and exit. '''

        self.__raster_file.close()
        sys.exit(0)

if __name__ == "__main__":
    
    if len(sys.argv) != 2:
        print("Usage: python terrain_reader.py ASPECT_RASTER.ASC")
    else:
        reader = TerrainReader(sys.argv[1])
        reader.read_all_aspects()
        reader.close_and_exit()

        