import os
import sys
from time import gmtime, strftime
from flask import Flask, send_file, abort

import utils
import geocoordinate_to_location
from SAISCrawler.script import db_manager as forecast_db
from SAISCrawler.script import utils as forecast_utils
from TerrainDB import mongodb_manager as terrain_db

scriptDirectory = os.path.abspath(os.path.join(__file__, os.pardir))
API_LOG = os.path.abspath(os.path.join(__file__, os.pardir)) + "/api.log"
LOG_REQUESTS = False

# Load imagery configuration json.
print("api_server: Server is loading overlay images...")
overlaysData = utils.load_imagery_config()

# Load overlay images.
try:
    
    levels = {}
    data = overlaysData["avalanche_risk"]
    for overlay in data:
        level_code = int(data[overlay]["level_code"])
        levels[level_code] = scriptDirectory + "/Overlays/" + data[overlay]["level_image"]
    
    # Check that we have all levels from 0 to 5, and all files exist.
    levels_complete = False if False in [i in levels for i in range(-1,5)] else True
    levels_all_exist = False if False in [os.path.isfile(levels[i]) for i in range(-1,5)] else True
    
    if (not levels_complete) or (not levels_all_exist):
        print("api_server: error reading overlays.json, which may be incomplete.")
        sys.exit(1)

except ValueError:
    print("api_server: error reading overlays.json.")

# Main API app.
app = Flask(__name__)

@app.route('/imagery/api/v1.0/avalanche_risks/<string:altitude>/<string:longitude>/<string:latitude>', methods=['GET'])
def get_risk(altitude, longitude, latitude):
    ''' Return a color-code-filled image containing the risk of the requested coordinate and altitude. '''
    
    # Initialise databases, not done earlier due to pymongo's connect after fork requirement.
    forecast_dbm = forecast_db.CrawlerDB(forecast_utils.get_project_full_path() + forecast_utils.read_config('dbFile'))
    terrain_dbm = terrain_db.MongoDBManager()

    not_found_message = ""
 
    try:
        
        altitude_parsed = int(round(float(altitude)))

        # Impossible altitudes.
        if (altitude_parsed < 0) or (altitude_parsed > 10000):
            return send_file(levels[-1], mimetype='image/png')
        
        longitude_parsed = float(longitude)
        latitude_parsed = float(latitude)
        
        # Impossible geodetic coordinates.
        if (longitude_parsed < -180.0) or (longitude_parsed > 180.0):
            abort(400)
        if (latitude_parsed < -90.0) or (latitude_parsed > 90.0):
            abort(400)
        
        # Request aspect from terrain database.
        tile_aspect_lookup = terrain_dbm.get_nearest_aspect(latitude_parsed, longitude_parsed)
        if not tile_aspect_lookup: # No data returned
            not_found_message = "Nearest aspect unavailable."
            abort(404)
        tile_aspect = tile_aspect_lookup["aspect"]
        
        # Request forecast from SAIS.
        location_name = geocoordinate_to_location.get_location_name(latitude_parsed, longitude_parsed).strip()
        if location_name == "":
            not_found_message = "Location name unavailable."
            abort(404)
            
        # Just in case multiple location ids are returned, take first one.
        location_id_list = forecast_dbm.select_location_by_name(location_name)
        if not location_id_list:
            not_found_message = "Location list empty."
            abort(404)
        location_id = int(location_id_list[0][0])
        location_forecast = forecast_dbm.lookup_newest_forecast_by_location_id(location_id, utils.get_facing_from_aspect(tile_aspect))
        if location_forecast == None:
            abort(400)
        
        # Return forecast colour.
        location_colour = utils.match_altitude_to_forecast(location_forecast, altitude_parsed)

        # Log successful request if this is the case.
        if (os.path.isfile(API_LOG)) and LOG_REQUESTS:
            with open(API_LOG, "a") as log_file:
                log_file.write(strftime("%Y-%m-%d %H:%M:%S", gmtime()) + ": Forecast found: " + str(location_forecast) + ", final colour: " + str(location_colour)+ ", altitude: " + str(altitude_parsed) + ".\n")
        
        return send_file(levels[location_colour], mimetype='image/png')
       
    except Exception as e:
        
        # Always return a result and not get held up by exception.
        if (os.path.isfile(API_LOG)) and LOG_REQUESTS:
            with open(API_LOG, "a") as log_file:
                log_file.write(strftime("%Y-%m-%d %H:%M:%S", gmtime()) + ": error serving client, no-data image returned. Error: " + str(e) + ". Message: " + not_found_message + "\n")

        return send_file(levels[-1], mimetype='image/png')

if __name__ == '__main__':
    app.run(debug=True)
