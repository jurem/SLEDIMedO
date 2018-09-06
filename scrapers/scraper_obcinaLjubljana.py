from bs4 import BeautifulSoup
import requests
import hashlib
import datetime
from database.dbExecutor import dbExecutor
import sys
from tqdm import tqdm
''' 
    firstRunBool used - working
    
    ta scraper crpa iz strani "aktualno", obstaja se drug scraper,
    ki crpa iz strani "ostale novice"

    created by markzakelj
'''
SOURCE = 'OBCINA-LJUBLJANA'
firstRunBool = False
num_pages_to_check = 2
base_url = 'https://www.ljubljana.si'
full_url = 'https://www.ljubljana.si/sl/aktualno/?start=' #kasneje dodas se stevilo zacetka (10, 20, ...)
headers = {'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/53.0.2785.143 Safari/537.36'}


def makeHash(title, date):
    return hashlib.sha1((title+date).encode('utf-8')).hexdigest()

def log_error(text):
    log_file = open('error_log_zakelj.log', 'a+')
    log_file.write(str(datetime.datetime.today()) + '\n')
    log_file.write('scraper_obcinaLjubljana.py\n')
    log_file.write(text + '\n')
    log_file.close()

def get_connection(url, session):
    try:
        r = session.get(url)
        return r
    except requests.exceptions.MissingSchema:
        log_error('invalid url: ' + url)
        return session.get(full_url)

def find_last_page(session):
    r = get_connection(full_url, session)
    soup = BeautifulSoup(r.text, 'html.parser')
    num = soup.find('div', class_='module paging').find_all('li')[-2].a
    if num:
        return num.text
    log_error('last page not found')
    return 1

def is_article_new(hash_str):
    if dbExecutor.getByHash(hash_str):
        return False
    return True


def getLink(soup):
    link = soup.select('div > h2 > a')
    if link:
        return base_url + link[0]['href']
    log_error('link not found, update select() method')
    return 'link not found'


def getDate(soup):
    raw_date = soup.select('div > a > img > span')
    if raw_date:
        return raw_date[0].text.replace(' ', '')
    raw_date2 = soup.select('div > a > span')
    if raw_date2:
        return raw_date2[0].text.replace(' ', '')

    log_error('date not found, update select() method')
    return 'date not found'


def getTitle(soup):
    title = soup.select('div > h2 > a')
    if title:
        return title[0].text
    log_error('title not found, update select() method')
    return 'title not found'


def getContent(url, session):
    r = session.get(url, timeout=10)
    soup = BeautifulSoup(r.text, 'lxml')

    content = soup.find('div', class_='lag-wrapper')
    if content:
        text = content.text
        return text
    log_error('content not found, update select() method')
    return 'content not found'


def formatDate(date):
    #format date for consistent database
    date = date.split('.')
    for i in range(2):
        if len(date[i]) == 1:
            date[i] = '0'+date[i]
    return '-'.join(reversed(date))



def getArticlesOn_n_pages(num_pages_to_check, session):

    articles = []

    if firstRunBool:
        num_pages_to_check = find_last_page(session)
    print('\tgathering articles ...')
    for n in tqdm(range(num_pages_to_check)):
        r = session.get(full_url + str(n * 10), timeout=10)
        soup = BeautifulSoup(r.text, 'lxml')
        articles_on_page = soup.find('ul', class_='list-big-blocks').find_all('li')
        articles = articles + articles_on_page

    return articles


def main():
    print('==========================')
    print('scraper_obcinaLjubljana.py')
    print('==========================')
    
    num_new_articles = 0

    with requests.Session() as session:
        session.headers.update(headers)
        articles = getArticlesOn_n_pages(num_pages_to_check, session)
        articles_checked = len(articles)

        articles_tuples = []
        print('\tgathering article info ...')
        for x in tqdm(articles):
            title = getTitle(x)
            date = getDate(x)
            hash_str = makeHash(title, date)

            if is_article_new(hash_str):
                link = getLink(x)
                content = getContent(link, session)
                tup = (str(datetime.date.today()), title, content, formatDate(date), hash_str, link, SOURCE)
                articles_tuples.append(tup)
                num_new_articles += 1

        dbExecutor.insertMany(articles_tuples)

    print(num_new_articles, 'new articles found,', num_pages_to_check,'pages checked -', articles_checked, 'articles checked\n')

if __name__ == '__main__':
    if len(sys.argv) == 2 and sys.argv[1] == "-F":
        firstRunBool = True
    main()
