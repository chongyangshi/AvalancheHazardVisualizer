###############################################################
# The SQLite3 interface library for the crawler.
###############################################################

import sqlite3
import time
import datetime

import utils

class CrawlerDB:
    """ The class generating a database management interface object for the
        crawler to use."""

    def __init__(self, dbFileName):
        self.__CrawlerDBConnection = sqlite3.connect(dbFileName, check_same_thread=False)
        self.__CrawlerDBCursor = self.__CrawlerDBConnection.cursor()


    def select_location_by_id(self, locationID):
        """ Returns a single tuple containing the information for a location
            of the given ID: (ID, Name, ForecastURL)."""

        self.__CrawlerDBCursor.execute("SELECT * FROM locations WHERE\
            location_id == ?", (locationID,))
        location = self.__CrawlerDBCursor.fetchone()

        return location


    def select_location_by_name(self, locationName):
        """ Returns a list of tuples containing the information for locations
            with name partially matching locationName, possibly empty. """

        self.__CrawlerDBCursor.execute("SELECT * FROM locations WHERE\
            location_name LIKE '%' || ? || '%'", (locationName,))
        locations = self.__CrawlerDBCursor.fetchall()

        return locations


    def select_all_location_id(self):
        """ Returns a list of all locations' location_id. """

        self.__CrawlerDBCursor.execute("SELECT location_id FROM locations")
        locations = self.__CrawlerDBCursor.fetchall()

        return [i[0] for i in locations]


    def add_location(self, locationName, locationURL):
        """ Add a new location, returning the new location ID. If parameter
            invalid, return 0."""

        if len(locationName) == 0:
            return 0
        if (len(locationURL) == 0) or (not locationURL.startswith("http")):
            return 0

        self.__CrawlerDBCursor.execute("INSERT INTO locations VALUES\
            (NULL, ?, ?)", (locationName, locationURL,))
        newID = self.__CrawlerDBCursor.execute("SELECT location_id FROM\
            locations WHERE location_name = ? AND location_forecast_url = ?",\
            (locationName, locationURL,)).fetchone()
        self.__CrawlerDBConnection.commit()

        return newID[0]


    def delete_location(self, locationID):
        """ Delete a location with the given ID, returns false if param invalid,
            true otherwise."""

        if locationID <= 0:
            return False

        if self.select_location_by_id(locationID) == None:
            return False

        self.__CrawlerDBCursor.execute("DELETE FROM locations WHERE\
            location_id = ?", (locationID,))
        self.__CrawlerDBConnection.commit()

        return True


    def lookup_forecast_by_forecast_id(self, forecastID):
        """ Lookup one forecast by its ID, returns None if not exist. """

        if forecastID <= 0:
            return None

        self.__CrawlerDBCursor.execute("SELECT * FROM forecasts WHERE\
            forecast_id = ?", (forecastID,))
        forecast = self.__CrawlerDBCursor.fetchone()

        return forecast


    def lookup_forecast_by_precise_search(self, locationID, forecastDate, direction):
        """ Perform a precise lookup which returns one record on the given
            locationID, date and direction of forecast. Returns None if no such
            forecast record found."""

        if locationID <= 0:
            return None

        if self.select_location_by_id(locationID) == None:
            return None

        if not utils.check_date_string(forecastDate): #If invalid date input
            return None

        if not utils.check_direction(direction): #If invalid direction
            return None

        self.__CrawlerDBCursor.execute("SELECT * FROM forecasts WHERE\
            location_id = ? AND forecast_date = ? AND direction = ?",\
            (locationID, forecastDate, direction,))
        forecast = self.__CrawlerDBCursor.fetchone()

        return forecast


    def lookup_newest_forecast_by_location_id(self, locationID, direction):
        """ Lookup the most recent forecast for a given location_id and
            direction, returns None if none exist. """

        if locationID <= 0:
            return None

        if self.select_location_by_id(locationID) == None:
            return None

        if not utils.check_direction(direction): #If invalid direction
            return None

        self.__CrawlerDBCursor.execute("SELECT * FROM forecasts WHERE\
            location_id = ? AND direction = ? ORDER BY date(forecast_date) DESC",\
            (locationID, direction,))
        forecast = self.__CrawlerDBCursor.fetchone()

        return forecast


    def lookup_newest_forecasts_by_location_id(self, locationID):
        """ Lookup the most recent forecasts for all directions for a given
            location_id, returns None if none exist. """

        if locationID <= 0:
            return None

        if self.select_location_by_id(locationID) == None:
            return None

        self.__CrawlerDBCursor.execute("SELECT * FROM forecasts WHERE location_id = ? \
            AND forecast_date = (SELECT MAX(forecast_date) FROM forecasts WHERE\
            location_id = ?);",\
            (locationID, locationID))
        forecast = self.__CrawlerDBCursor.fetchall()

        return forecast


    def lookup_forecasts_by_location_id(self, locationID):
        """ Lookup all forecasts of a given location by location_id. Returns
            empty set if location_id invalid or no forecasts available. """

        if locationID <= 0:
            return []

        if self.select_location_by_id(locationID) == None:
            return []

        self.__CrawlerDBCursor.execute("SELECT * FROM forecasts WHERE\
            location_id = ?", (locationID,))
        forecasts = self.__CrawlerDBCursor.fetchall()

        return forecasts


    def lookup_forecasts_by_location_id_and_date(self, locationID, forecastDate):
        """ Lookup the day's forecasts of a given location by location_id. Returns
            empty set if location_id invalid or no forecasts available. """

        if locationID <= 0:
            return []

        if self.select_location_by_id(locationID) == None:
            return []

        if not utils.check_date_string(forecastDate):
            return False

        self.__CrawlerDBCursor.execute("SELECT * FROM forecasts WHERE\
            location_id = ? AND forecast_date = ?", (locationID, forecastDate,))
        forecasts = self.__CrawlerDBCursor.fetchall()

        return forecasts


    def lookup_forecast_dates(self, locationID):
        """ Given a location ID, lookup the dates for the last (up to)
            50 forecasts. """

        if locationID <= 0:
            return False

        if self.select_location_by_id(locationID) == None:
            return False

        self.__CrawlerDBCursor.execute("SELECT DISTINCT(forecast_date) FROM forecasts\
            WHERE location_id = ? ORDER BY forecast_date DESC LIMIT 50", (locationID,))
        dates = self.__CrawlerDBCursor.fetchall()

        return dates


    def add_forecast(self, locationID, forecastDate, boundaries, dataset):
        """ Add a forecast data set into the database, locationID must match an
            existing location, boundaries must be a three-value tuple containing
            the three levels in the graph, with the lower boundary being smaller
            than the upper boundary, dataset must be a list of tuples in the form
            of [((lowerPrimary, lowerSecondary), (upperPrimary, upperSecondary))].
            It is worth noting that for each direction (N, NE, E, SE, S, SW,
             W, NW), a record is to be created on the same date's data. """

        if locationID <= 0:
            return False

        if self.select_location_by_id(locationID) == None:
            return False

        #Lower boundary must be smaller than the upper boundary, middle boundary may not be available.
        if int(boundaries[0]) >= int(boundaries[2]):
            return False

        if not utils.check_date_string(forecastDate):
            return False

        directions = ["N", "NE", "E", "SE", "S", "SW", "W", "NW"];
        if len(dataset) != len(directions): #Mismatched number of records.
            return False

        for i in range(0, len(dataset)):
            #First check if record already exists, if so, update existing record.
            data = dataset[i]
            direction = directions[i]
            existenceCheck = self.lookup_forecast_by_precise_search(locationID,
             forecastDate, direction)

            if existenceCheck != None: #Record already exists.
                self.__CrawlerDBCursor.execute("UPDATE forecasts SET\
                    lower_boundary = ?, middle_boundary = ?, upper_boundary = ?,\
                    lower_primary_colour = ?, lower_secondary_colour = ?,\
                    upper_primary_colour = ?, upper_secondary_colour = ? WHERE\
                    forecast_id = ?", (boundaries[0], boundaries[1],\
                    boundaries[2], data[0][0], data[0][1],\
                    data[1][0], data[1][1], existenceCheck[0],))

            else: #Add new record.
                self.__CrawlerDBCursor.execute("INSERT INTO forecasts VALUES\
                    (NULL, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",\
                    (locationID, forecastDate, direction, boundaries[0],\
                    boundaries[1], boundaries[2], data[0][0], data[0][1],\
                    data[1][0], data[1][1],))

        self.__CrawlerDBConnection.commit()

        return True


    def delete_forecast(self, forecastID):
        """ Delete a forecast by ID from the database, return False if ID
            invalid. """

        if forecastID <= 0:
            return False

        if self.lookup_forecast_by_forecast_id(forecastID) == None:
            return False

        self.__CrawlerDBCursor.execute("DELETE FROM forecasts WHERE\
            forecast_id = ?", (forecastID,))
        self.__CrawlerDBConnection.commit()

        return True


    def delete_forecasts_for_location_id(self, locationID):
        """ Delete all forecasts for a given location_id. """

        if locationID <= 0:
            return False

        if self.select_location_by_id(locationID) == None:
            return False

        if self.lookup_forecasts_by_location_id(locationID) == []:
            return False

        self.__CrawlerDBCursor.execute("DELETE FROM forecasts WHERE\
            location_id = ?", (locationID,))
        self.__CrawlerDBConnection.commit()

        return True


    def add_past_avalanches(self, past_avalanches):
        """ Add a list of past avalanches to the list. Return the number of
            successfully added/amended avalanche records. """

        new_count = 0
        amended_count = 0

        for avalanche in past_avalanches:

            # Validation.
            valid_avalanche = True
            for i in range(3):
                if (not isinstance(avalanche[i], int)) or (avalanche[i] < 1):
                    valid_avalanche = False

            converted_time = self.convert_time_string(avalanche[3].replace('\\', ''))
            if not converted_time:
                valid_avalanche = False

            if valid_avalanche:
                self.__CrawlerDBCursor.execute("SELECT avalanche_internal_id FROM\
                    past_avalanches WHERE avalanche_id = ?",
                    (avalanche[0],)) # Check identical avalanches.
                same_ids = self.__CrawlerDBCursor.fetchall()
                if len(same_ids) <= 0: # If a new one add it.
                    self.__CrawlerDBCursor.execute("INSERT INTO past_avalanches\
                        VALUES (NULL, ?, ?, ?, ?, ?)",
                        (avalanche[0], avalanche[1], avalanche[2],
                        converted_time, avalanche[4],))
                    new_count += 1
                else: # Amend existing record.
                    self.__CrawlerDBCursor.execute("UPDATE past_avalanches SET \
                        avalanche_id = ? , easting = ?, norting = ?, \
                        avalanche_time = ?, avalanche_comment = ? WHERE\
                        avalanche_internal_id = ?",
                        (avalanche[0], avalanche[1], avalanche[2],
                        converted_time, avalanche[4], same_ids[0][0],))
                    amended_count += 1

        self.__CrawlerDBConnection.commit()

        return new_count, amended_count


    def select_past_avalanches_by_date_range(self, start_date, end_date):
        """ Retrieve past avalanches that happened between start_date and
            end_date. """

        start_date = self.convert_time_string(start_date.replace('\\', ''))
        end_date = self.convert_time_string(end_date.replace('\\', ''))

        if (not start_date) or (not end_date):
            return False

        self.__CrawlerDBCursor.execute("SELECT * FROM past_avalanches WHERE\
            avalanche_time >= Datetime(?) AND avalanche_time <= Datetime(?)",
            (start_date, end_date))
        avalanches = self.__CrawlerDBCursor.fetchall()

        return avalanches


    def select_all_past_avalanches(self):
        """ Retrieve all recorded past avalanches, very slow, for use in evaluation
            script only. """

        self.__CrawlerDBCursor.execute("SELECT * FROM past_avalanches ")
        avalanches = self.__CrawlerDBCursor.fetchall()

        return avalanches


    def delete_past_avalanches_by_date_range(self, start_date, end_date):
        """ Delete past avalanches that happened between start_date and
            end_date. """

        start_date = self.convert_time_string(start_date.replace('\\', ''))
        end_date = self.convert_time_string(end_date.replace('\\', ''))

        if (not start_date) or (not end_date):
            return False

        self.__CrawlerDBCursor.execute("DELETE FROM past_avalanches WHERE\
            avalanche_time >= Datetime(?) AND avalanche_time <= Datetime(?)",
            (start_date, end_date))

        return True


    @staticmethod
    def convert_time_string(time_string):
        """ Verify and convert an English date/datetime into a universal
            date/datetime. """

        try:
            time_string = time_string.strip()

            if ' ' in time_string: # With time.
                if '/' in time_string:
                    format_string = '%d/%m/%Y %H:%M'
                else:
                    format_string = '%Y-%m-%d %H:%M'
                target_string = '%Y-%m-%d %H:%M'
            else:
                if '/' in time_string:
                    format_string = '%d/%m/%Y'
                else:
                    format_string = '%Y-%m-%d'
                target_string = '%Y-%m-%d'

            converted_date = datetime.datetime.strptime(time_string,
             format_string).strftime(target_string)

            return converted_date

        except ValueError:
            return False

"""
a = CrawlerDB(utils.get_project_full_path() + "/data/forecast.db")
print a.select_location_by_id("2")
print a.select_location_by_name("cairn")
print a.add_location("Test", "http://Test")
print a.delete_location("7")
print a.add_forecast("6", '2016-04-04', ('750', '900', '1055'), [(('1', '0'), ('1', '0')), (('1', '0'), ('1', '2')), (('1', '0'), ('1', '2')), (('1', '0'), ('1', '0')), (('1', '0'), ('1', '0')), (('1', '0'), ('1', '0')), (('1', '0'), ('1', '0')), (('1', '0'), ('1', '0'))])
print a.add_forecast("6", '2016-04-05', ('750', '800', '1055'), [(('1', '0'), ('1', '2')), (('1', '0'), ('2', '0')), (('1', '0'), ('2', '0')), (('1', '0'), ('1', '2')), (('1', '0'), ('1', '0')), (('1', '0'), ('1', '0')), (('1', '0'), ('1', '0')), (('1', '0'), ('1', '0'))])
print a.lookup_forecasts_by_location_id("6")
print a.lookup_forecast_by_precise_search("6", "2016-04-05", "S")
print a.lookup_forecast_by_forecast_id("10")
print a.add_past_avalanches([[4320, 298637, 802844, "23\/02\/2017 13:00", "Exact location (can't use map function) - steep slopes immediately below start of Milky Way. Soft slab avalanche which broke away harmlessly below us - narrow near miss for us."], [4318, 219199, 772963, "23\/02\/2017 11:00", "Debris observed by climbers at 760 metres on West aspect on Aonach Mor from a natural slab avalanche earlier in the day."]])
print a.select_past_avalanches_by_date_range('22/02/2017', '24/02/2017')
print a.delete_past_avalanches_by_date_range('22/02/2017', '24/02/2017')
"""
