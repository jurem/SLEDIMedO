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

SOURCE_ID = "GZS"      # source identifier
NUM_PAGES_TO_CHECK = 1 # how many pages will we check evey day for new articles
MAX_HTTP_RETRIES = 10  # set max number of http request retries if a page load fails
BASE_URL = "https://www.gzs.si"
    
firstRunBool = False   # import all the articles that exist if true; overrides NUM_PAGES_TO_CHECK

logger = loadLogger(SOURCE_ID)

# makes a sha1 hash string from atricle title and date string
# returns string hash
def makeHash(articleTitle, dateStr):
    hash_object = hashlib.sha1((articleTitle+dateStr).encode("utf-8"))
    return hash_object.hexdigest()

# parse date from html
def parseDate(toParseStr):
    month = {
        "januar": "01", "februar": "02", "marec": "03", "april": "04", "maj": "05",
        "junij": "06", "julij": "07", "avgust": "08", "september": "09",
        "oktober": "10", "november": "11", "december": "12"
    }
    dateRegex = "Datum novice: (\\d{1,2})\\. (\\w+) (\\d{4})"
    dateResult = re.search(dateRegex, toParseStr, re.M|re.U|re.I)
    try:
        day = dateResult.group(1)
        monthStr = dateResult.group(2)
        year = dateResult.group(3)
        dateStr = str(year)+"-"+month[monthStr]+"-"+str(day)
        return dateStr
        # print (dateStr)
    except IndexError as e:
        logger.exception("Date format is different.")
        return None

# navigates to the given link and extracts the article description
# returns article description string
def getArticleDescr(session, link):
    resp = session.get(link)
    soup = bs.BeautifulSoup(resp.text, "html.parser")
    return soup.find("div", class_="content noheight").text

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
        # set every http/https request to retry max MAX_HTTP_RETRIES retries before returning an error if there is any complications with loading the page
        s.mount("http://", requests.adapters.HTTPAdapter(max_retries = MAX_HTTP_RETRIES))  # set max retries to: MAX_HTTP_RETRIES
        s.mount("https://", requests.adapters.HTTPAdapter(max_retries = MAX_HTTP_RETRIES)) # set max retries to: MAX_HTTP_RETRIES
        s.headers.update(HEADERS)   # set headers of the session

        resp = s.get(BASE_URL+"/mediji/Novice/ArticlePage/1")
        soup = bs.BeautifulSoup(resp.text, "html.parser")
        logger.info("Checking page 1")

        lastPageNum = int(soup.find("div", class_="pager").find_all("a")[-2].text)

        for pageNum in range(2, lastPageNum+1, 1):
            try:
                pagesChecked += 1
                # find all ~15 articles on current page
                articles = soup.find_all("div", class_="article")

                for article in articles:
                    articlesChecked += 1

                    title = article.find("h1", class_="heading").find("a").text             # finds article title
                    link = article.find("h1", class_="heading").find("a")["href"] # finds article http link
                    dateStr = article.find("div", class_="metadata")          # finds article date (DATUM_VNOSA)
                    [x.extract() for x in dateStr.find_all('span', class_="pull-right")]
                    date_created = parseDate(dateStr.text)
                    hashStr = makeHash(title, date_created)                                # creates article hash from title and dateStr (HASH_VREDNOST)
                    
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

                # firstRunBool = True # DEBUG!
                if not firstRunBool and pagesChecked >= NUM_PAGES_TO_CHECK:
                    break

                # find next page
                resp = s.get(BASE_URL+"/mediji/Novice/ArticlePage/"+str(pageNum))
                soup = bs.BeautifulSoup(resp.text, "html.parser")
                logger.info("Checking page: {}".format(pageNum))

                        
            except Exception as e:
                logger.exception("")

    logger.info("Downloaded {} new articles.".format(articlesDownloaded))

# starts main function
if __name__ == '__main__':
    # checks if the second argument is provided and is equal to "-F" - means first run
    if len(sys.argv) == 2 and sys.argv[1] == "-F":
        firstRunBool = True

    print ("Add -F as the command line argument to execute first run command - downloads the whole history of articles from the page.")

    main()