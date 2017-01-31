from __future__ import division

import os
import json
from collections import OrderedDict
from math import copysign
from colorsys import hsv_to_rgb

from GeoData import rasters

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


def risk_code_to_colour(risk_code, static_risk):
    ''' Return an RGB 3-tuple for the colour represented by the risk_code
        and static risk (represented by capacity). '''
    
    # HSV (Hue, Value)
    # [None: Gray, Low: Faint Yellow, Moderate: Dark Yellow, Considerable: Orange, High: Red, Very High: Dark Red]
    risks = [(0, 0.753), (0.167, 1), (0.115, 0.996), (0.070, 0.992), (0.022, 0.941), (0.966, 0.741)]
    
    if (risk_code < 0) or (risk_code) > 5: # Invalid data, not filling that pixel.
        return (255, 255, 255, 0)
    else:
        saturation = 1 - static_risk / (rasters.RISK_RASTER_MAX - rasters.RISK_RASTER_MIN) # Inverted saturation-risk relation.
        rgb_colour = list(map(lambda x: int(round(x * 255)), hsv_to_rgb(risks[risk_code][0], saturation, risks[risk_code][1])))
        return tuple(rgb_colour)


def aspect_to_grayscale(aspect):
    ''' Convert 0-360 degrees aspect to 0-255 grayscale. '''

    if (aspect < 0) or (aspect > 360): #Invalid data.
        return (255, 255, 255, 0)
    else:
        converted_capacity = int(round(aspect / 360 * 255))
        return (255, 102, 102) + (converted_capacity, ) 


def aspect_to_rbg(aspect):
    ''' Convert aspect value to a spectrum of RGB colours. '''

    if (aspect < 0) or (aspect > 360): #Invalid data.
        return (255, 255, 255, 0)
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

        #Postprocessing: 50% capacity, 50% transparency.
        colours = map(lambda x: int(round(x)), colours)
        colours.append(127)
        colours = tuple(colours)

        return colours


def contour_to_rbg(pixel_grayscale):
    ''' Return contour values as 50% capacity and transparency grey. '''

    # Experimental choice of feature (lines).
    try:
        pixel_value = int(round(pixel_grayscale))
        if pixel_value > 150:
            return (70, 70, 70, 175)
        else:
            return (255, 255, 255, 0)

    except ValueError:
        return (255, 255, 255, 0)
