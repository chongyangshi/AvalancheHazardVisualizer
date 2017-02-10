###############################################################
# This stand-alone script imports configurations from a csv file
# into a table in a sqlite3 database for storage
###############################################################

import os
import sys
import csv
import sqlite3

if len(sys.argv) != 2:
    sys.exit("Usage: python db_import.py {source_csv_file}")

for arg in sys.argv:
    if len(arg) == 0:
        sys.exit("Usage: python db_import.py {source_csv_file}")

# Create connection.
scriptParentDirectory = os.path.dirname(os.path.abspath(os.path.join(__file__, os.pardir)))
dbImportDatabase = scriptParentDirectory + "/data/forecast.db"
dbImportConnection = sqlite3.connect(dbImportDatabase)
dbImportConnectionCursor = dbImportConnection.cursor()

# Parse the CSV file.
dbImportDataset = []
with open(sys.argv[1], 'r') as csvfile:
    content = csv.reader(csvfile, delimiter=',')
    for line in content:
        dbImportDataset.append((line[0].strip(), line[1].strip()[1:-1]))

# Create tables.
dbImportConnectionCursor.execute("""
        CREATE TABLE locations
        (location_id INTEGER PRIMARY KEY,
        location_name TEXT,
        location_forecast_url TEXT
        )"""
    )
dbImportConnectionCursor.execute("""
        CREATE TABLE forecasts
        (forecast_id INTEGER PRIMARY KEY,
        location_id INTEGER REFERENCES locations(location_id) ON DELETE CASCADE,
        forecast_date TEXT,
        direction TEXT,
        lower_boundary INTEGER,
        middle_boundary INTEGER,
        upper_boundary INTEGER,
        lower_primary_colour INTEGER,
        lower_secondary_colour INTEGER,
        upper_primary_colour INTEGER,
        upper_secondary_colour INTEGER
        )"""
    )

# Insert set of locations from the file.
dbImportConnectionCursor.executemany(\
    "INSERT INTO locations VALUES (NULL, ?, ?)", dbImportDataset)

# Commit changes and close connection.
dbImportConnection.commit()
dbImportConnection.close()
