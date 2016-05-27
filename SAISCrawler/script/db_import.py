###############################################################
# This stand-alone script imports configurations from a csv file
# into a table in a sqlite3 database for storage
###############################################################

import os
import sys
import csv
import sqlite3

if len(sys.argv) != 3:
    sys.exit("Usage: python db_import.py {source_csv_file} {destination_table_name}")

for arg in sys.argv:
    if len(arg) == 0:
        sys.exit("Usage: python db_import.py {source_csv_file} {destination_table_name}")

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
 
# Create table.
dbImportConnectionCursor.execute("CREATE TABLE " + sys.argv[2] +\
    ''' (location_id INTEGER PRIMARY KEY, 
        location_name TEXT, 
        location_forecast_url TEXT
        )'''
    )

# Insert dataset.
dbImportConnectionCursor.executemany(\
    "INSERT INTO " + sys.argv[2] + " VALUES (NULL, ?, ?)", dbImportDataset)

# Commit changes and close connection.
dbImportConnection.commit()
dbImportConnection.close()
