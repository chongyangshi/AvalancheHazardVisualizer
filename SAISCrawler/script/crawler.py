###############################################################
# The crawler that loads avalanche forecast data from SAIS website
# and update them into the database.
###############################################################

import sys
import os
import re
import urlparse
from selenium import webdriver, common
from time import sleep

import db_manager
import utils


class Crawler:
    """ The main class generating crawler instances to crawl the SAIS website. """

    def __init__(self):

        #Configure the source API.
        self.__crawlerReportURL = utils.read_config('reportAPI')
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


    def crawl(self, locations):
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


    def crawl_all(self):
        """ Crawl data for all locations in the database. """
        self.crawl(self._DBManager.select_all_location_id())


if __name__ == "__main__":
    forecastCrawler = Crawler()
    forecastCrawler.crawl_all()
