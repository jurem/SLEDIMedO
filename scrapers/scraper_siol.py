from bs4 import BeautifulSoup
import requests
import hashlib
from database.dbExecutor import dbExecutor
import sys
import datetime
from tqdm import tqdm
import os

'''
    firstRunBool - novic je prevec, nastavi num_pages_to_check=500

    za dostop do datuma je potrebno odpreti link do clanka - hash_str je sestavljen samo iz naslova

    created by markzakelj
'''

SOURCE = 'SIOL'
firstRunBool = False
num_errors = 0
base_url = 'https://siol.net'
full_url = 'https://siol.net/novice/slovenija?page=' #dodas se stevilko strani, 1 je prva stran
headers = {
    'user-agent':
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/53.0.2785.143 '
        'Safari/537.36'}

def makeHash(title):
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

def is_article_new(hash_str):
    if dbExecutor.getByHash(hash_str):
        return False
    return True

def getLink(soup):
    link = soup.find('a')
    if link:
        return base_url + link.get('href')
    log_error('link not found, update find() method')
    return 'link not found'


def getDate(soup):
    date = soup.find('span', class_='article__publish_date--date')
    if date:
        return ''.join(date.text.split()).strip(';')
    log_error('date not found, update find() method')
    return '1.1.1111'


def getTitle(soup):
    title = soup.find('a').get('title')
    if title:
        return title
    log_error('title not found, update find() method')
    return 'title not found'


def getContent(soup):
    
    content = soup.find('div', class_='article__body--content js_articleBodyContent')
    if content:
        return ' '.join(content.text.split())
    log_error('content not found, update select() method')
    return 'content not found'

def getArticlesOnPage(num_pages_to_check, session):
    articles = []
    if firstRunBool:
        num_pages_to_check = 500
    print('\tgathering articles ...')
    for n in tqdm(range(num_pages_to_check)):
        r = get_connection(full_url+str(n+1), session)
        soup = BeautifulSoup(r.text, 'html.parser')
        articles += soup.find('div', class_='column_content__inner').find_all('article')
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
        log_error('cant format date:'+ str(raw_date))


def main():
    print('===============')
    print(sys.argv[0])
    print('===============')

    num_pages_to_check = 3
    num_new_articles = 0

    with requests.Session() as session:
        session.headers.update(headers)
        articles = getArticlesOnPage(num_pages_to_check, session)

        print('\tgathering article info ...')
        for x in tqdm(articles):
            title = getTitle(x)
            hash_str = makeHash(title)

            if is_article_new(hash_str):
                link = getLink(x)
                r = get_connection(link, session)
                soup = BeautifulSoup(r.text, 'lxml')
                content = getContent(soup)
                date = getDate(soup)
                tup = (str(datetime.date.today()), title, content, formatDate(date), hash_str, link, SOURCE)
                dbExecutor.insertOne(tup)
                num_new_articles += 1    

        print(num_new_articles, 'new articles found,', len(articles), 'articles checked,', num_errors, 'errors found\n')



if __name__ == '__main__':
    if len(sys.argv) == 2 and sys.argv[1] == "-F":
        firstRunBool = True
    main()