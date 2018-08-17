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

SOURCE_ID = "ZADNJENOVICE" # source identifier
NUM_DAYS_TO_CHECK = 1      # how many pages will we check evey day for new articles
MAX_HTTP_RETRIES = 10      # set max number of http request retries if a page load fails

BASE_URL = "http://zadnjenovice.info"
POSTS_URL = BASE_URL+"/dogajanje/novice/"
    
firstRunBool = False       # import all the articles that exist if true; overrides NUM_DAYS_TO_CHECK

logger = loadLogger(SOURCE_ID)

# gets all the archive links that the page offers
def getCalArchiveLinks(session):
    logger.debug("Checking the calendar for all possible links of pages with articles.")
    MONTH_START = 6
    YEAR_START = 2018
    yearInt = int(datetime.datetime.now().year)
    monthInt = int(datetime.datetime.now().month)

    links = list()

    for year in range(YEAR_START, yearInt+1, 1):
        if year == YEAR_START: monthIntStart = MONTH_START
        else: monthIntStart = 1
        monthIntEnd = 13
        if year >= yearInt:
            monthIntEnd =  monthInt+1
        for month in range(monthIntStart, monthIntEnd, 1):
            link = BASE_URL+"/ajax.php?case=calendar&month="+str(month)+"&year="+str(year)
            resp = session.get(link)
            soup = bs.BeautifulSoup(resp.text, "html.parser")
            for a in soup.find_all("a"):
                partOfLink = a["href"]
                if "archive" in partOfLink:
                    links.append(BASE_URL+partOfLink[1:])

    BASE_AJAX_URL = "http://zadnjenovice.info/ajax.php?case=ajax_archive_next_prev"
    linksRez = list()
    for link in reversed(links):
        linksRez.append(BASE_AJAX_URL+"&"+parseAjaxLinks(link)+"&page=")

    return linksRez

# makes a sha1 hash string from atricle title and date string
# returns string hash
def makeHash(articleTitle, dateStr):
    hash_object = hashlib.sha1((articleTitle+dateStr).encode("utf-8"))
    return hash_object.hexdigest()

# get "?d=30&m=6&y=2018" OUT OF STRING
def parseAjaxLinks(toParseStr):
    regexStr = ".*?archive\\?(.+)"
    regexResult = re.search(regexStr, toParseStr, re.M|re.U|re.I)
    # print ("PARSING LINK:", toParseStr)
    try:
        rez = str(regexResult.group(1))
        return rez
    except Exception:
        logger.exception("Page is different")
        return None

# parse date from html
def parseDate(toParseStr):
    dateRegex = ".*?d=(\\d{1,2})&m=(\\d{1,2})&y=(\\d{4}).*?"
    dateResult = re.search(dateRegex, toParseStr, re.M|re.U|re.I)
    try:
        dateStr = str(dateResult.group(3))+"-"+str(dateResult.group(2))+"-"+str(dateResult.group(1))
        return dateStr
    except Exception:
        logger.exception("Date not specified/page is different")
        return None

# navigates to the given link and extracts the article description
# returns article description string
def getArticleDescr(session, link):
    resp = session.get(link)
    soup = bs.BeautifulSoup(resp.text, "html.parser")
    return soup.find("div", class_="article-content paragraph-font").text

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

        archiveLinks = getCalArchiveLinks(s)
        # archiveLinks = ["http://zadnjenovice.info/archive?d=30&m=6&y=2018"] # DEBUG
        if firstRunBool: logger.debug("Number of found days to check: {}".format(len(archiveLinks)))

        # while not on the last page
        for archiveDay, archiveLink in enumerate(archiveLinks):
            pageNum = 0
            articles = "1"  # so that len is not 0
            while len(articles) != 0 and archiveDay < NUM_DAYS_TO_CHECK or firstRunBool:
                pageNum+=1
                try:
                    archiveLinkPage = archiveLink+str(pageNum)
                    logger.info("Downloading page: {}".format(archiveLinkPage))
                    resp = s.get(archiveLinkPage)
                    soup = bs.BeautifulSoup(resp.text, "html.parser")

                    pagesChecked += 1
                    articles = soup.find_all("div", class_="section-news")
                    numberOfFoundArticles = len(articles)
                    logger.debug("Number of found articles: {}".format(numberOfFoundArticles))
                    pageCheckedarticles = 0 # number of checked articles on the current page

                    for article in articles:
                        pageCheckedarticles += 1
                        articlesChecked += 1

                        title = article.find("a", class_="heading-font").text                # finds article title
                        link = BASE_URL+article.find("a", class_="heading-font")["href"][1:] # finds article http link
                        date_created = parseDate(archiveLink)                                # finds article date (DATUM_VNOSA)
                        hashStr = makeHash(title, date_created)                              # creates article hash from title and dateStr (HASH_VREDNOST)

                        date_created = uniformDateStr(date_created, "%Y-%m-%d")
                        date_downloaded = todayDateStr                                       # date when the article was downloaded

                        # if article is not yet saved in the database we add it
                        if sqlBase.getByHash(hashStr) is None:
                            # get article description/content
                            description = getArticleDescr(s, link)

                            # (date_created: string, caption: string, contents: string, date: string, hash: string, url: string, source: string)
                            entry = (date_created, title, description, date_downloaded, hashStr, link, SOURCE_ID)
                            sqlBase.insertOne(entry, True)   # insert the article in the database
                            articlesDownloaded += 1

                        if articlesChecked % 5 == 0 and pageCheckedarticles != numberOfFoundArticles:
                            logger.info("Checked: {}/{} articles, overall {}. Downloaded: {} new articles.".format(pageCheckedarticles,
                                numberOfFoundArticles, articlesChecked, articlesDownloaded))
                    logger.info("Checked: {}/{} articles, overall {}. Downloaded: {} new articles.".format(pageCheckedarticles,
                                numberOfFoundArticles, articlesChecked, articlesDownloaded))

                    # firstRunBool = True # DEBUG!
                    if articles is None:    # no more incrementing of pageNum
                        break
                            
                except Exception:
                    logger.error("Url on which the error occured: {}".format(resp.url))
                    logger.exception("")
                    sys.exit()

    logger.info("Downloaded {} new articles.".format(articlesDownloaded))

# starts main function
if __name__ == '__main__':
    # checks if the second argument is provided and is equal to "-F" - means first run
    if len(sys.argv) == 2 and sys.argv[1] == "-F":
        firstRunBool = True

    print ("Add -F as the command line argument to execute first run command - downloads the whole history of articles from the page.")

    main()