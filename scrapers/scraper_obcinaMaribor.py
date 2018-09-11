from bs4 import BeautifulSoup
import requests
import hashlib
import re
from database.dbExecutor import dbExecutor
import sys
import datetime
from tqdm import tqdm

'''
    firstRunBool used - working

    vse novice se crpajo iz ene strani

    created by markzakelj
'''

SOURCE = 'OBCINA-MARIBOR'
firstRunBool = False
num_articles_to_check = 20
num_errors = 0
base_url = 'http://www.maribor.si/'
full_url = 'http://www.maribor.si/podrocje.aspx?id=291'
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
    link = soup.find('a', class_='povezava')
    if link:
        link = link.get('href')
        if re.search(base_url, link):
            return link
        return base_url + link
    log_error('link not found, update find() method')
    return 'link not found'


def getDate(soup):
    date = soup.find('span', class_='DatumVstavljanja1')
    if date:
        return date.text
    log_error('date not found, update find() method')
    return 'date not found'


def getTitle(soup):
    title = soup.find('a', class_='povezava')
    if title:
        return title.text
    log_error('title not found, update find() method')
    return 'title not found'


def getContent(url, session):
    r = get_connection(url, session)
    soup = BeautifulSoup(r.text, 'lxml')
    content = soup.find('div', id='vsebina')
    if content:
        return content.text
    log_error('content not found, url: '+ url)
    return 'content not found'


def makeNewFile(link, title, date, content, hash_str):
    with open(hash_str + '.txt', 'w+', encoding='utf-8') as info_file:
        info_file.write(link + '\n' + title + '\n' + date + '\n' + content)


def getArticlesOnPage(num_articles_to_check, session):
    r = get_connection(full_url, session)
    soup = BeautifulSoup(r.text, 'lxml')
    if firstRunBool:
        num_articles_to_check = -1
    print('\tgathering articles')
    articles = soup.find('div', id='vsebina').findChildren(recursive=False)[1].find_all('tr')
    return articles[:num_articles_to_check] #zadnji link odstranimo, ker je link do arhiva novic(zaenkrat ga ne rabimo)

def formatDate(date):
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
        articles = getArticlesOnPage(num_articles_to_check, session)


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
    print(num_new_articles, 'new articles found,', len(articles), 'articles checked,', num_errors, 'errors\n')

if __name__ == '__main__':
    if len(sys.argv) == 2 and sys.argv[1] == "-F":
        firstRunBool = True
    main()