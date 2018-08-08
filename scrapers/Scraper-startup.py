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

"""
    no need to check multiple pages, every article link is on the same page.
"""

SOURCE_ID = "STARTUP"
NUMBER_ARTICLES_TO_CHECK = 15
MAX_HTTP_RETRIES = 10   # set max number of http request retries if a page load fails
BASE_URL = "https://www.startup.si"
POSTS_URL = BASE_URL+"/sl-si/novice"

firstRunBool = False

logger = loadLogger(SOURCE_ID)

def makeHash(articleTitle, dateStr):
    hash_object = hashlib.sha1((articleTitle+dateStr).encode('utf-8'))
    return hash_object.hexdigest()

# parse date from html
def parseDate(toParseStr):
    dateRegex = ".*?(\\d{1,2}\\.\\d{1,2}\\.\\d{4}).*?"
    dateResult = re.search(dateRegex, toParseStr, re.M|re.U|re.I)
    if dateResult is None:
        logger.error("Date not specified/page is different")
        return None
    return dateResult.group(1)

# navigates to the given link and extracts the article description
def getArticleDescrAndDate(session, link):
    resp = session.get(link)
    soup = bs.BeautifulSoup(resp.text, "html.parser")
    description = soup.find("div", class_="news-html").text
    dateStr = parseDate(soup.find("div", class_="news-wrapper").find("div", class_="date-author").text)
    return (description, dateStr)

# gets the news from "Pretekle novice" section of the page
def getArchivedNews(session, soup, articlesList):
    linkGroup = soup.find_all("div", class_="n-link-group")
    for div in linkGroup:
        articles = div.find_all("div", class_="n-link")
        for article in articles:
            shortDate = article.find("span", class_="n-date").text
            link = BASE_URL+article.find("a")["href"]
            title = article.find("a").text
            articlesList.append((title, link, shortDate))
    logger.info("Found {} articles in the archive.".format(len(articlesList)))
    return articlesList

def getCurrentNews(session, soup, articlesList):
    currNews = soup.find("div", class_="current-news").find_all("div", class_="news-short")
    for article in currNews:
        shortDate = article.find("span", class_="n-date").text
        link = BASE_URL+article.find("a", class_="s-title")["href"]
        title = article.find("a", class_="s-title")
        [x.extract() for x in title.find_all("span")]
        title = title.text
        articlesList.append((title, link, shortDate))
    logger.info("Found {} current articles.".format(len(articlesList)))
    return articlesList

# creates a uniform date string out of the input @dateStr and date format @inputDateFromat
# input format defaulted to: "%d.%m.%Y"
# output format: "%Y-%m-%d" - default database entry format
def uniformDateStr(dateStr, inputDateFromat=""):
    if inputDateFromat == "":
        inputDateFromat = "%d.%m.%Y"
    return datetime.datetime.strptime(dateStr, inputDateFromat).strftime("%Y-%m-%d")


def main():
    articlesChecked = 0     # number of checked articles
    articlesDownloaded = 0  # number of downloaded articles

    # optionally set headers for the http request
    HEADERS = {
        "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36"
    }

    sqlBase = dbExecutor()  # creates a sql database handler class
    todayDateStr = datetime.datetime.now().strftime("%Y-%m-%d") # today date in the uniform format

    with requests.Session() as s:
        # set every http/https request to retry max MAX_HTTP_RETRIES retries before returning an error if there is any complications with loading the page
        s.mount("http://", requests.adapters.HTTPAdapter(max_retries = MAX_HTTP_RETRIES))  # set max retries to: MAX_HTTP_RETRIES
        s.mount("https://", requests.adapters.HTTPAdapter(max_retries = MAX_HTTP_RETRIES)) # set max retries to: MAX_HTTP_RETRIES
        s.headers.update(HEADERS)   # set headers of the session

        resp = s.get(POSTS_URL)
        soup = bs.BeautifulSoup(resp.text, "html.parser")

        articlesList = list()
        articlesList = getCurrentNews(s, soup, articlesList)
        articlesList = getArchivedNews(s, soup, articlesList)

        for article in articlesList:
            articlesChecked += 1
            try:
                title = article[0]
                link = article[1]
                shortDate = article[2]
                hashStr = makeHash(title, shortDate)

                # if article is not yet saved in the database we add it
                if sqlBase.getByHash(hashStr) is None:
                    # get article description/content
                    # logger.debug("Getting article from url: {}".format(link))
                    description, dateStr = getArticleDescrAndDate(s, link)
                    date_created = uniformDateStr(dateStr, "%d.%m.%Y")
                    date_downloaded = todayDateStr                            # date when the article was downloaded

                    # (date_created: string, caption: string, contents: string, date: string, hash: string, url: string, source: string)
                    entry = (date_created, title, description, date_downloaded, hashStr, link, SOURCE_ID)
                    sqlBase.insertOne(entry, True)   # insert the article in the database
                    articlesDownloaded += 1

                if articlesChecked % 5 == 0:
                    logger.info("Checked: {} articles. Downloaded: {} new articles.".format(articlesChecked, articlesDownloaded))
                if not firstRunBool and articlesChecked >= NUMBER_ARTICLES_TO_CHECK:
                    break

            except Exception:
                logger.exception("")
                sys.exit()

    logger.info("Downloaded {} new articles.".format(articlesDownloaded))

if __name__ == '__main__':
    # checks if the second argument is provided and is equal to "-F" - means first run
    if len(sys.argv) == 2 and sys.argv[1] == "-F":
        firstRunBool = True

    print ("Add -F as the command line argument to execute first run command - downloads the whole history of articles from the page.")

    main()