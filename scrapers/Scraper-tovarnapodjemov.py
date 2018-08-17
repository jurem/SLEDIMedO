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
    no need to check multiple pages, every article link is on the same page.
"""

SOURCE_ID = "TOVARNAPODJEMOV"
NUMBER_ARTICLES_TO_CHECK = 15
MAX_HTTP_RETRIES = 10   # set max number of http request retries if a page load fails
BASE_URL = "https://www.tovarnapodjemov.org"
POSTS_URL = BASE_URL+"/Blog/Vsi.aspx?id_menu=157"

firstRunBool = False

logger = loadLogger(SOURCE_ID)

def makeHash(articleTitle, dateStr):
    hash_object = hashlib.sha1((articleTitle+dateStr).encode('utf-8'))
    return hash_object.hexdigest()

# navigates to the given link and extracts the article description
def getArticleDescr(session, link):
    resp = session.get(link)
    soup = bs.BeautifulSoup(resp.text, "html.parser")
    return soup.find("div", id="ctl00_ContentPlaceHolder1_pnlText").text

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

        articlesTitle = soup.find("div", class_="main", id="ResizeBody").find_all("div", class_="blogPostTitle")
        articlesDate = soup.find("div", class_="main", id="ResizeBody").find_all("div", class_="blogPostDate")
        if len(articlesTitle) != len(articlesDate):
            logger.error("Page is different: number of title and date <div> tags is different.")
            sys.exit()

        for num in range(len(articlesTitle)):
            articlesChecked += 1
            try:
                title = articlesTitle[num].find("h2").text
                link = BASE_URL+articlesTitle[num].find("h2").find("a")["href"][2:]
                logger.debug("TITLE: {}\nLINK: {}".format(title.encode("utf-8"), link))
                dateStr = articlesDate[num].text.split(" |")[0]
                hashStr = makeHash(title, dateStr)
                # print ("title:\n", title, "link:\n", link, "dataStr:\n", dateStr, "hash:\n", hashStr)

                date_created = uniformDateStr(dateStr, "%d.%m.%y") # date when the article was published on the page
                logger.debug("DATE: {}".format(date_created))
                date_downloaded = todayDateStr                            # date when the article was downloaded


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
                if not firstRunBool and articlesChecked >= NUMBER_ARTICLES_TO_CHECK:
                    break

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