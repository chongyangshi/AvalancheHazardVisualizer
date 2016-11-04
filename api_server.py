from __future__ import division
import os
import sys
import StringIO
from time import gmtime, strftime
from flask import Flask, send_file, abort
from PIL import Image

import utils
import geocoordinate_to_location
from SAISCrawler.script import db_manager as forecast_db
from SAISCrawler.script import utils as forecast_utils
from GeoData import raster_reader, raster_reader_bng

API_LOG = os.path.abspath(os.path.join(__file__, os.pardir)) + "/api.log"
LOG_REQUESTS = False
SPATIAL_READER = raster_reader_bng

# Initialise forecast database and raster reader.
forecast_dbm = forecast_db.CrawlerDB(forecast_utils.get_project_full_path() + forecast_utils.read_config('dbFile'))
raster = SPATIAL_READER.RasterReader()

# Main API app.
app = Flask(__name__)

@app.route('/imagery/api/v1.0/avalanche_risks/<string:longitude_initial>/<string:latitude_initial>/<string:longitude_final>/<string:latitude_final>', methods=['GET'])
def get_risk(longitude_initial, latitude_initial, longitude_final, latitude_final):
    ''' Return a color-code image containing the risk of the requested coordinate and altitude area. '''

    not_found_message = ""
 
    try:
        
        upper_left_corner = map(float, [longitude_initial, latitude_initial])
        lower_right_corner = map(float, [longitude_final, latitude_final])
        center_coordinates = [sum(e)/len(e) for e in zip(*[upper_left_corner, lower_right_corner])]
        
        # Impossible geodetic coordinates.
        not_found_message = "Invalid input data."
        if (upper_left_corner[0] < -180.0) or (upper_left_corner[0] > 180.0):
            abort(400)
        if (upper_left_corner[1] < -90.0) or (upper_left_corner[1] > 90.0):
            abort(400)
        if (lower_right_corner[0] < -180.0) or (lower_right_corner[0] > 180.0):
            abort(400)
        if (lower_right_corner[1] < -90.0) or (lower_right_corner[1] > 90.0):
            abort(400)
        not_found_message = ""

        # Preclude requests that are too large.
        if (abs(lower_right_corner[0] - upper_left_corner[0]) > 0.03) or (abs(lower_right_corner[1] - upper_left_corner[1]) > 0.02):
            not_found_message = "Request too large."
            abort(404)
        
        # Request heights and aspects from the raster.
        heights_matrix = raster.read_heights(upper_left_corner[0], upper_left_corner[1], lower_right_corner[0], lower_right_corner[1])
        aspects_matrix = raster.read_aspects(upper_left_corner[0], upper_left_corner[1], lower_right_corner[0], lower_right_corner[1])
        # If no data returned.
        if (heights_matrix is False) or (aspects_matrix is False): 
            not_found_message = "Heights or aspects out of range."
            abort(400)
        if (len(heights_matrix) <= 0) or (len(aspects_matrix) <= 0): 
            not_found_message = "Heights or aspects too large to request."
            abort(404)
        
        matrix_height = len(heights_matrix)
        matrix_width = len(heights_matrix[0])
        
        # Request forecast from SAIS.
        location_name = geocoordinate_to_location.get_location_name(center_coordinates[0], center_coordinates[1]).strip()
        if location_name == "":
            not_found_message = "Location name unavailable."
            abort(404)
            
        # Just in case multiple location ids are returned, take first one.
        location_id_list = forecast_dbm.select_location_by_name(location_name)
        if not location_id_list:
            not_found_message = "Location list empty."
            abort(404)
        location_id = int(location_id_list[0][0])
        
        # Look up the most recent forecasts for the location.
        location_forecasts = forecast_dbm.lookup_newest_forecasts_by_location_id(location_id)
        if location_forecasts == None:
            not_found_message = "Forecast for location not found."
            abort(400)
        location_forecast_list = list(location_forecasts)
        
        # Return forecast colours.
        location_colours = []
        for i in range(0, len(heights_matrix)):
            colour_row = []
            for j in range(0, len(heights_matrix[i])):
                colour_row.append(utils.match_aspect_altitude_to_forecast(location_forecast_list, aspects_matrix[i][j], heights_matrix[i][j]))
            location_colours.append(colour_row)
        
        # Build the image according to colours.
        # Create an empty image with one pixel for each point.
        return_image = Image.new("RGBA", (matrix_width, matrix_height), None)
        return_image_pixels = return_image.load()
        for i in range(return_image.size[0]):   
            for j in range(return_image.size[1]):
                return_image_pixels[i,j] = utils.risk_code_to_colour(location_colours[j][i]) # 2D array is in inversed order of axis.
        image_object = StringIO.StringIO() 
        return_image.save(image_object, format="png") 
        image_object.seek(0)

        return send_file(image_object, mimetype='image/png')
       
    except Exception as e:
        
        # Always return a result and not get held up by exception.
        if (os.path.isfile(API_LOG)) and LOG_REQUESTS:
            with open(API_LOG, "a") as log_file:
                log_file.write(strftime("%Y-%m-%d %H:%M:%S", gmtime()) + ": error serving client, no-data image returned. Error: " + str(e) + ". Message: " + not_found_message + "\n")
        
        # Return an empty image.
        return_image = Image.new("RGBA", (1, 1), None)
        image_object = StringIO.StringIO() 
        return_image.save(image_object, format="png")
        image_object.seek(0)
        
        return send_file(image_object, mimetype='image/png')


@app.route('/imagery/api/v1.0/terrain_aspects/<string:longitude_initial>/<string:latitude_initial>/<string:longitude_final>/<string:latitude_final>', methods=['GET'])
def get_aspect(longitude_initial, latitude_initial, longitude_final, latitude_final):
    ''' Return a grayscale map of terrain aspects, with 0-360 degrees mapped to 0-255 color levels. '''

    not_found_message = ""
 
    try:
        
        upper_left_corner = map(float, [longitude_initial, latitude_initial])
        lower_right_corner = map(float, [longitude_final, latitude_final])
        center_coordinates = [sum(e)/len(e) for e in zip(*[upper_left_corner, lower_right_corner])]
        
        # Impossible geodetic coordinates.
        not_found_message = "Invalid input data."
        if (upper_left_corner[0] < -180.0) or (upper_left_corner[0] > 180.0):
            abort(400)
        if (upper_left_corner[1] < -90.0) or (upper_left_corner[1] > 90.0):
            abort(400)
        if (lower_right_corner[0] < -180.0) or (lower_right_corner[0] > 180.0):
            abort(400)
        if (lower_right_corner[1] < -90.0) or (lower_right_corner[1] > 90.0):
            abort(400)
        not_found_message = ""

        # Preclude requests that are too large.
        if (abs(lower_right_corner[0] - upper_left_corner[0]) > 0.03) or (abs(lower_right_corner[1] - upper_left_corner[1]) > 0.02):
            not_found_message = "Request too large."
            abort(404)
        
        # Request aspects from the raster.
        aspects_matrix = raster.read_aspects(upper_left_corner[0], upper_left_corner[1], lower_right_corner[0], lower_right_corner[1])
        # If no data returned.
        if (aspects_matrix is False) or (len(aspects_matrix) <= 0): 
            not_found_message = "Heights or aspects out of range or too large to request."
            abort(400)

        matrix_height = len(aspects_matrix)
        matrix_width = len(aspects_matrix[0])
        
        # Build the image according to colours.
        # Create an empty image with one pixel for each point.
        return_image = Image.new("RGBA", (matrix_width, matrix_height), None)
        return_image_pixels = return_image.load()
        for i in range(return_image.size[0]):   
            for j in range(return_image.size[1]):
                return_image_pixels[i,j] = utils.aspect_to_grayscale(aspects_matrix[j][i]) # 2D array is in inversed order of axis.
        image_object = StringIO.StringIO() 
        return_image.save(image_object, format="png") 
        image_object.seek(0)

        return send_file(image_object, mimetype='image/png')
       
    except Exception as e:
        
        # Always return a result and not get held up by exception.
        if (os.path.isfile(API_LOG)) and LOG_REQUESTS:
            with open(API_LOG, "a") as log_file:
                log_file.write(strftime("%Y-%m-%d %H:%M:%S", gmtime()) + ": error serving client, no-data image returned. Error: " + str(e) + ". Message: " + not_found_message + "\n")
        
        # Return an empty image.
        return_image = Image.new("RGBA", (1, 1), None)
        image_object = StringIO.StringIO() 
        return_image.save(image_object, format="png")
        image_object.seek(0)
        
        return send_file(image_object, mimetype='image/png')

if __name__ == '__main__':
    app.run(debug=True)
