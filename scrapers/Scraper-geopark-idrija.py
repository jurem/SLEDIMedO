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
    2 parts:
        part one checks the page /si/novice - multiple pages
        part two check the page /si/dogodki - one page without article date - saves NULL to the database
"""

SOURCE_ID = "GEOPARK-IDRIJA" # source identifier
NUM_PAGES_TO_CHECK = 1       # how many pages will we check evey day for new articles
NUM_ARTICLES_TO_CHECK = 30   # how many pages will we check evey day for new articles
MAX_HTTP_RETRIES = 10        # set max number of http request retries if a page load fails
DEBUG = True                 # print for debugging
BASE_URL = "http://www.geopark-idrija.si"
    
firstRunBool = False         # import all the articles that exist if true; overrides NUM_PAGES_TO_CHECK

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
    dateRegex = "^\\w+,\\s(\\d{2})\\.\\s(\\w+)\\s(\\d{4})"
    dateResult = re.search(dateRegex, toParseStr, re.M|re.U|re.I)
    try:
        day = dateResult.group(1)
        monthStr = dateResult.group(2)
        year = dateResult.group(3)
        dateStr = str(year)+"-"+month[monthStr]+"-"+str(day)
        # print (dateStr)
    except IndexError as e:
        print ("ERROR: wrong date parsing:", e)

    return dateStr

# removes multiple newlines in the string, then removes 
# the start and finishing new lines if they exist
def removeNewLines(text):
    text = re.sub(r'\n\s*\n', '\n\n', text)
    text = text.strip('\n')
    text = text.strip('\t')
    text = text.strip('\r')
    return text

# navigates to the given link and extracts the article descriptionsoup.find("div", class_="c2p").text
# returns article description string
def getArticleDescr(session, link):
    resp = session.get(link)
    soup = bs.BeautifulSoup(resp.text, "html.parser")
    return removeNewLines(soup.find("div", class_="c2p").text)

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

    errorList = list()

    # optionally set headers for the http request
    HEADERS = {
        "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36"
    }

    sqlBase = dbExecutor()  # creates a sql database handler class
    todayDateStr = datetime.datetime.now().strftime("%Y-%m-%d") # today date in the uniform format

    # creates a session
    with requests.Session() as s:
        pageStart = 0    # set at which page (article) to start

        # set every http/https request to retry max MAX_HTTP_RETRIES retries before returning an error if there is any complications with loading the page
        s.mount("http://", requests.adapters.HTTPAdapter(max_retries = MAX_HTTP_RETRIES))  # set max retries to: MAX_HTTP_RETRIES
        s.mount("https://", requests.adapters.HTTPAdapter(max_retries = MAX_HTTP_RETRIES)) # set max retries to: MAX_HTTP_RETRIES
        s.headers.update(HEADERS)   # set headers of the session

        # send get request to the http page (if you need a post request you could also use s.post(...))
        resp = s.get(BASE_URL+"/si/novice/")
        # adds the html text of the http response to the BeautifulSoup parser
        soup = bs.BeautifulSoup(resp.text, "html.parser")

        # find "next page" button link - to import all the news recursive
        try:
            nextPageLink = BASE_URL+"/"+soup.find("div", class_="pager").find_all("a")[-1]["href"]
        except KeyError as e:
            print (e)
            errorList.append(e)

        while nextPageLink != None:
            try:
                pagesChecked += 1
                # find all ~15 articles on current page
                articles = soup.find_all("div", class_="newswrapp")

                for article in articles:
                    articlesChecked += 1

                    textPart = article.find("div", class_="newstext")

                    title = textPart.find("h2").find("a").text           # finds article title
                    link = BASE_URL+textPart.find("h2").find("a")["href"]         # finds article http link
                    date_created = parseDate(textPart.find("div", class_="date").text) # finds article date (DATUM_VNOSA)
                    hashStr = makeHash(title, date_created)                                      # creates article hash from title and dateStr (HASH_VREDNOST)

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


                # find next page
                resp = s.get(nextPageLink)                        # loads next page
                soup = bs.BeautifulSoup(resp.text, "html.parser") # add html text to the soup
                try:
                    nextPageLink = BASE_URL+"/"+soup.find("div", class_="pager").find_all("a")[-1]["href"] # select the "next page" button http link
                except AttributeError as e:
                    nextPageLink = None
                except KeyError as e:
                    nextPageLink = None

                if not firstRunBool and pagesChecked >= NUM_PAGES_TO_CHECK:
                    break
                    
            except Exception as e:
                print (e)

        resp = s.get(BASE_URL+"/si/dogodki/")
        # adds the html text of the http response to the BeautifulSoup parser
        soup = bs.BeautifulSoup(resp.text, "html.parser")


        pagesChecked += 1
        # find all ~15 articles on current page
        articles = soup.find_all("div", class_="newswrapp")

        for article in articles:
            try:
                articlesChecked += 1

                textPart = article.find("div", class_="newstext")

                title = textPart.find("h2").find("a").text            # finds article title
                link = BASE_URL+textPart.find("h2").find("a")["href"] # finds article http link
                date_created = ""                                     # finds article date (DATUM_VNOSA)
                hashStr = makeHash(title, date_created)               # creates article hash from title and dateStr (HASH_VREDNOST)
                date_created = None
                date_downloaded = todayDateStr                        # date when the article was downloaded

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

                if not firstRunBool and articlesChecked >= NUM_ARTICLES_TO_CHECK:
                    break
            except Exception as e:
                print (e)
                errorList.append(e)

    print ("Downloaded:", articlesDownloaded, "new articles.")
    if len(errorList): print ("ERROR LIST: ", errorList)

# starts main function
if __name__ == '__main__':
    # checks if the second argument is provided and is equal to "-F" - means first run
    if len(sys.argv) == 2:
        if sys.argv[1] == "-F":
            firstRunBool = True
        else:
            firstRunBool = False

    print ("Add -F as the command line argument to execute first run command - downloads the whole history of articles from the page.")

    main()