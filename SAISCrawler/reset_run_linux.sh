#!/bin/bash
# This script erases the current database, recreate one and pull new
# forecast data into the database.

#Obtain the script directory
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

#Launch Xvfb session for Linux.
Xvfb -auth /etc/X99.cfg :99 -screen scrn 1280x1024x16 &
export DISPLAY=:99

rm $DIR/data/forecast.db
python $DIR/script/db_import.py $DIR/data/SAIS_locations.csv
python $DIR/script/crawler.py

killall Xvfb
