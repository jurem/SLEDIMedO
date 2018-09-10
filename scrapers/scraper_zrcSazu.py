from bs4 import BeautifulSoup
import requests
import hashlib
from database.dbExecutor import dbExecutor
import sys
import datetime
from tqdm import tqdm

'''
    vse novice so zbrane na eni strani

    created by markzakelj
'''

SOURCE = 'ZRC-SAZU'
firstRunBool = False
num_articles_to_check = 20
num_errors = 0
base_url = 'https://www.zrc-sazu.si/'
full_url = 'https://www.zrc-sazu.si/sl/novice'
headers = {
    'user-agent':
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/53.0.2785.143 '
        'Safari/537.36'}

def makeHash(title, date):
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


def is_article_new(hash_str):
    if dbExecutor.getByHash(hash_str):
        return False
    return True

def getLink(soup):
    link = soup.find('a')
    if link:
        return link.get('href')
    log_error('link not found, update find() method')
    return 'link not found'


def getDate(soup):
    date = soup.find('div').contents
    if date:
        return ''.join(date[-3].split())
    log_error('date not found, update find() method')
    return 'date not found'


def getTitle(soup):
    title = soup.find('a')
    if title:
        return title.text
    log_error('title not found, update find() method')
    return 'title not found'


def getContent(url, session):
    r = session.get(url, timeout=5)
    soup = BeautifulSoup(r.text, 'lxml')
    content = soup.find('div', class_='left content-wide').find('div', class_='field-items')
    if content:
        return content.text
    log_error('content not found, update select() method'+url)
    return 'content not found'


def getArticlesOnPage(num_articles_to_check, session):
    r = session.get(full_url, timeout=5)
    soup = BeautifulSoup(r.text, 'lxml')
    if firstRunBool:
        num_articles_to_check = None
    print('\tgathering articles ...')
    articles = soup.find_all('div', class_='left item news')
    return articles[:num_articles_to_check]


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

    print('=========================')
    print(sys.argv[0])
    print('=========================')
    
    num_new_articles = 0

    with requests.Session() as session:
        session.headers.update(headers)
        articles = getArticlesOnPage(num_articles_to_check, session)

        print('\tgathering article info ...')
        for x in tqdm(articles):
            title = getTitle(x)
            date = getDate(x)
            hash_str = makeHash(title, date)

            if is_article_new(hash_str):
                link = getLink(x)
                content = getContent(link, session)
                tup = (str(datetime.date.today()), title, content, formatDate(date), hash_str, link, SOURCE)
                dbExecutor.insertOne(tup)
                num_new_articles += 1
    

        print(num_new_articles, 'new articles found,', len(articles), 'articles checked,', num_errors, 'errors found\n')



if __name__ == '__main__':
    if len(sys.argv) == 2 and sys.argv[1] == "-F":
        firstRunBool = True
    main()