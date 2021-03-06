from bs4 import BeautifulSoup
import requests
import hashlib
import datetime
from database.dbExecutor import dbExecutor
import sys
from tqdm import tqdm
''' 
    firstRunBool used - working
    
    created by markzakelj
'''
SOURCE = 'LJNOVICE'
firstRunBool = False
num_pages_to_check = 2
num_errors = 0
base_url = 'https://ljnovice.si'
full_url = 'https://ljnovice.si/page/' #kasneje dodas se stevilko strani (1, 2, ..)
headers = {'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/53.0.2785.143 Safari/537.36'}
meseci = {'januar': '1.', 'februar': '2.', 'marec': '3.', 'april': '4.', 'maj': '5.',
          'junij': '6.', 'julij': '7.', 'avgust': '8.', 'september': '9.',
          'oktober': '10.', 'november': '11.', 'december': '12.'}

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
        return link.get('href')
    log_error('link not found, update select() method')
    return 'link not found'


def getDate(soup):
    raw_date = soup.find('time')
    if raw_date:
        raw_date = raw_date.text.replace(',', '.').split(' ')
        raw_date[0] = meseci[raw_date[0]]
        temp = raw_date[0]
        raw_date[0] = raw_date[1]
        raw_date[1] = temp 
        return ''.join(raw_date)
    log_error('Date not found, update select() method')
    return '1.1.1111'


def getTitle(soup):
    title = soup.select('article > header > h2 > a')
    if title:
        return ' '.join(title[0].text.split())
    log_error('title not found, update select() method')
    return 'title not found'


def getContent(url, session):
    r = get_connection(url, session)
    soup = BeautifulSoup(r.text, 'lxml')
    content =  soup.find('div', class_='entry-content clearfix')
    if content:
        return ' '.join(content.text.split())
    log_error('content not found: '+url)
    return 'content not found'


def getArticlesOn_n_pages(num_pages_to_check, session):
    articles = []
    i = 0
    n = 0
    print('\tgathering articles ...')
    while i < num_pages_to_check:
        r = get_connection(full_url + str(n+1), session)
        soup = BeautifulSoup(r.text, 'lxml')
        articles_on_page = soup.find_all('div', class_='post-column clearfix')
        articles = articles + articles_on_page
        if firstRunBool and n < 100:
            n += 1
            if not soup.find('div', class_='post-pagination clearfix').find('a', class_='next'):
                print('found last page')
                break
        else:
            i += 1
            n += 1
    return articles

def format_date(date):
    #format date for consistent database
    date = date.split('.')
    for i in range(2):
        if len(date[i]) == 1:
            date[i] = '0'+date[i]
    return '-'.join(reversed(date))


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
            date = format_date(getDate(x))
            hash_str = makeHash(title, date)

            if is_article_new(hash_str):
                link = getLink(x)
                content = getContent(link, session)
                tup = (str(datetime.date.today()), title, content, date, hash_str, link, SOURCE)
                dbExecutor.insertOne(tup)
                num_new_articles += 1

    print(num_new_articles, 'new articles found,', len(articles), 'articles checked,', num_errors, 'errors found\n')

if __name__ == '__main__':
    if len(sys.argv) == 2 and sys.argv[1] == "-F":
        firstRunBool = True
    main()