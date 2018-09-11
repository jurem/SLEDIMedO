from bs4 import BeautifulSoup as bs
import requests
import hashlib
import datetime
from datetime import timedelta
from database.dbExecutor import dbExecutor
import sys
from tqdm import tqdm
''' 
    firstRunBool used - working(res dolgo bo trajalo)
    created by markzakelj
'''

SOURCE = 'REGIONAL-OBALA'
firstRunBool = False
num_pages_to_check = 1
num_errors = 0
base_url = 'http://www.regionalobala.si'
full_urls = ['http://www.regionalobala.si/obalne-zgodbe/',
             'http://www.regionalobala.si/vesti/',
             'http://www.regionalobala.si/trendi/',
             'http://www.regionalobala.si/zanimivo'] 
             #kasneje dodas se stevilo strani (1, 2, ...)

headers = {'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/53.0.2785.143 Safari/537.36'}
date_correct = {'danes': datetime.date.today().strftime('%d.%m.%Y'),
                'včeraj': (datetime.date.today() - timedelta(1)).strftime('%d.%m.%Y') }

def makeHash(title):
    return hashlib.sha1((title).encode('utf-8')).hexdigest()

def find_last_page(url, session):
    r = get_connection(url, session)
    soup = bs(r.text, 'html.parser')
    num = soup.find('div', class_='t1 fright').find_all('a')[-1].get('href').split('/')[-1]
    return int(num)

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
    return base_url

def find_real_date(date):
    if date in date_correct:
        return date_correct[date]
    return date


def getDate(soup):
    raw_date = soup.find('div', class_='newsDate')
    if raw_date:
        date = raw_date.text
        return find_real_date(date[:date.find(' ')]) #odrezi pri prvem presledku - .text je oblike 'dd.mm.yyyy ob hh:mm'
    raw_date = soup.find('div', class_='time')
    if raw_date:
        date = raw_date.text
        return find_real_date(date[:date.find(' ')])
    log_error('date not found, update select() method')
    return '1.1.1111'


def getTitle(soup):
    title = soup.find('a')
    if title:
        return title.text
    log_error('title not found, update select() method')
    return 'title not found'


def getContent(soup):

    #odstrani vse 'script' elemente, da se ne pojavijo v 'content'
    for script in soup(['script']):
        script.decompose()

    content = soup.find('div', class_='p1 block_news no-min-height')
    if content:
        return ' '.join(content.text.split())
    log_error('content not found, update select() method')
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
        print('cant format date:'+ str(raw_date))

def getArticlesOn_n_pages(num_pages_to_check, session):
    articles = []
    print('\tgathering articles ...')
    for url in full_urls:
        if firstRunBool:
            num_pages_to_check = find_last_page(url + '1', session)
        for n in tqdm(range(num_pages_to_check)):
            r = get_connection(url + str(n+1), session)
            soup = bs(r.text, 'html.parser')
            articles += soup.find_all('div', class_='w2 h2 x1 y1 block ')
            articles += soup.find_all('div', class_='grid_4 block_news_small block_news_style')
    return articles


def main():
    print('=========================')
    print(sys.argv[0])
    print('=========================')
    
    num_new_articles = 0

    with requests.Session() as session:
        session.headers.update(headers)
        articles = getArticlesOn_n_pages(num_pages_to_check, session)
        articles_checked = len(articles)

        print('\tgathering article info ...')
        for x in tqdm(articles):
            title = getTitle(x)
            date = getDate(x)
            hash_str = makeHash(title)

            if is_article_new(hash_str):
                link = getLink(x)
                r = get_connection(link, session)
                soup = bs(r.text, 'html.parser')
                content = getContent(soup)
                tup = (str(datetime.date.today()), title, content, formatDate(date), hash_str, link, SOURCE)
                dbExecutor.insertOne(tup)
                num_new_articles += 1

        print(num_new_articles, 'new articles found,', articles_checked, 'articles checked', num_errors, 'errors found\n')

if __name__ == '__main__':
    if len(sys.argv) == 2 and sys.argv[1] == "-F":
        firstRunBool = True
    main()
