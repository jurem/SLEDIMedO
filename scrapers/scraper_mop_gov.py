import requests
from bs4 import BeautifulSoup as bs
import hashlib
from database.dbExecutor import dbExecutor
import datetime
import sys
from tqdm import tqdm
"""
    firstRunBool used - working

    created by markzakelj
"""

SOURCE = 'MOP-GOV'
firstRunBool = False
num_pages_to_check = 2
num_errors = 0
base_url = 'http://www.mop.gov.si'
full_url = ['http://www.mop.gov.si/si/medijsko_sredisce/sporocila_za_javnost/page/',
           'http://www.mop.gov.si/si/medijsko_sredisce/napoved_dogodkov/page/']
             #dodaj se stevilo strani - prva stran je 1
headers = {'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/53.0.2785.143 Safari/537.36'}


def make_hash(title, date):
    return hashlib.sha1((title + date).encode('utf-8')).hexdigest()

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
    soup = bs(r.text, 'html.parser')
    num = soup.find('ul', class_='f3-widget-paginator').find_all('li')[-2].text
    return int(num)


def is_article_new(hash_str):
    if dbExecutor.getByHash(hash_str):
        return False
    return True


def get_title(soup):
    title = soup.find('a', title=True)
    if title:
        return title.text.strip()
    log_error('title not found, update select() method')
    return 'title not found'


def get_date(soup):
    raw_date = soup.find('time')
    if raw_date:
        return raw_date['datetime'].replace(' ', '')
    log_error('date not found')
    return '1.1.1111' #code for date not found


def get_link(soup):
    link = soup.find('a')
    if link:
        return link.get('href')
    log_error('link not found')
    return base_url #return base url to avoid exceptions


def get_content(url, session):
    r = get_connection(url, session)
    soup = bs(r.text, 'html.parser')
    content = soup.find('div', class_='article')
    if content:
        for script in content(['script']):
            script.decompose()
        return content.text.strip()
    log_error('content not found: '+url)
    return 'content not found'


def get_articles_on_pages(num_pages_to_check, session):
    articles = []
    for url in full_url:
        if firstRunBool:
            num_pages_to_check = find_last_page(url+'1', session)
        print('\tgathering articles on: '+ url)
        for n in tqdm(range(num_pages_to_check)):
            r = get_connection(url + str(n + 1), session)
            soup = bs(r.text, 'html.parser')
            articles += soup.find_all('td', class_='news-list-text')
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

        articles = get_articles_on_pages(num_pages_to_check,session)

        print('\tgathering article info ...')
        for x in tqdm(articles):
            title = get_title(x)
            date = get_date(x)
            hash_str = make_hash(title, date)

            if is_article_new(hash_str):
                link = get_link(x)
                content = get_content(link, session)
                new_tup = (str(datetime.date.today()), title, content, formatDate(date), hash_str, link, SOURCE)
                dbExecutor.insertOne(new_tup)
                num_new_articles += 1

        print(num_new_articles, 'new articles found,', len(articles),'articles checked,', num_errors, 'errors found\n')


if __name__ == '__main__':
    if len(sys.argv) == 2 and sys.argv[1] == "-F":
        firstRunBool = True
    main()