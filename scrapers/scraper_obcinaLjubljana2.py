from bs4 import BeautifulSoup
import requests
import hashlib
import datetime
from database.dbExecutor import dbExecutor
import sys
from tqdm import tqdm


''' 
    firstRunBool used - working

    ta scraper crpa iz strani "ostale novice", obstaja se drug scraper,
    ki crpa iz strani "aktualno"
    
    na tem url-ju so clanki zbrani na samo eni strani!

    nekateri clanki ne vodijo do nove strani, ampak te vodijo na osnovno stran - content not found - te napake ignoriraj!

    created by markzakelj
'''
SOURCE = 'OBCINA-LJUBLJANA'
firstRunBool = False
num_articles_to_check = 20
num_errors = 0
base_url = 'https://www.ljubljana.si'
full_url = 'https://www.ljubljana.si/sl/aktualno/ostale-novice-2/'
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
    link = soup.select('div > h2 > a')
    if link:
        return base_url + link[0]['href']
    log_error('link not found, update select() method')
    return 'link not found'


def getDate(soup):
    raw_date = soup.select('div > a > img > span')
    if raw_date:
        return raw_date[0].text.replace(' ', '')
    raw_date2 = soup.select('div > a > span')
    if raw_date2:
        return raw_date2[0].text.replace(' ', '')

    log_error('date not found, update select() method')
    return '1.1.1111'


def getTitle(soup):
    title = soup.select('div > h2 > a')
    if title:
        return title[0].text
    log_error('title not found, update select() method')
    return 'title not found'


def getContent(url, session):
    r = session.get(url, timeout=10)
    soup = BeautifulSoup(r.text, 'html.parser')

    content = soup.find('div', class_='lag-wrapper')
    if content:
        text = content.text
        return text    
    log_error('content not found, update select() method or get content from excerpt')
    return None


def formatDate(date):
    #format date for consistent database
    date = date.split('.')
    for i in range(2):
        if len(date[i]) == 1:
            date[i] = '0'+date[i]
    return '-'.join(reversed(date))


def getArticlesOn_n_pages(num_articles_to_check, session):
    if firstRunBool:
        num_articles_to_check = None #da vrne cel list
    r = session.get(full_url)
    print('\tgathering articles ...')
    soup = BeautifulSoup(r.text, 'html.parser')
    articles = soup.find('ul', class_='list-big-blocks').find_all('li')
    return articles[:num_articles_to_check]


def main():

    print('=========================')
    print(sys.argv[0])
    print('=========================')
    
    num_new_articles = 0

    with requests.Session() as session:
        session.headers.update(headers)
        articles = getArticlesOn_n_pages(num_articles_to_check, session)

        new_articles_tuples = []

        print('\tgathering article info ...')
        for x in tqdm(articles):
            title = getTitle(x)
            date = getDate(x)
            hash_str = makeHash(title, date)

            if is_article_new(hash_str):
                link = getLink(x)
                content = getContent(link, session)
                if not content:
                    content = x.find('p').text
                num_new_articles += 1
                new_articles_tuples.append((str(datetime.date.today()), title, content, formatDate(date), hash_str, link, SOURCE))
    
    dbExecutor.insertMany(new_articles_tuples)
    print(num_new_articles, 'new articles found,', len(articles), 'articles checked,', num_errors, 'errors found\n')


if __name__ == '__main__':
    if len(sys.argv) == 2 and sys.argv[1] == "-F":
        firstRunBool = True
    main()
