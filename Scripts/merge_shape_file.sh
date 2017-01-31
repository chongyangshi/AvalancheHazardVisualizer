#!/bin/sh

# Merge individual shape files to a full shape file for rasterisation.
OPERATING_DIRECTORY = /Data/
TEMP_DIRECTORY = $OPERATING_DIRECTORY/temp
OUTPUT_FILE = $OPERATING_DIRECTORY/merged.shp
find $OPERATING_DIRECTORY -name '*_line*' -print > $OPERATING_DIRECTORY/lines.txt
xargs -a $OPERATING_DIRECTORY/lines.txt cp -t $TEMP_DIRECTORY
for f in $TEMP_DIRECTORY/*.shp; do ogr2ogr -update -append $OUTPUT_FILE $f -f "ESRI Shapefile"; done;


