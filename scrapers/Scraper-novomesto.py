# -*- coding: utf-8 -*-

import bs4 as bs
import requests
import re
import hashlib
import os.path
import sys # for arguments
import datetime
from logLoader import loadLogger
from database.dbExecutor import dbExecutor

"""
	TODO: correct database encoding
"""

SOURCE_ID = "NOVOMESTO"   # source identifier
NUM_PAGES_TO_CHECK = 1 # how many pages will we check evey day for new articles
MAX_HTTP_RETRIES = 10  # set max number of http request retries if a page load fails
BASE_URL = "https://www.novomesto.si"
POSTS_URL = BASE_URL+"/dogajanje/novice/"
    
firstRunBool = False   # import all the articles that exist if true; overrides NUM_PAGES_TO_CHECK

logger = loadLogger(SOURCE_ID)

# makes a sha1 hash string from atricle title and date string
# returns string hash
def makeHash(articleTitle, dateStr):
    hash_object = hashlib.sha1((articleTitle+dateStr).encode("utf-8"))
    return hash_object.hexdigest()

# parse date from html
def parseDate(toParseStr):
    dateRegex = ".*?(\\d{2}\\.\\d{2}\\.\\d{4}).*?"
    dateResult = re.search(dateRegex, toParseStr, re.M|re.U|re.I)
    if dateResult is None:
        # raise Exception("Date not specified/page is different")
        logger.error("Date not specified/page is different")
        return None
    return dateResult.group(1)

# navigates to the given link and extracts the article description
# returns article description string
def getArticleDescr(session, link):
    resp = session.get(link)
    soup = bs.BeautifulSoup(resp.text, "html.parser")
    return soup.find("article").text

# creates a uniform date string out of the input @dateStr and date format @inputDateFromat
# input format defaulted to: "%d.%m.%Y"
# output format: "%Y-%m-%d" - default database entry format
def uniformDateStr(dateStr, inputDateFromat=""):
    if inputDateFromat == "":
        inputDateFromat = "%d.%m.%Y"
    return datetime.datetime.strptime(dateStr, inputDateFromat).strftime("%Y-%m-%d")


# main function
def main():
    pagesChecked = 0        # number of checked pages
    articlesChecked = 0     # number of checked articles
    articlesDownloaded = 0  # number of downloaded articles

    # optionally set headers for the http request
    HEADERS = {
        "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36"
    }

    sqlBase = dbExecutor()  # creates a sql database handler class
    todayDateStr = datetime.datetime.now().strftime("%Y-%m-%d") # today date in the uniform format

    # creates a session
    with requests.Session() as s:
        pageNum = 1    # set at which page (article) to start

        # set every http/https request to retry max MAX_HTTP_RETRIES retries before returning an error if there is any complications with loading the page
        s.mount("http://", requests.adapters.HTTPAdapter(max_retries = MAX_HTTP_RETRIES))  # set max retries to: MAX_HTTP_RETRIES
        s.mount("https://", requests.adapters.HTTPAdapter(max_retries = MAX_HTTP_RETRIES)) # set max retries to: MAX_HTTP_RETRIES
        s.headers.update(HEADERS)   # set headers of the session

        resp = s.get(POSTS_URL+str(pageNum))
        soup = bs.BeautifulSoup(resp.text, "html.parser")

        # while not on the last page
        while soup.find("ul", class_="pagination").find("li", class_="next").find("a")["href"] != "#":
            try:
                pagesChecked += 1
                articles = soup.find("ul", class_="news-list news-archive list-group").find_all("li", class_="list-group-item")

                for article in articles:
                    articlesChecked += 1

                    title = article.find("span", class_="title").text               # finds article title
                    link = BASE_URL+article.find("a")["href"]                       # finds article http link
                    dateStr = article.find("span", class_="date").text              # finds article date (DATUM_VNOSA)
                    hashStr = makeHash(title, dateStr)                              # creates article hash from title and dateStr (HASH_VREDNOST)

                    date_created = uniformDateStr(dateStr, "%d. %m. %Y") # date when the article was published on the page
                    date_downloaded = todayDateStr                                  # date when the article was downloaded

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

                # load next page
                pageNum += 1
                nextPageLink = POSTS_URL+str(pageNum)
                resp = s.get(nextPageLink)
                soup = bs.BeautifulSoup(resp.text, "html.parser")

                # firstRunBool = True # DEBUG!
                if not firstRunBool and pagesChecked >= NUM_PAGES_TO_CHECK:
                    break
                        
            except Exception:
                logger.exception("")

    logger.info("Downloaded {} new articles.".format(articlesDownloaded))

# starts main function
if __name__ == '__main__':
    # checks if the second argument is provided and is equal to "-F" - means first run
    if len(sys.argv) == 2 and sys.argv[1] == "-F":
        firstRunBool = True

    print ("Add -F as the command line argument to execute first run command - downloads the whole history of articles from the page.")

    main()