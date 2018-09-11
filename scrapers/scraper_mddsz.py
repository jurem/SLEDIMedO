from bs4 import BeautifulSoup
import requests
import hashlib
import datetime
from database.dbExecutor import dbExecutor
import sys
from tqdm import tqdm

'''
    firstRunBool used - working (traja lahko tudi do 30 min)

    created by markzakelj
'''

SOURCE = 'MDDSZ'
firstRunBool = False
num_pages_to_check = 3
num_errors = 0
base_url = 'http://www.mddsz.gov.si'
full_url = 'http://www.mddsz.gov.si/si/medijsko_sredisce/sporocila_za_medije/page/' #kasneje dodas se cifro strani
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

def find_last_page(url, session):
    #ne uporabljaj, novic je prevec(segajo do leta 2005)
    r = get_connection(url, session)
    soup = BeautifulSoup(r.text, 'html.parser')
    num = soup.find('ul', class_='f3-widget-paginator').find_all('li')[-2].text
    return int(num)

def is_article_new(hash_str):
    if dbExecutor.getByHash(hash_str):
        return False
    return True

def getLink(soup):
    link = soup.select('h4 > a')
    if link:
        return link[0]['href']
    log_error('link not found, update find() method')
    return base_url #return base_url to avoid exceptions


def getDate(soup):
    date = soup.find('time')
    if date:
        return ''.join(date.text.split())
    log_error('date not found, update find() method')
    return 'date not found'


def getTitle(soup):
    title = soup.select('h4 > a')
    if title:
        return ' '.join(title[0].text.split())
    log_error('title not found, update find() method')
    return 'title not found'


def getContent(url, session):
    r = get_connection(url, session)
    soup = BeautifulSoup(r.text, 'lxml')

    #znebi se script texta na strani, da ne bo del content-a
    for script in soup(['script']):
        script.decompose()

    content = soup.find('div', class_='news news-single-item')
    if content:
        return ' '.join(content.text.split())
    log_error('content not found, update select() method'+url)
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


def getArticlesOnPage(num_pages_to_check, session):
    articles = []
    if firstRunBool:
        #num_pages_to_check = find_last_page(full_url+'1', session)
        num_pages_to_check = 100 #hitreje
    print('\tgathering articles ...')
    for n in tqdm(range(num_pages_to_check)):
        r = get_connection(full_url + str(n+1), session)
        soup = BeautifulSoup(r.text, 'lxml')
        articles_on_page = soup.find('div', class_='news').find_all('table')
        articles = articles + articles_on_page
    return articles


def main():
    print('=========================')
    print(sys.argv[0])
    print('=========================')
    
    num_new_articles = 0

    with requests.Session() as session:
        session.headers.update(headers)
        articles = getArticlesOnPage(num_pages_to_check, session)

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

        print(num_new_articles, 'new articles found', len(articles), 'articles checked,', num_errors, 'errors found\n')



if __name__ == '__main__':
    if len(sys.argv) == 2 and sys.argv[1] == "-F":
        firstRunBool = True
    main()