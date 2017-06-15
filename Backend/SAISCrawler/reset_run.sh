#!/bin/bash
# This script erases the current database, recreate one and pull new
# forecast data into the database.

#Obtain the script directory
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

rm $DIR/data/forecast.db
python $DIR/script/db_import.py $DIR/data/SAIS_locations.csv
python $DIR/script/crawler.py
