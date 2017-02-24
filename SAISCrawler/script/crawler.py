###############################################################
# The crawler that loads avalanche forecast data from SAIS website
# and update them into the database.
###############################################################

import sys
import os
import re
import urlparse
import json
from selenium import webdriver, common
from time import sleep

import db_manager
import utils


class Crawler:
    """ The main class generating crawler instances to crawl the SAIS website. """

    def __init__(self):

        #Configure the source API.
        self.__crawlerReportURL = utils.read_config('reportAPI')
        self.__crawlerMapURL = utils.read_config('mapURL')
        self.__crawlerAvalancheURL = utils.read_config('avalancheURL')

        if len(self.__crawlerReportURL) == 0:
            raise ValueError("Empty report API URL in the configuration file!")

        #Configure the crawler.
        if sys.platform == "linux2":
            chromedriver = utils.get_project_full_path() + "/bin/chromedriver_linux" #This is the Linux driver.
        else:
            chromedriver = utils.get_project_full_path() + "/bin/chromedriver_osx" #Assume it's on OS X otherwise, not using Win.
        os.environ["webdriver.chrome.driver"] = chromedriver

        self._crawlerViewDriver = webdriver.Chrome(chromedriver)
        self._crawlerViewDriver.implicitly_wait(4)
        self._crawlerViewDriver.set_page_load_timeout(8)

        #Configure the DB interface.
        dbFile = utils.get_project_full_path() + utils.read_config('dbFile')
        self._DBManager = db_manager.CrawlerDB(dbFile)


    def quit(self):
        """ Exit the crawler webview driver. """
        self._crawlerViewDriver.quit()


    def crawl_forecasts(self, locations):
        """ Crawl data of locations in the list. """

        if len(locations) <= 0:
            return False

        #Fetch the report ID source for each location.
        crawlerLocations = []
        for item in locations:

            item = str(item)
            if not item.isdigit():
                return False

            locationInfo = self._DBManager.select_location_by_id(item)
            crawlerLocations.append([locationInfo[0], locationInfo[2]])

        for location in crawlerLocations:

            retry_count = 0
            load_success = False

            # Attempt to load the page three times, if not working then give up and throw exception.
            while not load_success:
                try:
                    self._crawlerViewDriver.get(location[1])
                    load_success = True
                except common.exceptions.TimeoutException:
                    retry_count += 1
                    if retry_count >= 3:
                        raise

            i = 1
            crawlerReports = []

            #Lookup all report IDs until exhaustion.
            while True:
                try:
                    crawlerReports.append(int(self._crawlerViewDriver.find_element_by_xpath("//ul[@id='report-dates']/li[" + str(i) + "]").get_attribute("data-report-id")))
                    i += 1
                except common.exceptions.NoSuchElementException:
                    break

            #List of lists.
            crawlerData = []

            if len(crawlerReports) == 0:
                raise Exception("SAISCrawler has failed to obtain any data for this location, likely a network error.")

            for report_id in crawlerReports:

                try:
                    #Fetch encoded data and its date.
                    self._crawlerViewDriver.get(self.__crawlerReportURL + str(report_id))
                    crawlerCrURL = self._crawlerViewDriver.find_element_by_xpath("//img[@id='cr-img']").get_attribute("src")
                    crawlerCrDate = str(self._crawlerViewDriver.find_element_by_xpath("//time[1]").get_attribute("datetime"))
                except:
                    #If the CR URL for that report cannot be loaded.
                    crawlerCrURL = None

                if crawlerCrURL != None:
                    #Wait a little while for throttling.
                    sleep(1)

                    #Parse a compassrose URL, with a integer string on length 32 as forecast data, and three altitude boundaries.
                    crawlerParsedURL = urlparse.urlparse(crawlerCrURL)
                    crawlerParsedQuery = urlparse.parse_qs(crawlerParsedURL.query)

                    #Decode the integer string data.
                    crawlerParsedForecastData = str(crawlerParsedQuery['val'][0])

                    #Decode the altitude parameters. They may not always be integers (e.g. "1055m"), so match first int found.
                    crawlerParsedForecastLowerBoundary = re.findall(r'\d+', str(crawlerParsedQuery['txts'][0]))[0]
                    #In case some reports not setting the middle boundary (found on Report #6095):
                    try:
                        crawlerParsedForecastMiddleBoundary = re.findall(r'\d+', str(crawlerParsedQuery['txtm'][0]))[0]
                    except KeyError:
                        crawlerParsedForecastMiddleBoundary = 0
                    crawlerParsedForecastUpperBoundary = re.findall(r'\d+', str(crawlerParsedQuery['txte'][0]))[0]

                    #Check that the data is of correct length.
                    if len(crawlerParsedForecastData) != 32:
                        raise ValueError("Invalid forecast data from webpage.")

                    #Slice data, order: N, NE, E, SE, S, SW, W, NW.
                    crawlerParsedForecastData = [crawlerParsedForecastData[i:i+4] for i in range(0,len(crawlerParsedForecastData),4)]
                    crawlerParsedForecastDataList = []
                    for data in crawlerParsedForecastData:
                        #Primary, Secondary values for lower, upper sectors.
                        crawlerParsedForecastDataList.append(((data[0], data[2]), (data[1], data[3])))

                    #Add all information to the data set.
                    crawlerData.append([crawlerCrDate, (crawlerParsedForecastLowerBoundary, crawlerParsedForecastMiddleBoundary, crawlerParsedForecastUpperBoundary), crawlerParsedForecastDataList])

            for data in crawlerData:
                self._DBManager.add_forecast(location[0], data[0], data[1], data[2])


    def crawl_past_avalanches(self):
        """ Crawl the Avalanche Map for past avalanches."""

        retry_count = 0
        load_success = False

        # Attempt to load the page three times, if not working then give up
        # and throw exception.
        while not load_success:
            try:
                self._crawlerViewDriver.get(self.__crawlerMapURL)
                load_success = True
            except common.exceptions.TimeoutException:
                retry_count += 1
                if retry_count >= 3:
                    raise

        # Obtain a list of years of record.
        map_options = self._crawlerViewDriver.find_element_by_xpath('//*[@id="mapform"]/select')
        option_values = [i.get_attribute("value") for i in map_options.find_elements_by_tag_name("option")]
        years = []
        for val in option_values:
            if val.isdigit():
                years.append(int(val))

        # Grab avalanche records of each year.
        for year in years:
            year_url = self.__crawlerAvalancheURL + str(year)
            sleep(1)
            self._crawlerViewDriver.get(year_url)
            page_scripts = self._crawlerViewDriver.find_elements_by_tag_name('script')

            # Locate the correct script containing the markers.
            correct_script = None
            for script in page_scripts:
                script_inner = script.get_attribute("innerHTML")
                if "var markers = " in script_inner:
                    correct_script = script_inner
                    break

            if correct_script is None:
                raise Exception("SAISCrawler has failed to find markers in " + str(year) + ", exiting.")

            # Locate the line with the markers.
            marker_line = None
            script_lines = correct_script.split('\n')
            for line in script_lines:
                line_str = str(line).strip()
                if line_str.startswith('var markers = '):
                    marker_line = line_str
                    break

            if marker_line is None:
                raise Exception("SAISCrawler has failed to find the marker line in " + str(year) + ", exiting.")

            line_start = marker_line.find('[')
            line_end = marker_line.rfind(']')
            marker_line = marker_line[line_start:line_end+1]

            try:
                marker_json = json.loads(marker_line)
            except ValueError:
                print(marker_line)
                raise Exception("SAISCrawler has failed to load the marker JSON in " + str(year) + ", exiting.")

            avalanche_records = []
            try:
                for avalanche in marker_json:
                    avalanche_record = [avalanche['ID'], avalanche['Easting'],
                    avalanche['Northing'], avalanche['Date'],
                    avalanche['Comments']]
                    avalanche_records.append(avalanche_record)
            except KeyError:
                raise Exception("SAISCrawler has failed to read the marker JSON in " + str(year) + ", exiting.")

            new, amended_count = self._DBManager.add_past_avalanches(avalanche_records)

            print("SAISCrawler: added {} new, amended {} for record year {}.".format(new, amended_count, year))

        return True


    def crawl_all(self):
        """ Crawl data for all locations in the database. """

        #self.crawl_forecasts(self._DBManager.select_all_location_id())
        self.crawl_past_avalanches()
        load_success = False


if __name__ == "__main__":
    forecastCrawler = Crawler()
    forecastCrawler.crawl_all()
