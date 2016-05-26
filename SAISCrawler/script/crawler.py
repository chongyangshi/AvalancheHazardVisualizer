import os
import urlparse
from selenium import webdriver, common

#Report locations to be crawled, first is name, second is data listing source.
crawlerLocations = [("Creag Meagaidh", "http://www.sais.gov.uk/creag-meagaidh/"),
                    ("Glencoe", "http://www.sais.gov.uk/glencoe/"),
                    ("Lochaber", "http://www.sais.gov.uk/lochaber/"),
                    ("Nothern Cairngorms", "http://www.sais.gov.uk/northern-cairngorms/"),
                    ("Southern Cairngorms", "http://www.sais.gov.uk/southern-cairngorms/"),
                    ("Torridon", "http://www.sais.gov.uk/torridon/")]

#The API source of report request.
crawlerReportURL = "http://www.sais.gov.uk/_ajax_report/?report_id="

#Configure the crawler.
scriptParentDirectory = os.path.dirname(os.path.abspath(os.path.join(__file__, os.pardir)))
chromedriver = scriptParentDirectory + "/bin/chromedriver"
os.environ["webdriver.chrome.driver"] = chromedriver
crawlerViewDriver = webdriver.Chrome(chromedriver)
crawlerViewDriver.implicitly_wait(4)
crawlerViewDriver.set_page_load_timeout(4)

#Crawl through each location.
crawlerLocationReports = dict()
for location in crawlerLocations:

    crawlerViewDriver.get(location[1])

    i = 1
    crawlerReports = []

    while True:
        try:
            crawlerReports.append(int(crawlerViewDriver.find_element_by_xpath("//ul[@id='report-dates']/li[" + str(i) + "]").get_attribute("data-report-id")))
            i += 1
        except common.exceptions.NoSuchElementException:
            break

    #List of lists
    crawlerData = []

    for report_id in crawlerReports:

        try:
            #Fetch encoded data and its date.
            crawlerViewDriver.get(crawlerReportURL + str(report_id))
            crawlerCrURL = crawlerViewDriver.find_element_by_xpath("//img[@id='cr-img']").get_attribute("src")
            crawlerCrDate = str(crawlerViewDriver.find_element_by_xpath("//time[1]").get_attribute("datetime"))
        except:
            #If the CR URL for that report cannot be loaded.
            crawlerCrURL = None

        if crawlerCrURL != None:

            #Parse a compassrose URL, with a integer string on length 32 as forecast data, and three altitude boundaries.
            crawlerParsedURL = urlparse.urlparse(crawlerCrURL)
            crawlerParsedQuery = urlparse.parse_qs(crawlerParsedURL.query)

            #Decode the integer string data.
            crawlerParsedForecastData = str(crawlerParsedQuery['val'][0])
            crawlerParsedForecastLowerBoundary = str(crawlerParsedQuery['txts'][0])
            #In case some reports not setting the middle boundary (found on 6095): 
            try:
                crawlerParsedForecastMiddleBoundary = str(crawlerParsedQuery['txtm'][0])
            except KeyError:
                crawlerParsedForecastMiddleBoundary = "0"
            crawlerParsedForecastUpperBoundary = str(crawlerParsedQuery['txte'][0])
            
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
            crawlerData.append([crawlerCrDate, crawlerParsedForecastLowerBoundary, crawlerParsedForecastMiddleBoundary, crawlerParsedForecastUpperBoundary, crawlerParsedForecastDataList])

    crawlerLocationReports[location[0]] = crawlerData

crawlerViewDriver.quit()
print crawlerLocationReports