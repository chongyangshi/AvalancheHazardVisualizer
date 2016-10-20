import os
import json

def load_imagery_config():
    ''' Load data from imagery configration file. '''
    
    scriptDirectory = os.path.abspath(os.path.join(__file__, os.pardir))
    configFile = scriptDirectory + "/overlays.json"

    if not os.path.isfile(configFile):
        raise ValueError("The imagery configuration file overlays.json does not exist!")

    with open(configFile) as overlaysFile:
        overlaysData = json.load(overlaysFile)

    return overlaysData


def get_facing_from_aspect(aspect):
    ''' Convert an aspect value (0-360.0) to a direction, clockwise by ArcGIS definition. '''

    x = float(aspect)

    if (x > 360.0) or (x < 0): # Invalid
        return ""
    
    result = ""
    if (x > 337.5) or (x <= 22.5): result = "N"
    elif (x > 22.5) and (x <= 67.5): result = "NE"
    elif (x > 67.5) and (x <= 112.5): result = "E"
    elif (x > 112.5) and (x <= 157.5): result = "SE"
    elif (x > 157.5) and (x <= 202.5): result = "S"
    elif (x > 202.5) and (x <= 247.5): result = "SW"
    elif (x > 247.5) and (x <= 292.5): result = "W"
    elif (x > 292.5) and (x <= 337.5): result = "NW"

    return result


def match_altitude_to_forecast(forecast, altitude):
    ''' Operate on the one record of SAIS forecast to see which altitude range
        does the altitude fit in. '''
    
    lower_boundary = int(forecast[4])
    middle_boundary = int(forecast[5])
    upper_boundary = int(forecast[6])
    lower_primary_colour = int(forecast[7])
    lower_secondary_colour = int(forecast[8])
    upper_primary_colour = int(forecast[9])
    upper_secondary_colour = int(forecast[10])

    if (altitude < lower_boundary):
        #Below snow line, no altitude-related risk.
        return 0
    elif (altitude >= lower_boundary) and (altitude < middle_boundary):
        return max(lower_primary_colour, lower_secondary_colour)
    elif (altitude >= middle_boundary) and (altitude <= upper_boundary):
        return max(upper_primary_colour, upper_secondary_colour)
    else:
        #Above snow line, no altitude-related risk.
        return 0