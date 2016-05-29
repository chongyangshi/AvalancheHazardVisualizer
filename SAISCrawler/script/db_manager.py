###############################################################
# The SQLite3 interface library for the crawler.
# TODO: write this
###############################################################

import sqlite3

import utils

class CrawlerDB:
    ''' The class generating a database management interface object for the
        crawler to use.'''

    def __init__(self, dbFileName):
        self.__CrawlerDBConnection = sqlite3.connect(dbFileName)
        self.__CrawlerDBCursor = self.__CrawlerDBConnection.cursor()

    def select_location_by_id(self, locationID):
        ''' Returns a single tuple containing the information for a location
            of the given ID: (ID, Name, ForecastURL).'''

        self.__CrawlerDBCursor.execute("SELECT * FROM locations WHERE location_id == ?", (locationID,))
        location = self.__CrawlerDBCursor.fetchone()

        return location

    def select_location_by_name(self, locationName):
        ''' Returns a list of tuples containing the information for locations
            with name partially matching locationName, possibly empty. '''

        self.__CrawlerDBCursor.execute("SELECT * FROM locations WHERE location_name LIKE '%' || ? || '%'", (locationName,))
        locations = self.__CrawlerDBCursor.fetchall()

        return locations

    def add_location(self, locationName, locationURL):
        ''' Add a new location, returning the new location ID. If parameter
            invalud, return 0.'''

        if len(locationName) == 0:
            return 0
        if (len(locationURL) == 0) or (not locationURL.startswith("http")):
            return 0

        self.__CrawlerDBCursor.execute("INSERT INTO locations VALUES (NULL, ?, ?)", (locationName, locationURL,))
        newID = self.__CrawlerDBCursor.execute("SELECT location_id FROM locations WHERE location_name = ? AND location_forecast_url = ?", (locationName, locationURL,)).fetchone()
        self.__CrawlerDBConnection.commit()

        return newID[0]

    def delete_location(self, locationID):
        ''' Delete a location with the given ID, returns false if param invalid,
            true otherwise.'''

        if locationID <= 0:
            return False

        if self.select_location_by_id(locationID) == None:
            return False

        self.__CrawlerDBConnection.execute("DELETE FROM locations WHERE location_id = ?", (locationID,))
        self.__CrawlerDBConnection.commit()

        return True

a = CrawlerDB(utils.get_project_full_path() + "/data/forecast.db")
print a.select_location_by_id("2")
print a.select_location_by_name("cairn")
print a.add_location("Test", "http://Test")
print a.delete_location("7")
