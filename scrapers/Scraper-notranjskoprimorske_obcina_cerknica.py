import hashlib

from requests import get
from requests.exceptions import RequestException
from contextlib import closing
from bs4 import BeautifulSoup
import re
import datetime

from database.dbExecutor import dbExecutor
import sys


NUM_PAGES_TO_CHECK = 10
firstRunBool = False
meseci = {'januar': '1.', 'februar': '2.', 'marec': '3.', 'april': '4.', 'maj': '5.',
          'junij': '6.', 'julij': '7.', 'avgust': '8.', 'september': '9.',
'oktober': '10.', 'november': '11.', 'december': '12.'}


def makeHash(articleTitle, dateStr):
    hash_object = hashlib.sha1((articleTitle+dateStr).encode("utf-8"))

    return hash_object.hexdigest()

def simple_get(url):
    """
    Attempts to get the content at `url` by making an HTTP GET request.
    If the content-type of response is some kind of HTML/XML, return the
    text content, otherwise return None.
    """
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


parent_link = ("http://notranjskoprimorske.si/kategorije/vse-novice/")

def uniformDateStr(dateStr, inputDateFromat=""):
    if inputDateFromat == "":
        inputDateFromat = "%d.%m.%Y"
    return datetime.datetime.strptime(dateStr, inputDateFromat).strftime("%Y-%m-%d")





def get_text(stran,SOURCE_ID):
    sqlBase = dbExecutor()  # creates a sql database handler class
    todayDateStr = datetime.datetime.now().strftime("%Y-%m-%d")  # today date in the uniform format
    soup = BeautifulSoup(simple_get("http://notranjskoprimorske.si/kategorije/vse-novice/page/"+str(stran)), "html.parser")
    all_links = soup.find_all("a")
    tmp = 0
    for links in all_links:
        if(links.get("href")==None): continue
        if(re.match("http://notranjskoprimorske.si/[0-9][0-9][0-9][0-9]/+",links.get("href")) and tmp == 0):
            #print("----------------------")
            soup = BeautifulSoup(simple_get(links.get("href")), "html.parser")
            naslov = soup.find("h1",{"class":"entry-title"}).text
            datum =  soup.find("span",{"class":"td-post-date"}).find("time").text.split()
            s=""
            seq = (datum[1], meseci[datum[2]], datum[3])
            datum = uniformDateStr(s.join(seq))

            vse = soup.find("div", {"class": "td-post-content"}).find_all("p")
            vsebina = ""
            for obj in vse:
                vsebina += str(obj.text).strip() + "\n"
            link = links.get("href")
            hashStr = makeHash(naslov, datum)  # creates article hash from title and dateStr (HASH_VREDNOST)
            date_downloaded = todayDateStr  # date when the article was downloaded

            if sqlBase.getByHash(hashStr) is None:
                description = vsebina
                entry = (datum, naslov, description, date_downloaded, hashStr, link, SOURCE_ID)
                sqlBase.insertOne(entry)  # insert the article in the database
                print("Inserted succesfuly")

        if (tmp < 1):
            tmp += 1
        else:
            tmp = 0

def get_articles( SOURCE_ID):
    stevilka_strani = 1
    now = datetime.datetime.now()
    get_text(stevilka_strani, SOURCE_ID)
    pagesChecked = 1
    while True:
        pagesChecked += 1
        print(stevilka_strani)
        stevilka_strani+=1
        get_text(stevilka_strani,SOURCE_ID)
        if not firstRunBool and pagesChecked >= NUM_PAGES_TO_CHECK:
            break

def main():
    get_articles("Notranjskeprimorske-Občina_Cerknica")


if __name__ == '__main__':
    # checks if the second argument is provided and is equal to "-F" - means first run
    if len(sys.argv) == 2 and sys.argv[1] == "-F":
        firstRunBool = True

    print ("Add -F as the command line argument to execute first run command - downloads the whole history of articles from the page.")

    main()