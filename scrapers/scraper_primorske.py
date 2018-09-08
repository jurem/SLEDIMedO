import requests
from bs4 import BeautifulSoup as bs
import hashlib
from database.dbExecutor import dbExecutor
import datetime
import sys
from tqdm import tqdm
import re

""" 

    formatDate ni uporaben, datum je na strani ze v pravi obliki

    napake, so verjetno zaradi praznih 'clankov' (white space na page-u)
    nov

    created by markzakelj
"""

SOURCE = 'PRIMORSKE'
firstRunBool  = False
num_pages_to_check = 1
num_errors = 0
base_url = 'https://www.primorske.si'
full_urls = ['https://www.primorske.si/primorska/istra?page=',
             'https://www.primorske.si/primorska/goriska?page=', 
             'https://www.primorske.si/primorska/srednja-primorska?page=',
             'https://www.primorske.si/kultura?page=']
            
             #dodaj se stevilo strani - prva stran je 0

#full_urls = ['https://www.primorske.si/primorska/istra?page='] use this variable when testing - it's faster ;)
headers = {'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/53.0.2785.143 Safari/537.36'}


def make_hash(title, date):
    return hashlib.sha1((title + date).encode('utf-8')).hexdigest()

def find_last_page(url, session):
    r = get_connection(url, session)
    soup = bs(r.text, 'html.parser')
    num = soup.find('ul', class_='pagination').find_all('a')[-1].get('href').split('=')[-1]
    return int(num)

def log_error(text):
    global num_errors
    num_errors += 1
    log_file = open('error_log_zakelj.log', 'a+')
    log_file.write(str(datetime.datetime.today()) + '\n')
    log_file.write('scraper_primorske.py' + '\n')
    log_file.write(text + '\n\n')
    log_file.close()

def get_connection(url, session):
    try:
        r = session.get(url, timeout=10)
        return r
    except requests.exceptions.MissingSchema:
        log_error('invalid url: ' + url)
        return session.get(url)


def is_article_new(hash_str):
    if dbExecutor.getByHash(hash_str):
        return False
    return True


def get_title(soup):
    title = soup.find('a', class_='article-title')
    if title:
        return ' '.join(title.text.split())
    log_error('title not found, update select() method')
    return 'title not found'


def get_date(soup):
    date = soup.find('div', class_='article-published need_to_be_rendered')
    if date:
        return date.get('datetime')[:10]
    log_error('date not found')
    return '1111-01-01' #code for date not found


def get_link(soup):
    link = soup.find('a')
    if link:
        return base_url + link.get('href')
    log_error('link not found')
    return base_url #return base url to avoid exceptions


def get_content(soup):
    content = soup.find('div', class_='content-column')
    if content:
        return ' '.join(content.text.split())
    log_error('content not found')
    return 'content not found'


def get_articles_on_pages(num_pages_to_check, session):
    articles = []
    print('\tgathering articles ...')
    for url in full_urls:
        if firstRunBool:
            num_pages_to_check = find_last_page(url+str(1), session)
        for n in tqdm(range(num_pages_to_check)):
            r = get_connection(url + str(n+1), session)
            soup = bs(r.text, 'html.parser')
            articles += soup.find_all('div', class_='article-full')
            articles += soup.find_all('div', class_='article-medium')
    return articles

def main():
    print('====================')
    print('scraper_primorske.py')
    print('====================')
    
    num_new_articles = 0
    articles_checked = 0

    with requests.Session() as session:
        session.headers.update(headers)

        articles = get_articles_on_pages(num_pages_to_check,session)
        articles_checked = len(articles)

        print('\tgathering article info ...')
        for x in tqdm(articles):
            title = get_title(x)
            date = get_date(x)
            hash_str = make_hash(title, date)

            if is_article_new(hash_str):
                link = get_link(x)
                r = get_connection(link, session)
                soup = bs(r.text, 'html.parser')
                content = get_content(soup)
                new_tup = (str(datetime.date.today()), title, content, date, hash_str, link, SOURCE)
                dbExecutor.insertOne(new_tup)
                num_new_articles += 1

        print(num_new_articles, 'new articles found,', articles_checked,'articles checked', num_errors,'errors found\n')


if __name__ == '__main__':
    if len(sys.argv) == 2 and sys.argv[1] == "-F":
        firstRunBool = True
    main()