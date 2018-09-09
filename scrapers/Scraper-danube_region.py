import hashlib

import requests
from requests import get
from requests.exceptions import RequestException
from contextlib import closing
from bs4 import BeautifulSoup
import re
import datetime
import os
import weakref
from scrapers.database.dbExecutor import dbExecutor
import sys


NUM_PAGES_TO_CHECK = 10
MAX_HTTP_RETRIES = 10  # set max number of http request retries if a page load fails
firstRunBool = False
meseci = {'January,': '1.', 'February,': '2.', 'March,': '3.', 'April,': '4.', 'May,': '5.',
          'June,': '6.', 'July,': '7.', 'August,': '8.', 'September,': '9.',
'October,': '10.', 'November,': '11.', 'December,': '12.'}



def makeHash(articleTitle, dateStr):
    hash_object = hashlib.sha1((articleTitle+dateStr).encode("utf-8"))

    return hash_object.hexdigest()

def simple_get(url):


    try:
        with closing(get(url, stream=True)) as resp:
            if is_good_response(resp):
                return resp.content
            else:
                return None

    except RequestException as e:
        log_error('Error during requests to {0} : {1}'.format(url, str(e)))
        return None

def is_good_response(resp):
    """
    Returns True if the response seems to be HTML, False otherwise.
    """
    content_type = resp.headers['Content-Type'].lower()
    return (resp.status_code == 200
            and content_type is not None
            and content_type.find('html') > -1)


def log_error(e):

    print(e)


clanki = []
parent_link = ("http://www.danube-region.eu")

def uniformDateStr(dateStr, inputDateFromat=""):
    if inputDateFromat == "":
        inputDateFromat = "%d.%m.%Y"
    return datetime.datetime.strptime(dateStr, inputDateFromat).strftime("%Y-%m-%d")





def get_text(stran,SOURCE_ID):



    sqlBase = dbExecutor()  # creates a sql database handler class
    todayDateStr = datetime.datetime.now().strftime("%Y-%m-%d")  # today date in the uniform format


    soup = BeautifulSoup(simple_get("http://www.danube-region.eu/communication/news?start="+str(stran)), "html.parser")
    all_links =  soup.find("main",{"id":"content"}).find_all("a")
    for links in all_links:
        if(links.get("href")==None): continue
        if(re.match("/communication/news/+",links.get("href"))):
            soup = BeautifulSoup(simple_get(parent_link+links.get("href")), "html.parser")
            naslov = soup.find("div",{"class","page-header"}).find("h2").text.strip().split("\n")[0]
            datum = soup.find("dd",{"class":"published"}).text.split(":")[1].split()
            s=""
            seq = (datum[0]+".", meseci[datum[1]+","], datum[2])
            datum = uniformDateStr(s.join(seq))

            vse = soup.find("div",{"class","item-page"}).find_all("p")
            vsebina=""
            for p in vse:
                vsebina += p.text.strip()

            link = links.get("href")
            hashStr = makeHash(naslov, datum)  # creates article hash from title and dateStr (HASH_VREDNOST)
            date_downloaded = todayDateStr  # date when the article was downloaded
            if sqlBase.getByHash(hashStr) is None:
                # get article description/content
                description = vsebina
                # (date_created: string, caption: string, contents: string, date: string, hash: string, url: string, source: string)
                entry = (datum, naslov, description, date_downloaded, hashStr, link, SOURCE_ID)
                sqlBase.insertOne(entry)  # insert the article in the database
                print("Inserted succesfuly")

def get_articles( SOURCE_ID):
    stevilka_strani = 0
    now = datetime.datetime.now()
    now = now.year
    get_text(stevilka_strani, SOURCE_ID)
    pagesChecked = 0
    while True:
        pagesChecked += 1
        stevilka_strani+=12
        get_text(stevilka_strani,SOURCE_ID)
        if not firstRunBool and pagesChecked >= NUM_PAGES_TO_CHECK and pagesChecked < 100: #ne rabimo pregledati vseh 400 strnai, ker gre nazaj do leta 2005
            break

def main():
    get_articles("Danube region")


if __name__ == '__main__':
    # checks if the second argument is provided and is equal to "-F" - means first run
    if len(sys.argv) == 2 and sys.argv[1] == "-F":
        firstRunBool = True

    print ("Add -F as the command line argument to execute first run command - downloads the whole history of articles from the page.")

    main()