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
    
    html on this page is broken, so the program searches for all
    the links of news and then gets the title, date and content from the
    news subpages - takes more time
    
    TODO: saving encoding is wrong
"""

SOURCE_ID = "ZRSVN"
NUMBER_ARTICLES_TO_CHECK = 30
MAX_HTTP_RETRIES = 10   # set max number of http request retries if a page load fails
BASE_URL = "http://www.zrsvn.si"
DEBUG = True

firstRunBool = False
    
def makeHash(articleTitle, dateStr):
    hash_object = hashlib.sha1((articleTitle+dateStr).encode('utf-8'))
    return hash_object.hexdigest()

def parseDate(toParse):
    for i in toParse:
        # print (i.text)
        regexStr = "(\\d{2}\\.\\d{2}\\.\\d{4}).*?"
        result = re.search(regexStr, i.text, re.M|re.U|re.I)
        if result:
            return result.group(1)
    
    if DEBUG: print (("Date not specified/page is different"))
    return None

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

        pages = [BASE_URL+"/sl/informacija.asp?id_meta_type=54&type_informacij=0",
                 BASE_URL+"/sl/informacija.asp?id_meta_type=68&type_informacij=0"]

        resp = s.get(pages[0])
        soup = bs.BeautifulSoup(resp.text, "html.parser")
        allNewsLinksHtml = soup.find_all("span", class_="vec")
            
        resp = s.get(pages[1])
        soup = bs.BeautifulSoup(resp.text, "html.parser")
        allNewsLinksHtml2 = soup.find_all("span", class_="vec")

        # makes a one list out of two
        # list1: [1,2,3,4]
        # list2: [5,6,7,8]
        # output list: [1,5,2,6,3,7,4,8]
        for num, pg in enumerate(allNewsLinksHtml2):
            allNewsLinksHtml.insert(num*2, pg)
        
        for newsLink in allNewsLinksHtml:
            try:
                articlesChecked += 1

                link = BASE_URL+"/sl/"+newsLink.find("a")["href"]
                resp = s.get(link)
                soup = bs.BeautifulSoup(resp.text, "html.parser")
                subPage = soup.find("div", class_="Vsebina")

                title = subPage.find("h2").text
                dateStr = parseDate(subPage.find_all("p"))
                hashStr = makeHash(title, dateStr)
                description = subPage.text


                # # print ("date created:", dateStr)
                date_created = uniformDateStr(dateStr, "%d.%m.%Y") # date when the article was published on the page
                date_downloaded = todayDateStr                       # date when the article was downloaded


                # if article is not yet saved in the database we add it
                if sqlBase.getByHash(hashStr) is None:
                    # get article description/content

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