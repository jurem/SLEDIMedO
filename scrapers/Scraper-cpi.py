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

SOURCE_ID = "CPI"      # source identifier
MAX_HTTP_RETRIES = 10   # set max number of http request retries if a page load fails
BASE_URL = "http://www.cpi.si"
URLS_TO_CHECK = [BASE_URL+"/mednarodno-sodelovanje/"+i for i in ["projekti-eu-komisije.aspx", "erasmus-.aspx"]]


logger = loadLogger(SOURCE_ID)

# makes a sha1 hash out of title and date strings
# returns string hash
def makeHash(articleTitle):
    hash_object = hashlib.sha1((articleTitle).encode("utf-8"))
    return hash_object.hexdigest()

# navigates to the given link and extracts the article description
def getArticleDescr(session, link):
    resp = session.get(link)
    soup = bs.BeautifulSoup(resp.text, "html.parser")
    # print (soup.encode("utf-8"))
    description = soup.find("div", class_="freetext")
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

    sqlBase = dbExecutor()  # creates a sql database handler class
    todayDateStr = datetime.datetime.now().strftime("%Y-%m-%d") # today date in the uniform format

    # optionally set headers for the http request
    HEADERS = {
        "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36"
    }

    with requests.Session() as s:
        # set every http/https request to retry max MAX_HTTP_RETRIES retries before returning an error if there is any complications with loading the page
        s.mount("http://", requests.adapters.HTTPAdapter(max_retries = MAX_HTTP_RETRIES))  # set max retries to: MAX_HTTP_RETRIES
        s.mount("https://", requests.adapters.HTTPAdapter(max_retries = MAX_HTTP_RETRIES)) # set max retries to: MAX_HTTP_RETRIES
        s.headers.update(HEADERS)   # set headers of the session

        for url in URLS_TO_CHECK:
            logger.info("Checking page: {}".format(url))
            resp = s.get(url)
            soup = bs.BeautifulSoup(resp.text, "html.parser")

            articles = soup.find("div", class_="freetext").find_all("li")
            for article in articles:
                articlesChecked += 1

                try:
                    link = BASE_URL+article.find("a")["href"]
                    title = article.text.strip()
                    hashStr = makeHash(title)

                    date_downloaded = todayDateStr                     # date when the article was downloaded
                    date_created = None

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


                except Exception as e:
                    logger.error("Url on which the error occured: {}".format(resp.url))
                    logger.exception("")
                    sys.exit()

    logger.info("Downloaded {} new articles.".format(articlesDownloaded))

if __name__ == '__main__':
    print ("No need to add -F because the page is small.")
    main()