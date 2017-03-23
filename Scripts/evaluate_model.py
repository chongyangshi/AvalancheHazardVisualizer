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

THRESHOLD_PERCENTILES = [
    50.000000, 52.500000, 55.000000, 57.500000, 60.000000,
    62.500000, 65.000000, 67.500000, 70.000000, 72.500000,
    75.000000, 77.500000, 80.000000, 82.500000, 85.000000,
    87.500000, 90.000000, 92.500000, 95.000000, 97.500000,
    99.500000]
THRESHOLD_VALUES = [
    2.015127e-04, 2.015127e-04, 2.015127e-04, 2.015127e-04, 2.119121e-04,
    2.673585e-04, 3.260623e-04, 3.911575e-04, 4.662734e-04, 5.560244e-04,
    6.668069e-04, 8.067768e-04, 9.898760e-04, 1.235987e-03, 1.580646e-03,
    2.089052e-03, 2.906299e-03, 4.449752e-03, 8.608662e-03, 3.165039e-02,
    0.1230]

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
    for t in range(len(THRESHOLD_PERCENTILES)):
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

            if max_risk >= THRESHOLD_VALUES[t]:
                current_threshold_hits += 1

        accuracy_data[distance*RASTER_RESOLUTION].append((THRESHOLD_PERCENTILES[t], current_threshold_hits/total_tested)) # (percentile, accuracy)
        print("{}m at {}pct: accuracy {}%".format(distance * RASTER_RESOLUTION, THRESHOLD_PERCENTILES[t], current_threshold_hits/total_tested * 100))
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
    plt.plot([i[0] for i in accuracy_data[d]], [i[1] * 100 for i in accuracy_data[d]], DISTANCE_COLOURS[colour_count] + '-')
    plt.text(41, text_y, "-: searching within " + str(d) + 'm', color=DISTANCE_COLOURS[colour_count])
    colour_count += 1
    text_y += 3.5
plt.show()
