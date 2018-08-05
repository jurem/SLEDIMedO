# -*- coding: utf-8 -*-

import bs4 as bs
import requests
import re
import hashlib
import os.path
import sys # for arguments
import datetime
from database.dbExecutor import dbExecutor

"""
    no need to check multiple pages, every article link is on the same page.
"""

SOURCE_ID = "KOPER"
NUMBER_ARTICLES_TO_CHECK = 15
MAX_HTTP_RETRIES = 10   # set max number of http request retries if a page load fails
BASE_URL = "http://www.koper.si"
DEBUG = True

firstRunBool = False
    
def makeHash(articleTitle, dateStr):
    hash_object = hashlib.sha1((articleTitle+dateStr).encode('utf-8'))
    return hash_object.hexdigest()

# navigates to the given link and extracts the article description
def getArticleDescr(session, link):
    resp = session.get(link)
    soup = bs.BeautifulSoup(resp.text, "html.parser")
    return soup.find("div", style="margin-bottom:20px;").text

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

        resp = s.get(BASE_URL+"/index.php?page=newsplus&item=295&showall=1")
        soup = bs.BeautifulSoup(resp.text, "html.parser")

        articles = soup.find("td", class_="content").find_all("td", style="padding-left:5px;padding-right:20px;")

        for article in articles:
            articlesChecked += 1
            try:
                title = article.find("span", class_="javnost").text
                link = BASE_URL+"/"+article.find("div", class_="preberi_vec").find("a")["href"]
                dateStr = article.find("span", class_="datum").text
                hashStr = makeHash(title, dateStr)
                # print ("title:\n", title, "link:\n", link, "dataStr:\n", dateStr, "hash:\n", hashStr)

                # print ("date created:", dateStr)
                date_created = uniformDateStr(dateStr, "%d.%m.%Y, %H:%M") # date when the article was published on the page
                date_downloaded = todayDateStr                       # date when the article was downloaded


                # if article is not yet saved in the database we add it
                if sqlBase.getByHash(hashStr) is None:
                    # get article description/content
                    description = getArticleDescr(s, link)

                    # (date_created: string, caption: string, contents: string, date: string, hash: string, url: string, source: string)
                    entry = (date_created, title, description, date_downloaded, hashStr, link, SOURCE_ID)
                    sqlBase.insertOne(entry, True)   # insert the article in the database
                    articlesDownloaded += 1

                if DEBUG and articlesChecked % 5 == 0:
                    print ("Checked:", articlesChecked, "articles. Downloaded:", articlesDownloaded, "new articles.")
                if not firstRunBool and articlesChecked >= NUMBER_ARTICLES_TO_CHECK:
                    break

            except Exception as e:
                print (e)


    print ("Downloaded:", articlesDownloaded, "new articles.")
    # print (sqlBase.getById(2))

if __name__ == '__main__':
    # checks if the second argument is provided and is equal to "-F" - means first run
    if len(sys.argv) == 2:
        if sys.argv[1] == "-F":
            firstRunBool = True
        else:
            firstRunBool = False

    print ("Add -F as the command line argument to execute first run command - downloads the whole history of articles from the page.")

    main()