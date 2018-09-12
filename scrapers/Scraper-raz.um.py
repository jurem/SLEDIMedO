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
BASE_URL = "http://raz.um.si/"
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
parent_link = ("http://raz.um.si/")

def uniformDateStr(dateStr, inputDateFromat=""):
    if inputDateFromat == "":
        inputDateFromat = "%d.%m.%Y"
    return datetime.datetime.strptime(dateStr, inputDateFromat).strftime("%Y-%m-%d")





def get_text(stran,SOURCE_ID):



    sqlBase = dbExecutor()  # creates a sql database handler class
    todayDateStr = datetime.datetime.now().strftime("%Y-%m-%d")  # today date in the uniform format


    soup = BeautifulSoup(simple_get("http://raz.um.si/novice-in-dogodki/Strani/default.aspx#"), "html.parser")
    all_links = soup.find_all("a")
    for links in all_links:
        if(links.get("href")==None ): continue
        if(re.match("/novice-in-dogodki/novica/Strani/+",links.get("href"))):
            soup = BeautifulSoup(simple_get(parent_link+links.get("href")), "html.parser")
            naslov = soup.find("div", {"class":"naslov_novice"}).text.strip()
            datum =  soup.find("div", {"class":"year"}).text.strip().split()
            vsebina = soup.find("div", {"class":"teloNovice"}).text.strip()
            datum = uniformDateStr(datum[1])
            link = links.get("href")
            hashStr = makeHash(naslov, datum)  # creates article hash from title and dateStr (HASH_VREDNOST)
            date_downloaded = todayDateStr  # date when the article was downloaded

            if sqlBase.getByHash(hashStr) is None:
                description = vsebina
                entry = (datum, naslov, description, date_downloaded, hashStr, link, SOURCE_ID)
                sqlBase.insertOne(entry)  # insert the article in the database
                print("Inserted succesfuly")

def get_articles( SOURCE_ID):
    stevilka_strani = 0
    now = datetime.datetime.now()
    now = now.year
    get_text(stevilka_strani, SOURCE_ID)

def main():
    get_articles("raz.um")


if __name__ == '__main__':
    # checks if the second argument is provided and is equal to "-F" - means first run
    if len(sys.argv) == 2 and sys.argv[1] == "-F":
        firstRunBool = True

    print ("Add -F as the command line argument to execute first run command - downloads the whole history of articles from the page.")

    main()