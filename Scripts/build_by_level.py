#!/usr/bin/python

# Build virtual raster for each zoom level, in order to reproject a large terrain raster 
# into Cesium terrain model without causing integer overflow.
# Derived from https://github.com/geo-data/cesium-terrain-builder/issues/37#issuecomment-252857173 by Stelios Vitalis <liberostelios@gmail.com>

import os, sys

def run_cmd(cmd):
    print("$ " + cmd)
    os.system(cmd)

# Local script, therefore no sanity check. Do not use any non-pre-defined paths.

input_raster = "/data/testinput.tif"
output_dir = "/data/testout"
temp_dir = "/data/testtemp"
start_level = 18
end_level = 0

if (start_level <= end_level) or (end_level < 0):
    print("Error: start_level must be at least 1, end_level must be at least 0.")
    sys.exit(1)

if (not os.path.exists(input_raster)) or (not os.path.exists(output_dir)) or (not os.path.exists(temp_dir)):
    print("Error: input_raster, output_dir and temp_dir must all exist.")
    sys.exit(1)

#Build top-level tile
run_cmd("ctb-tile --output-dir " + output_dir + "/ --start-zoom " + str(start_level) + " --end-zoom " + str(start_level) + " " + input_raster)

for i in range(start_level, end_level, -1): #No need to build below end_level, so intentionally finishing loop on 1.
    
    current_level = str(i)
    next_level = str(i-1)

    # Build GDAL tileset for current level.
    run_cmd("ctb-tile --output-format GTiff --output-dir " + temp_dir + "/ --start-zoom " + current_level + " --end-zoom " + current_level + " " + input_raster)
    
    # Build Virtual Raster for current level from the GDAL tileset.
    run_cmd("find " + temp_dir + "/" + current_level + " -name '*.tif' | xargs gdalbuildvrt " + temp_dir + "/level" + current_level + ".vrt")

    # Finally build the terrain for next level based on the Virtual Raster.
    run_cmd("ctb-tile -o " + output_dir + "/ --start-zoom " + next_level + " --end-zoom " + next_level + " " + temp_dir + "/level" + current_level + ".vrt")

