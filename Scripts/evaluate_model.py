#!/usr/bin/pythonw
# Evaluate the static risk model against past avalanches recorded by the SAIS.
from __future__ import division
import os
import sys
import numpy as np
import matplotlib.pyplot as plt
from collections import OrderedDict

from SAISCrawler.script import db_manager, utils
from GeoData import raster_reader, rasters, bng_to_lonlat

THRESHOLD_PERCENTILES = [0.5, 0.75, 0.9, 0.95, 0.99, 0.995]
THRESHOLD_VALUES = [2.0151e-04, 6.6681e-04, 0.0029, 0.0086, 0.0890, 0.1230]
DISTANCES = [5, 10, 25, 50, 100]
DISTANCE_COLOURS = ['r', 'b', 'g', 'k', 'm']
RASTER_RESOLUTION = 5

dbFile = './SAISCrawler/data/forecast.db'
avalanche_dbm = db_manager.CrawlerDB(dbFile)
static_risk = raster_reader.RasterReader(rasters.RISK_RASTER)

all_past_avalanches = avalanche_dbm.select_all_past_avalanches()
accuracy_data = OrderedDict({})
print("==========================================================")
for distance in DISTANCES:
    accuracy_data[distance*RASTER_RESOLUTION] = []
    for threshold in THRESHOLD_PERCENTILES:
        current_threshold_hits = 0
        total_tested = 0
        for avalanche in all_past_avalanches:

            # Convert BNG locations to coordinates.
            x, y = bng_to_lonlat.OSGB36toWGS84(avalanche[2], avalanche[3])

            # Calculate the coordinates of the initial and final points of our bounding box.
            # First four params can refer to the same coordinate due to how the function works.
            index_x, index_y = static_risk.coordinate_to_index(x, y)
            box_initial = static_risk.index_to_coordinate(index_x - distance, index_y - distance)
            box_final = static_risk.index_to_coordinate(index_x + distance, index_y + distance)

            # Read the static risk in the bounding box.
            risk_points = static_risk.read_points(box_initial[0], box_initial[1], box_final[0], box_final[1])
            if isinstance(risk_points, bool):
                if not risk_points:
                    # Box outside raster boundary, discard.
                    continue

            # Now count the total and check whether it's a hit.
            total_tested += 1
            max_risk = np.amax(risk_points)

            if max_risk >= threshold:
                current_threshold_hits += 1

        accuracy_data[distance*RASTER_RESOLUTION].append((threshold * 100, current_threshold_hits/total_tested)) # (percentile, accuracy)

        print("At a percentile of {} ({}), within a square bounding box of {} meters, the accuracy is {} ({}/{})"
        .format(str(threshold * 100) + '%', THRESHOLD_VALUES[THRESHOLD_PERCENTILES.index(threshold)],
        distance * RASTER_RESOLUTION, current_threshold_hits/total_tested, current_threshold_hits,
        total_tested))
print("==========================================================")

# Make plots.
plt.figure(1)
plt.axis([40, 110, 0, 100])
plt.title('Accuracy of Static Risk Model in Recalling Recorded Avalanches')
plt.xlabel("Risk Threshold (percentile)")
plt.ylabel("Recall Accuracy (%)")
plt.grid(True)
colour_count = 0
text_y = 2
for d in accuracy_data:
    plt.plot([i[0] for i in accuracy_data[d]], [i[1] * 100 for i in accuracy_data[d]], DISTANCE_COLOURS[colour_count] + '+')
    plt.text(41, text_y, "+: searching within " + str(d) + 'm', color=DISTANCE_COLOURS[colour_count])
    colour_count += 1
    text_y += 3.5
plt.show()
