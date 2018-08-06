# -*- coding: utf-8 -*-

import bs4 as bs
import requests
import re
import hashlib
import os.path
import sys
import datetime
from database.dbExecutor import dbExecutor

import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning) # disabeled ssl certificate so it shows warnings

SOURCE_ID = "UNI-LJ"       # source identifier
NUM_PAGES_TO_CHECK = 1     # how many pages will to check evey day for new articles
NUM_ARTICLES_TO_CHECK = 20 # how many articles to check every day
MAX_HTTP_RETRIES = 10      # set max number of http request retries if a page load fails
DEBUG = True
BASE_URL = "https://www.uni-lj.si"

MAX_YEAR = 2007

firstRunBool = False       # import all the articles that exist if true; overrides NUM_PAGES_TO_CHECK

# makes a sha1 hash out of title and date strings
# returns string hash
def makeHash(articleTitle, dateStr):
    hash_object = hashlib.sha1((articleTitle+dateStr).encode("utf-8"))
    return hash_object.hexdigest()

# navigates to the given link and extracts the article description
def getArticleDescr(session, link):
    resp = session.get(link, verify=False)
    soup = bs.BeautifulSoup(resp.text, "html.parser")

    # get just the text (not javascript code)
    [x.extract() for x in soup.find_all('script')]
    paragraphs = [paragraph.text+"\n" for paragraph in soup.find("div", id="text-content-container").find_all("p", class_=None)]
    rez = ""
    for p in paragraphs:
        rez += p
    return rez

# creates a uniform date string out of the input @dateStr and date format @inputDateFromat
def uniformDateStr(dateStr, inputDateFromat=""):
    if inputDateFromat == "":
        inputDateFromat = "%d.%m.%Y"
    return datetime.datetime.strptime(dateStr, inputDateFromat).strftime("%Y-%m-%d")


def main():
    articlesChecked = 0
    articlesDownloaded = 0  # number of downloaded articles
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

        finishedBool = False

        for yearNum in range(yearInt, MAX_YEAR-1, -1):
            print ("Checking year:", yearNum)
            pagelink = BASE_URL+"/aktualno/novice/leto_"+str(yearNum)
            # try: 
            pagesChecked += 1

            resp = s.get(pagelink, verify=False)

            soup = bs.BeautifulSoup(resp.text, "html.parser")

            articles = soup.find("ul", class_="news-list").find_all("li")

            for article in articles:
                articlesChecked += 1

                title = article.find("span", class_="news-title").text
                link = BASE_URL+article.find("span", class_="news-title").find("a")["href"]
                dateStr = article.find("span", class_="news-date").text
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

                if DEBUG and articlesChecked % 5 == 0:
                    print ("Checked:", articlesChecked, "articles. Downloaded:", articlesDownloaded, "new articles.")

                if firstRunBool and articlesChecked >= NUM_ARTICLES_TO_CHECK:
                    finishedBool = True
                    break

            if finishedBool: break

            # except Exception as e:
            #     print (e)

    print ("Downloaded:", articlesDownloaded, "new articles.")


if __name__ == '__main__':
    # checks if the second argument is provided and is equal to "-F" - means first run
    if len(sys.argv) == 2:
        if sys.argv[1] == "-F":
            firstRunBool = True
        else:
            firstRunBool = False

    print ("Add -F as the command line argument to execute first run command - downloads the whole history of articles from the page.")

    main()