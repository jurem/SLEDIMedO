# -*- coding: utf-8 -*-
from bs4 import BeautifulSoup
import requests
import hashlib
import datetime
from database.dbExecutor import dbExecutor
import sys
from tqdm import tqdm
''' 
    firstBool used - working

    created by markzakelj
'''

SOURCE = 'TURISTICNA-ZVEZA'
firstRunBool = False
num_pages_to_check = 2
num_errors = 0
base_url = 'http://www.turisticna-zveza.si/'
full_url = 'http://www.turisticna-zveza.si/novice.php?stran=' #kasneje dodas se stevilo strani (1, 2, ...)
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
    try:
        r = session.get(url, timeout=10)
        return r
    except requests.exceptions.MissingSchema:
        log_error('invalid url: ' + url)
        return session.get(url)

def correct_string(text):
    #se znebi nepravilno kodiranig sumnikov
    return text.replace('Å½', 'Ž').replace('Ä', 'č').replace('Å¾', 'ž').replace('Å¡', 'š')

def find_last_page(url, session):
    r = get_connection(url, session)
    soup = BeautifulSoup(r.text, 'html.parser')
    num = soup.find('div', class_='pagination').find_all('a')
    if num:
        return int(num[-1].text)
    log_error('last page not found')
    return 1

def is_article_new(hash_str):
    if dbExecutor.getByHash(hash_str):
        return False
    return True


def getLink(soup):
    link = soup.find('footer').find('a')
    if link:
        return base_url + link.get('href')
    log_error('link not found, update select() method')
    return 'link not found'


def getDate(soup):
    raw_date = soup.select('header > h2')
    if raw_date:
        date = raw_date[0].text
        return date[8:]
    log_error('date not found, update select() method')
    return '1.1.1111' #1.1.1111 means original date was not found


def getTitle(soup):
    title = soup.select('header > h1')
    if title:
        return title[0].text.strip()
    log_error('title not found, update select() method')
    return 'title not found'


def getContent(url, session):
    r = get_connection(url, session)
    soup = BeautifulSoup(r.text, 'html.parser')
    content = soup.find('div', class_='novica-vsebina')
    if content:
        text = content.text
        return ' '.join(text.split())
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
        log_error('cant format date:'+ str(raw_date))



def getArticlesOn_n_pages(num_pages_to_check, session):
    articles = []
    if firstRunBool:
        num_pages_to_check = find_last_page(full_url+'1', session)
    print('\tgathering article info ...')
    for n in tqdm(range(num_pages_to_check)):
        r = get_connection(full_url + str(n+1), session)
        soup = BeautifulSoup(r.text, 'html.parser')
        articles += soup.find('section').find_all('article')
    return articles


def main():
    print('=======================')
    print(sys.argv[0])
    print('=======================')

    
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
                tup = (str(datetime.date.today()), correct_string(title), correct_string(content), formatDate(date), hash_str, link, SOURCE)
                dbExecutor.insertOne(tup)
                num_new_articles += 1

        print(num_new_articles, 'new articles found,', len(articles), 'articles checked,', num_errors, 'errors found\n')

if __name__ == '__main__':
    if len(sys.argv) == 2 and sys.argv[1] == "-F":
        firstRunBool = True
    main()
