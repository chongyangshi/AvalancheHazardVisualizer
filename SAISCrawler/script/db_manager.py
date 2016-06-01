###############################################################
# The SQLite3 interface library for the crawler.
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
            invalid, return 0.'''

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

        self.__CrawlerDBCursor.execute("DELETE FROM locations WHERE location_id = ?", (locationID,))
        self.__CrawlerDBConnection.commit()

        return True


    def lookup_forecast_by_forecast_id(self, forecastID):
        ''' Lookup one forecast by its ID, returns None if not exist. '''

        if forecastID <= 0:
            return None

        self.__CrawlerDBCursor.execute("SELECT * FROM forecasts WHERE forecast_id = ?", (forecastID,))
        forecast = self.__CrawlerDBCursor.fetchone()

        return forecast


    def lookup_forecast_by_precise_search(self, locationID, forecastDate, direction):
        ''' Perform a precise lookup which returns one record on the given
            locationID, date and direction of forecast. Returns None if no such
            forecast record found.'''

        if locationID <= 0:
            return None

        if self.select_location_by_id(locationID) == None:
            return None

        if not utils.check_date_string(forecastDate): #If invalid date input
            return None

        if not utils.check_direction(direction): #If invalid direction
            return None

        self.__CrawlerDBCursor.execute("SELECT * FROM forecasts WHERE location_id = ? AND forecast_date = ? AND direction = ?", (locationID, forecastDate, direction,))
        forecast = self.__CrawlerDBCursor.fetchone()

        return forecast


    def lookup_newest_forecast_by_location_id(self, locationID, direction):
        ''' Lookup the most recent forecast for a given location_id and
            direction, returns None if none exist. '''

        if locationID <= 0:
            return None

        if self.select_location_by_id(locationID) == None:
            return None

        if not utils.check_direction(direction): #If invalid direction
            return None

        self.__CrawlerDBCursor.execute("SELECT * FROM forecasts WHERE location_id = ? AND direction = ? ORDER BY date(forecast_date) DESC", (forecastID, direction,))
        forecast = self.__CrawlerDBCursor.fetchone()


    def lookup_forecasts_by_location_id(self, locationID):
        ''' Lookup all forecasts of a given location by location_id. Returns
            empty set if location_id invalid or no forecasts available. '''

        if locationID <= 0:
            return []

        if self.select_location_by_id(locationID) == None:
            return []

        self.__CrawlerDBCursor.execute("SELECT * FROM forecasts WHERE location_id = ?", (locationID,))
        forecasts = self.__CrawlerDBCursor.fetchall()

        return forecasts


    def add_forecast(self, locationID, forecast_date, boundaries, dataset):
        ''' Add a forecast data set into the database, locationID must match an
            existing location, boundaries must be a three-value tuple containing
            the three levels in the graph, with the lower boundary being smaller
            than the upper boundary, dataset must be a list of tuples in the form
            of [((lowerPrimary, lowerSecondary), (upperPrimary, upperSecondary))].
            It is worth noting that for each direction (N, NE, E, SE, S, SW,
             W, NW), a record is to be created on the same date's data. '''

        if locationID <= 0:
            return False

        if self.select_location_by_id(locationID) == None:
            return False

        #Lower boundary must be smaller than the upper boundary, middle boundary may not be available.
        if int(boundaries[0]) >= int(boundaries[2]):
            return False

        if not utils.check_date_string(forecast_date):
            return False

        directions = ["N", "NE", "E", "SE", "S", "SW", "W", "NW"];
        if len(dataset) != len(directions): #Mismatched number of records.
            return False
        for i in range(0, len(dataset)):
            data = dataset[i]
            direction = directions[i]
            self.__CrawlerDBCursor.execute("INSERT INTO forecasts VALUES (NULL, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",\
                (locationID, forecast_date, direction, boundaries[0],\
                boundaries[1], boundaries[2], data[0][0], data[0][1],\
                data[1][0], data[1][1],))
        self.__CrawlerDBConnection.commit()

        return True


    def delete_forecast(self, forecastID):
        ''' Delete a forecast by ID from the database, return False if ID
            invalid. '''

        if forecastID <= 0:
            return False

        if self.lookup_forecast_by_forecast_id(forecastID) == None:
            return False

        self.__CrawlerDBCursor.execute("DELETE FROM forecasts WHERE forecast_id = ?", (forecastID,))
        self.__CrawlerDBConnection.commit()

        return True


    def delete_forecasts_for_location_id(self, locationID):
        ''' Delete all forecasts for a given location_id. '''

        if locationID <= 0:
            return False

        if self.select_location_by_id(locationID) == None:
            return False

        if self.lookup_forecasts_by_location_id(locationID) == []:
            return False

        self.__CrawlerDBCursor.execute("DELETE FROM forecasts WHERE location_id = ?", (locationID,))
        self.__CrawlerDBConnection.commit()

        return True

'''
a = CrawlerDB(utils.get_project_full_path() + "/data/forecast.db")
print a.select_location_by_id("2")
print a.select_location_by_name("cairn")
print a.add_location("Test", "http://Test")
print a.delete_location("7")
print a.add_forecast("6", '2016-04-04', ('750', '900', '1055'), [(('1', '0'), ('1', '0')), (('1', '0'), ('1', '2')), (('1', '0'), ('1', '2')), (('1', '0'), ('1', '0')), (('1', '0'), ('1', '0')), (('1', '0'), ('1', '0')), (('1', '0'), ('1', '0')), (('1', '0'), ('1', '0'))])
print a.add_forecast("6", '2016-04-05', ('750', '800', '1055'), [(('1', '0'), ('1', '2')), (('1', '0'), ('2', '0')), (('1', '0'), ('2', '0')), (('1', '0'), ('1', '2')), (('1', '0'), ('1', '0')), (('1', '0'), ('1', '0')), (('1', '0'), ('1', '0')), (('1', '0'), ('1', '0'))])
print a.lookup_forecasts_by_location_id("6")
print a.lookup_forecast_by_precise_search("6", "2016-04-05", "S")
print a.lookup_forecast_by_forecast_id("10")'''
