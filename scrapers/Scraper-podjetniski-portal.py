# -*- coding: utf-8 -*-

import bs4 as bs
import requests
import re
import hashlib
import os.path
import sys
import datetime
from logLoader import loadLogger, setLoggerLevel
from database.dbExecutor import dbExecutor

SOURCE_ID = "PODJ-PORTAL"  # source identifier
NUM_PAGES_TO_CHECK = 1 # how many pages will we check evey day for new articles
MAX_HTTP_RETRIES = 10  # set max number of http request retries if a page load fails
BASE_URL = "https://www.podjetniski-portal.si"
POSTS_URL = BASE_URL+"/index.php?t=news&l=sl&year="

MAX_YEAR = 2008
    
firstRunBool = False   # import all the articles that exist if true; overrides NUM_PAGES_TO_CHECK

logger = loadLogger(SOURCE_ID)
setLoggerLevel(logger, "INFO")

# makes a sha1 hash out of title and date strings
# returns string hash
def makeHash(articleTitle, dateStr):
    hash_object = hashlib.sha1((articleTitle+dateStr).encode("utf-8"))
    return hash_object.hexdigest()

# navigates to the given link and extracts the article description
def getArticleDescr(session, link):
    resp = session.get(link)
    soup = bs.BeautifulSoup(resp.text, "html.parser")
    return soup.find("section", class_="content").text

# creates a uniform date string out of the input @dateStr and date format @inputDateFromat
def uniformDateStr(dateStr, inputDateFromat=""):
    if inputDateFromat == "":
        inputDateFromat = "%d.%m.%Y"
    return datetime.datetime.strptime(dateStr, inputDateFromat).strftime("%Y-%m-%d")


def main():
    articlesChecked = 0
    articlesDownloaded = 0  # number of downloaded articles

    sqlBase = dbExecutor()  # creates a sql database handler class
    todayDateStr = datetime.datetime.now().strftime("%Y-%m-%d") # today date in the uniform format
    yearInt = datetime.datetime.now().year

    # optionally set headers for the http request
    HEADERS = {
        "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36"
    }

    with requests.Session() as s:
        # set every http/https request to retry max MAX_HTTP_RETRIES retries before returning an error if there is any complications with loading the page
        s.mount("http://", requests.adapters.HTTPAdapter(max_retries = MAX_HTTP_RETRIES))  # set max retries to: MAX_HTTP_RETRIES
        s.mount("https://", requests.adapters.HTTPAdapter(max_retries = MAX_HTTP_RETRIES)) # set max retries to: MAX_HTTP_RETRIES
        s.headers.update(HEADERS)   # set headers of the session

        maxYearToCheck = MAX_YEAR-1
        if not firstRunBool:
            maxYearToCheck = yearInt-1
        for yearNum in range(yearInt, maxYearToCheck, -1):
            logger.info("Checking year: {}".format(yearNum))

            yearPageLink = POSTS_URL+str(yearNum)

            try: 
                resp = s.get(yearPageLink)
                soup = bs.BeautifulSoup(resp.text, "html.parser")

                articleListings = soup.find("ul", class_="newsList").find_all("li")

                for article in articleListings:
                    articlesChecked += 1

                    title = article.find("a").text
                    link = BASE_URL+"/"+article.find("a")["href"]
                    dateStr = article.find("span", class_="date").text.strip(" ")
                    hashStr = makeHash(title, dateStr)

                    logger.debug("TITLE: {}".format(title.encode("utf-8")))
                    logger.debug("TITLE: {}".format(link))
                    logger.debug("DATE: {}".format(dateStr))

                    date_created = uniformDateStr(dateStr, "%d.%m.%Y") # date when the article was published on the page
                    date_downloaded = todayDateStr                       # date when the article was downloaded

                    # if article is not yet saved in the database we add it
                    if sqlBase.getByHash(hashStr) is None:
                        # get article description/content
                        description = getArticleDescr(s, link)

                        # (date_created: string, caption: string, contents: string, date: string, hash: string, url: string, source: string)
                        entry = (date_created, title, description, date_downloaded, hashStr, link, SOURCE_ID)
                        sqlBase.insertOne(entry, True)   # insert the article in the database
                        articlesDownloaded += 1

                    if articlesChecked % 5 == 0:
                        logger.info("Checked: {} articles. Downloaded: {} new articles.".format(articlesChecked, articlesDownloaded))

            except Exception:
                logger.error("Url on which the error occured: {}".format(resp.url))
                logger.exception("")
                sys.exit()

    logger.info("Downloaded {} new articles.".format(articlesDownloaded))


if __name__ == '__main__':
    # checks if the second argument is provided and is equal to "-F" - means first run
    if len(sys.argv) == 2 and sys.argv[1] == "-F":
        firstRunBool = True

    print ("Add -F as the command line argument to execute first run command - downloads the whole history of articles from the page.")

    main()