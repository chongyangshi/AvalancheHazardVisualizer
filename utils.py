from __future__ import division

import os
import json
from collections import OrderedDict
from math import copysign

# Conversion table for aspect 0-360 degrees to RGB values, represented by linear changes in six segments.
CHANNEL_RANGE = 255
CHANNEL_COLOURINGS = {
    "R" : [(CHANNEL_RANGE, CHANNEL_RANGE), (CHANNEL_RANGE, 0), (0, 0), (0, 0), (0, CHANNEL_RANGE), (CHANNEL_RANGE, CHANNEL_RANGE)],
    "G" : [(0, CHANNEL_RANGE), (CHANNEL_RANGE, CHANNEL_RANGE), (CHANNEL_RANGE, CHANNEL_RANGE), (CHANNEL_RANGE, 0), (0, 0), (0, 0)],
    "B" : [(0, 0), (0, 0), (0, CHANNEL_RANGE), (CHANNEL_RANGE, CHANNEL_RANGE), (CHANNEL_RANGE, CHANNEL_RANGE), (CHANNEL_RANGE, 0)]
}


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


def match_aspect_altitude_to_forecast(forecasts, aspect, altitude):
    ''' Operate on one list of SAIS forecasts in the same day
        to see which risk altitude range does the altitude fit 
        in. '''
    
    # If forecasts not available.
    if len(forecasts) <= 0:
        return -1
    
    # Validate aspect.
    if not (0 <= aspect <= 360):
        return -1
    forecast_search = [i for i in forecasts if str(i[3]) == get_facing_from_aspect(aspect)]
    if len(forecast_search) < 1:
        return -1
    forecast = forecast_search[0]

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


def risk_code_to_colour(risk_code):
    ''' Return an RGB 3-tuple for the colour represented by the risk_code. '''

    # [None: Gray, Low: Green, Moderate: Light Yellow, Considerable: Light Orange, High: Light Red, Very High: Dark Red]
    risks = [(192,192,192), (153,255,153), (255,255,153), (255,178,102), (255,102,102), (102,0,0)]
    
    if (risk_code < 0) or (risk_code) > 5: # Invalid data, not filling that pixel.
        return (255,255,255,0)
    else:
        # Add a 50% transparency channel (255/2)
        risks[risk_code] = risks[risk_code] + (127,)
        return risks[risk_code]


def aspect_to_grayscale(aspect):
    ''' Convert 0-360 degrees aspect to 0-255 grayscale. '''

    if (aspect < 0) or (aspect > 360): #Invalid data.
        return (255,255,255,0)
    else:
        converted_capacity = int(round(aspect / 360 * 255))
        return (255, 102, 102) + (converted_capacity, ) 


def aspect_to_rbg(aspect):
    ''' Convert aspect value to a spectrum of RGB colours. '''

    if (aspect < 0) or (aspect > 360): #Invalid data.
        return (255,255,255,0)
    elif (aspect == 0) or (aspect == 360): # Special case
        return (255, 0, 0)
    else:
        # Calculate the weird RGB coding.
        segment = int(aspect // 60)
        partition = aspect % 60
        offset = partition / 60.0 * 255.0
        colours = []

        for channel in CHANNEL_COLOURINGS:
            if CHANNEL_COLOURINGS[channel][segment][1] == CHANNEL_COLOURINGS[channel][segment][0]:
                colours.append(CHANNEL_COLOURINGS[channel][segment][1])
            else:
                colours.append(CHANNEL_COLOURINGS[channel][segment][0] + copysign(1, CHANNEL_COLOURINGS[channel][segment][1] - CHANNEL_COLOURINGS[channel][segment][0]) * offset)

        #Postprocessing: 75% capacity, 25% transparency.
        colours = map(lambda x: int(round(x)), colours)
        colours.append(191)
        colours = tuple(colours)

        return colours
