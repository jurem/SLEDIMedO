import hashlib

from requests import get
from requests.exceptions import RequestException
from contextlib import closing
from bs4 import BeautifulSoup
import re
import datetime

from database.dbExecutor import dbExecutor
import sys


NUM_PAGES_TO_CHECK = 1
MAX_HTTP_RETRIES = 10  # set max number of http request retries if a page load fails
BASE_URL = "https://www.tednik.si/tednik"
firstRunBool = False
meseci = {'januar': '1.', 'februar': '2.', 'marec': '3.', 'april': '4.', 'maj': '5.',
          'junij': '6.', 'julij': '7.', 'avgust': '8.', 'september': '9.',
'oktober': '10.', 'november': '11.', 'december': '12.'}




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
parent_link = ("https://www.tednik.si/tednik")

def uniformDateStr(dateStr, inputDateFromat=""):
    if inputDateFromat == "":
        inputDateFromat = "%d.%m.%Y"
    return datetime.datetime.strptime(dateStr, inputDateFromat).strftime("%Y-%m-%d")





def get_text(stran,SOURCE_ID):



    sqlBase = dbExecutor()  # creates a sql database handler class
    todayDateStr = datetime.datetime.now().strftime("%Y-%m-%d")  # today date in the uniform format

    tmp = 0
    soup = BeautifulSoup(simple_get("https://www.tednik.si/tednik?limit=9&start="+str(stran)), "html.parser")
    all_links = soup.find("div",{"class":"t3-content"}).find_all("a")
    for links in all_links:
        if(links.get("href")==None ): continue
        if(re.match("/tednik/+",links.get("href")) and tmp == 0):
            soup = BeautifulSoup(simple_get(parent_link+links.get("href")), "html.parser")
            naslov = soup.find("h1",{"class":"article-title"}).text.strip()
            datum = soup.find("div",{"class":"article-main"}).find("time").text.strip()
            datum = datum.split()
            vse = soup.find("div", {"class": "article-content-main"}).find_all("p")
            vsebina = ""
            for obj in vse:
                vsebina += str(obj.text).strip() + "\n"
            s = ""
            seq = (datum[1]+".", meseci[datum[2].lower()], datum[3])
            datum = uniformDateStr(s.join(seq))
            link = links.get("href")
            hashStr = makeHash(naslov, datum)  # creates article hash from title and dateStr (HASH_VREDNOST)
            date_downloaded = todayDateStr  # date when the article was downloaded

            if sqlBase.getByHash(hashStr) is None:
                description = vsebina
                entry = (datum, naslov, description, date_downloaded, hashStr, link, SOURCE_ID)
                sqlBase.insertOne(entry)  # insert the article in the database
                print("Inserted succesfuly")

        if(tmp < 2):
            tmp += 1
        else: tmp =0
def get_articles( SOURCE_ID):
    stevilka_strani = 0
    now = datetime.datetime.now()
    now = now.year
    get_text(stevilka_strani, SOURCE_ID)
    pagesChecked = 0
    while True:
        pagesChecked += 1
        stevilka_strani+=9
        get_text(stevilka_strani,SOURCE_ID)
        if not firstRunBool and pagesChecked >= NUM_PAGES_TO_CHECK:
            break

def main():
    get_articles("Štajerski tednik")


if __name__ == '__main__':
    # checks if the second argument is provided and is equal to "-F" - means first run
    if len(sys.argv) == 2 and sys.argv[1] == "-F":
        firstRunBool = True

    print ("Add -F as the command line argument to execute first run command - downloads the whole history of articles from the page.")

    main()