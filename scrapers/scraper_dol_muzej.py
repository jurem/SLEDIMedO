import requests
from bs4 import BeautifulSoup as bs
import hashlib
from database.dbExecutor import dbExecutor
import datetime
import sys
from tqdm import tqdm
"""
    hash je narejen samo iz naslova

    firstRunBool used - working

    created by markzakelj
"""

SOURCE = 'DOL-MUZEJ'
firstRunBool = False
num_pages_to_check = 1
num_errors = 0
base_url = 'http://www.dolenjskimuzej.si'
full_url = 'http://www.dolenjskimuzej.si/si/muzej/novice/?p='
             #dodaj se stevilo strani - prva stran je 1
headers = {'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/53.0.2785.143 Safari/537.36'}

meseci = {'januar': '1.', 'februar': '2.', 'marec': '3.', 'april': '4.', 'maj': '5.',
          'junij': '6.', 'julij': '7.', 'avgust': '8.', 'september': '9.',
          'oktober': '10.', 'november': '11.', 'december': '12.'}

def make_hash(title):
    return hashlib.sha1((title).encode('utf-8')).hexdigest()

def log_error(text):
    global num_errors
    num_errors += 1
    log_file = open('error_log_zakelj.log', 'a+')
    log_file.write(str(datetime.datetime.today()) + '\n')
    log_file.write(sys.argv[0] + '\n')
    log_file.write(text + '\n\n')
    log_file.close()

def get_connection(url, session):
    #time.sleep(3)
    try:
        r = session.get(url, timeout=10)
        return r
    except requests.exceptions.MissingSchema:
        log_error('invalid url: ' + url)
        return session.get(url)
    except requests.exceptions.ConnectionError as e:
        log_error('connection error: '+url+'\n'+str(e))

def correct_string(content):
    #popravi nepravilne znake
    return content.replace('Ä', 'č').replace('Å¡', 'š').replace('Å¾', 'ž').replace('Å½', 'Ž').replace('Å ', 'Š')


def is_article_new(hash_str):
    if dbExecutor.getByHash(hash_str):
        return False
    return True


def get_title(soup):
    title = soup.find('a')
    if title:
        return correct_string(title.text.strip())
    log_error('title not found, update select() method')
    return 'title not found'


def get_date(soup):
    raw_date = soup.find('div', class_='col-lg-12').find('p')
    if raw_date:
        raw_date = raw_date.text
        date = raw_date.split()
        date[1] = meseci[date[1]]
        return ''.join(date)
    log_error('Date not found, update select() method')
    return '1.1.1111'


def get_link(soup):
    link = soup.find('a')
    if link:
        return base_url + link.get('href')
    log_error('link not found')
    return base_url #return base url to avoid exceptions


def get_content(soup):
    content = soup.find('div', class_='col-lg-12 col-md-12 col-sm-12')
    if content:
        return correct_string(content.text.strip())
    content = soup.find('div', class_='col-lg-4 col-md-4 col-sm-4')
    if content:
        return correct_string(content.text.strip())
    log_error('content not found')
    return 'content not found'


def get_articles_on_pages(num_pages_to_check, session):
    articles = []
    if firstRunBool:
        num_pages_to_check = find_last_page(full_url+'1', session)
    print('\tgathering articles ...')
    for n in tqdm(range(num_pages_to_check)):
        r = session.get(full_url + str(n + 1), timeout=10)
        soup = bs(r.text, 'html.parser')
        articles += soup.find('div', class_='col-lg-12 col-md-12 col-sm-12').find_all('h3')
    return articles

def find_last_page(url, session):
    r = get_connection(url, session)
    soup = bs(r.text, 'html.parser')
    num = soup.find('ul', class_='paging').find_all('a')[-1].text
    return int(num)


def formatDate(raw_date):
    #format date for consistent database
    try:
        date = raw_date.split('.')
        for i in range(2):
            if len(date[i]) == 1:
                date[i] = '0'+date[i]
        return '-'.join(reversed(date))
    except IndexError:
        log_error('can\'t format date:'+ str(raw_date))


def main():
    print('=========================')
    print(sys.argv[0])
    print('=========================')

    num_new_articles = 0

    with requests.Session() as session:
        session.headers.update(headers)

        articles = get_articles_on_pages(num_pages_to_check,session)

        print('\tgathering article info ...')
        for x in tqdm(articles):
            title = get_title(x)
            hash_str = make_hash(title)

            if is_article_new(hash_str):
                link = get_link(x)
                r = session.get(link, timeout=8)
                soup = bs(r.text, 'html.parser')
                content = get_content(soup)
                date = get_date(soup)
                new_tup = (str(datetime.date.today()), title, content, formatDate(date), hash_str, link, SOURCE)
                dbExecutor.insertOne(new_tup)
                num_new_articles += 1
        print(num_new_articles, 'new articles found,', len(articles),'articles checked,', num_errors, 'errors found\n')


if __name__ == '__main__':
    if len(sys.argv) == 2 and sys.argv[1] == "-F":
        firstRunBool = True
    main()