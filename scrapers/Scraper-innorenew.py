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
meseci = {'january,': '1.', 'february,': '2.', 'march,': '3.', 'april,': '4.', 'may,': '5.',
          'june,': '6.', 'july,': '7.', 'august,': '8.', 'september,': '9.',
'october,': '10.', 'november,': '11.', 'december,': '12.'}



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
parent_link = ("https://innorenew.eu/")

def uniformDateStr(dateStr, inputDateFromat=""):
    if inputDateFromat == "":
        inputDateFromat = "%d.%m.%Y"
    return datetime.datetime.strptime(dateStr, inputDateFromat).strftime("%Y-%m-%d")





def get_text(stran,SOURCE_ID):



    sqlBase = dbExecutor()  # creates a sql database handler class
    todayDateStr = datetime.datetime.now().strftime("%Y-%m-%d")  # today date in the uniform format


    soup = BeautifulSoup(simple_get("https://innorenew.eu/news/#"), "html.parser")
    all_links = soup.find("div").find_all("a")
    tmp = 0
    for links in all_links:
        if(links.get("href")==None): continue
        if(re.match("https://innorenew.eu/[0-9][0-9][0-9][0-9/]+",links.get("href")) and tmp == 0 ):
            soup = BeautifulSoup(simple_get(links.get("href")), "html.parser")
            n_soup = soup.find("div", {"class":"col-md-7 col-md-push-5"})
            naslov = n_soup.find("h2").text.strip()
            d_soup = soup.find("aside", {"class":"col-md-3 col-md-pull-7"})
            soup = soup.find("article")
            dat = d_soup.find_all("p")
            datum = dat[1].text.split()
            s=""
            seq = (datum[2], meseci[str(datum[1]).lower()+","], datum[3])
            datum = uniformDateStr(s.join(seq), "%d,%m.%Y")
            vse = soup.find_all("p")

            vsebina = ""
            tmp_bool = True
            for obj in vse:
                if(tmp_bool):
                    tmp_bool= False
                    continue
                vsebina += str(obj.text).strip() + "\n"
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


        if (tmp < 2):
            tmp += 1
        else:
            tmp = 0
def get_articles( SOURCE_ID):
    stevilka_strani = 1
    get_text(stevilka_strani, SOURCE_ID)



def main():
    get_articles("innorenew")


if __name__ == '__main__':
    # checks if the second argument is provided and is equal to "-F" - means first run
    if len(sys.argv) == 2 and sys.argv[1] == "-F":
        firstRunBool = True

    print ("Add -F as the command line argument to execute first run command - downloads the whole history of articles from the page.")

    main()