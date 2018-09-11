from bs4 import BeautifulSoup
import requests
import hashlib
import time
import datetime
from database.dbExecutor import dbExecutor
import sys
from tqdm import tqdm
''' 
    firstRunBool used - working

    created by markzakelj
'''
SOURCE = 'ESS-GOV'
firstRunBool = False
num_pages_to_check = 1
num_errors = 0
base_url = 'https://www.ess.gov.si'
full_url = 'https://www.ess.gov.si/obvestila?pidPagerArticles=' #kasneje dodas se stevilko strani (1, 2, ..)
headers = {'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/53.0.2785.143 Safari/537.36'}


def makeHash(title, date):
    return hashlib.sha1((title+date).encode('utf-8')).hexdigest()

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


def is_article_new(hash_str):
    if dbExecutor.getByHash(hash_str):
        return False
    return True


def getLink(soup):
    link = soup.find('a')
    if link:
        return base_url + link.get('href')
    log_error('link not found, update select() method')
    return 'link not found'


def getDate(soup):
    raw_date = soup.find('time')
    if raw_date:
        return raw_date.text
    log_error('Date not found, update select() method')
    return 'date not found'


def getTitle(soup):
    title = soup.select('header > h3  > a')
    if title:
        return ' '.join(title[0].text.split())
    log_error('title not found, update select() method')
    return 'title not found'


def getContent(url, session):
    r = get_connection(url, session)
    soup = BeautifulSoup(r.text, 'lxml')
    content =  soup.find('div', class_='cc')
    if content:
        return content.text.strip()
    log_error('content not found, update select() method')
    return 'content not found'


def getArticlesOn_n_pages(num_pages_to_check, session):
    articles = []
    i = 0
    n = 0
    print('\tgathering articles ...')
    while i < num_pages_to_check:
        r = get_connection(full_url + str(n+1), session)
        soup = BeautifulSoup(r.text, 'lxml')
        articles_on_page = soup.find_all('article')
        articles = articles + articles_on_page
        if firstRunBool and n < 100:
            n += 1
            if  soup.find('section', class_='pager').find_all('li')[-1]['class'][0] == 'current':
                print('found last page')
                break
        else:
            n += 1
            i += 1
    return articles

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
        articles = getArticlesOn_n_pages(num_pages_to_check, session)

        print('\tgathering article info ...')
        for x in tqdm(articles):
            title = getTitle(x)
            date = getDate(x)
            hash_str = makeHash(title, date)

            if is_article_new(hash_str):
                link = getLink(x)
                content = getContent(link, session)
                new_tup = (str(datetime.date.today()), title, content, formatDate(date), hash_str, link, SOURCE)
                dbExecutor.insertOne(new_tup)
                num_new_articles += 1

    print(num_new_articles, 'new articles found,', len(articles), 'articles checked,', num_errors, 'errors found\n')

if __name__ == '__main__':
    if len(sys.argv) == 2 and sys.argv[1] == "-F":
        firstRunBool = True
    main()