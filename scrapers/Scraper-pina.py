# -*- coding: utf-8 -*-

import bs4 as bs
import requests
import re
import hashlib
import os.path
import sys
import datetime
from logLoader import loadLogger
from database.dbExecutor import dbExecutor

SOURCE_ID = "PINA"      # source identifier
NUM_PAGES_TO_CHECK = 3  # how many pages will we check evey day for new articles
MAX_HTTP_RETRIES = 10   # set max number of http request retries if a page load fails
BASE_URL = "http://www.pina.si"

MAX_YEAR = 2015

firstRunBool = False    # import all the articles that exist if true; overrides NUM_PAGES_TO_CHECK

logger = loadLogger(SOURCE_ID)

# makes a sha1 hash out of title and date strings
# returns string hash
def makeHash(articleTitle, dateStr):
    hash_object = hashlib.sha1((articleTitle+dateStr).encode("utf-8"))
    return hash_object.hexdigest()

# navigates to the given link and extracts the article description
def getArticleDescr(session, link):
    resp = session.get(link)
    soup = bs.BeautifulSoup(resp.text, "html.parser")
    # print (soup.encode("utf-8"))
    description = soup.find("article", class_="post")
    # print (description.encode("utf-8"))
    if description is None:
        logger.error("Possible error: cannot find article description.")
        return ""
    else:
        return description.text

# creates a uniform date string out of the input @dateStr and date format @inputDateFromat
def uniformDateStr(dateStr, inputDateFromat=""):
    if inputDateFromat == "":
        inputDateFromat = "%d.%m.%Y"
    return datetime.datetime.strptime(dateStr, inputDateFromat).strftime("%Y-%m-%d")


def main():
    articlesChecked = 0
    articlesDownloaded = 0  # number of downloaded articles
    pageNum = 0
    pagesChecked = 0

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

        for yearNum in range(yearInt, MAX_YEAR-1, -1):
            nextPageLink = ""
            pagelink = BASE_URL+"/"+str(yearNum)
            while "javascript:void(0);" not in nextPageLink:
                try: 
                    if not firstRunBool and pagesChecked >= NUM_PAGES_TO_CHECK:
                        break
                    pageNum += 1
                    pagesChecked += 1
                    resp = s.get(pagelink)
                    soup = bs.BeautifulSoup(resp.text, "html.parser")

                    articles = soup.find_all("article", class_="post")

                    for article in articles:
                        articlesChecked += 1

                        title = article.find("h2", class_="entry-title").text
                        link = article.find("h2", class_="entry-title").find("a")["href"]
                        dateStr = article.find("time", class_="entry-date").text
                        hashStr = makeHash(title, dateStr)

                        date_created = uniformDateStr(dateStr, "%d.%m.%Y") # date when the article was published on the page
                        date_downloaded = todayDateStr                     # date when the article was downloaded

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

                    nextPageLink = soup.find("div", class_="pagination loop-pagination").find_all("a")[1]["href"]
                    pagelink = nextPageLink

                except Exception as e:
                    logger.exception("")

    logger.info("Downloaded {} new articles.".format(articlesDownloaded))

if __name__ == '__main__':
    # checks if the second argument is provided and is equal to "-F" - means first run
    if len(sys.argv) == 2 and sys.argv[1] == "-F":
        firstRunBool = True

    print ("Add -F as the command line argument to execute first run command - downloads the whole history of articles from the page.")

    main()