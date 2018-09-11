from bs4 import BeautifulSoup
import requests
import hashlib
import datetime
from database.dbExecutor import dbExecutor
import sys
from tqdm import tqdm
''' 
    firstRunBool used - working
    traja zelo dolgo!!!
    
    created by markzakelj
'''
SOURCE = 'NASCAS'
firstRunBool = False
num_pages_to_check = 1
num_errors = 0
base_url = 'http://www.nascas.si'
full_urls = ['http://www.nascas.si/category/gospodarstvo/page/',
             'http://www.nascas.si/category/druzba/page/',
             'http://www.nascas.si/category/kultura/page/',
             'http://www.nascas.si/category/zanimivo/page/'] 
              #kasneje dodas se stevilko strani(1, 2, ...)

headers = {'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/53.0.2785.143 Safari/537.36'}

meseci = {'januar,': '1.', 'februar,': '2.', 'marec,': '3.', 'april,': '4.', 'maj,': '5.',
          'junij,': '6.', 'julij,': '7.', 'avgust,': '8.', 'september,': '9.',
          'oktober,': '10.', 'november,': '11.', 'december,': '12.'}


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

def find_last_page(url, session):
    r = get_connection(url, session)
    soup = BeautifulSoup(r.text, 'html.parser')
    num = soup.find('div', class_='pagination clearfix').find_all('a')[-2].text
    return int(num)


def is_article_new(hash_str):
    if dbExecutor.getByHash(hash_str):
        return False
    return True


def getLink(soup):
    link = soup.find('a')
    if link:
        return link.get('href')
    log_error('link not found, update select() method')
    return 'link not found'


def getDate(soup):
    raw_date = soup.find('span', class_='entry-meta-date updated')
    if raw_date:
        raw_date = raw_date.text.split()
        raw_date[1] = meseci[raw_date[1]]
        return ''.join(raw_date)

    log_error('date not found, update select() method')
    return '1.1.1111'


def getTitle(soup):
    title = soup.find('a', title=True)
    if title:
        return title.get('title')
    log_error('title not found, update select() method')
    return 'title not found'


def getContent(url, session):
    r = session.get(url, timeout=10)
    soup = BeautifulSoup(r.text, 'html.parser')

    content = soup.find('div', class_='entry-content clearfix')
    if content:
        return content.text
    log_error('content not found: '+url)
    return 'content not found'


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


def getArticlesOn_n_pages(num_pages_to_check, session):

    articles = []
    for url in full_urls:
        if firstRunBool:
            num_pages_to_check = find_last_page(url+'1', session)
        print('\tgathering articles on: '+url)
        for n in tqdm(range(num_pages_to_check)):
            r = session.get(url + str(n+1), timeout=10)
            soup = BeautifulSoup(r.text, 'html.parser')
            articles += soup.find_all('article', class_='content-lead')
            articles += soup.find_all('article', class_='content-list')
    return articles


def main():
    print('=========================')
    print(sys.argv[0])
    print('=========================')
    
    num_new_articles = 0

    with requests.Session() as session:
        session.headers.update(headers)

        articles = getArticlesOn_n_pages(num_pages_to_check, session)

        print('\tgathering articles ...')
        for x in tqdm(articles):
            title = getTitle(x)
            date = getDate(x)
            hash_str = makeHash(title, date)

            if is_article_new(hash_str):
                link = getLink(x)
                content = getContent(link, session)
                new_tup = (str(datetime.date.today()), title, content, date, hash_str, link, SOURCE)
                dbExecutor.insertOne(new_tup)
                num_new_articles += 1

    print(num_new_articles, 'new articles found,', len(articles), 'articles checked,', num_errors, 'errors found\n')

if __name__ == '__main__':
    if len(sys.argv) == 2 and sys.argv[1] == "-F":
        firstRunBool = True
    main()