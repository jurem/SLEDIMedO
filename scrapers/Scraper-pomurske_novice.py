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
firstRunBool = False
meseci = {'januar,': '1.', 'februar,': '2.', 'marec,': '3.', 'april,': '4.', 'maj,': '5.',
          'junij,': '6.', 'julij,': '7.', 'avgust,': '8.', 'september,': '9.',
'oktober,': '10.', 'november,': '11.', 'december,': '12.'}



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
parent_link = ("http://pomurske-novice.si")

def uniformDateStr(dateStr, inputDateFromat=""):
    if inputDateFromat == "":
        inputDateFromat = "%d,%m.%Y"
    return datetime.datetime.strptime(dateStr, inputDateFromat).strftime("%Y-%m-%d")





def get_text(stran,SOURCE_ID):



    sqlBase = dbExecutor()  # creates a sql database handler class
    todayDateStr = datetime.datetime.now().strftime("%Y-%m-%d")  # today date in the uniform format


    soup = BeautifulSoup(simple_get("http://pomurske-novice.si/rubrika/pomurje/page/"+str(stran)), "html.parser")
    all_links = soup.find("div",{"class":"td-ss-main-content"}).find_all("a")

    tmp=0
    for links in all_links:
        if(links.get("href")==None): continue
        if(re.match("http://pomurske-novice.si/+",links.get("href")) and tmp ==0 and not re.match("http://pomurske-novice.si/rubrika/+",links.get("href"))):
            print(links.get("href"))
            try:
                soup = BeautifulSoup(simple_get(links.get("href")), "html.parser")
                naslov = soup.find("h1", {"class": "entry-title"}).text.strip()

                if(soup.find("time") == None ):
                    datum=todayDateStr
                else:
                    try:
                        datum = soup.find("time").text.strip().split()
                        s = ""
                        seq = (datum[1], meseci[datum[0]+","], datum[2])
                        datum= uniformDateStr(s.join(seq))
                    except ValueError as e:
                        datum= todayDateStr
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
            except TypeError as e:
                print(e)

        if (tmp < 2):
            tmp += 1
        else:
            tmp = 0

    print(tmp)

def get_articles( SOURCE_ID):
    stevilka_strani = 1
    now = datetime.datetime.now()
    now = now.year
    get_text(stevilka_strani, SOURCE_ID)
    pagesChecked = 0
    while True:
        pagesChecked += 1
        stevilka_strani+=1
        get_text(stevilka_strani,SOURCE_ID)
        if not firstRunBool and pagesChecked >= NUM_PAGES_TO_CHECK and pagesChecked < 100: #ne rabimo pregledati vseh 400 strnai, ker gre nazaj do leta 2005
            break

def main():
    get_articles("Pomurske novice")


if __name__ == '__main__':
    # checks if the second argument is provided and is equal to "-F" - means first run
    if len(sys.argv) == 2 and sys.argv[1] == "-F":
        firstRunBool = True

    print ("Add -F as the command line argument to execute first run command - downloads the whole history of articles from the page.")

    main()