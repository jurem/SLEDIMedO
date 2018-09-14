from bs4 import BeautifulSoup
import requests
import hashlib
import datetime
from database.dbExecutor import dbExecutor
import sys
from tqdm import tqdm
''' 
    created by markzakelj
'''

SOURCE = 'PRC'
firstRunBool = False
num_errors = 0
num_pages_to_check = 1
base_url = 'https://www.prc.si'
full_url = 'https://www.prc.si/novice?page=' #kasneje dodas se stevilo strani (1, 2, ...)
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
    soup = BeautifulSoup(r.text, 'html.parser')
    num = soup.find('div', class_='pages tc fs14').find_all('a')[-2].text
    return int(num)
    

def is_article_new(hash_str):
    if dbExecutor.getByHash(hash_str):
        return False
    return True


def getLink(soup):
    link = soup.find('a')
    if link:
        return base_url + link['href']
    log_error('link not found, update select() method')
    return 'link not found'


def getDate(soup):
    date = []
    raw_date = soup.find('div', class_='fr date')
    if raw_date:
        for c in raw_date.find_all('img'):
            date.append(c.get('src')[-5])
        date = ''.join(date)
        date = date.replace('t', '.')
        return date
    log_error('date not found inside soup')
    return '1.1.1111' #1.1.1111 means original date was not found


def getTitle(soup):
    title = soup.select('div > h4')
    if title:
        return title[0].text.strip()
    log_error('title not found, update select() method')
    return 'title not found'


def getContent(url, session):
    r = session.get(url, timeout=10)
    soup = BeautifulSoup(r.text, 'html.parser')

    content = soup.find('div', class_='empty')
    if content:
        text = content.text
        return ' '.join(text.split())
    log_error('content not found, url: '+url)
    return 'content not found'


def formatDate(date):
    #format date for consistent database
    date = date.split('.')
    for i in range(2):
        if len(date[i]) == 1:
            date[i] = '0'+date[i]
    return '-'.join(reversed(date))



def getArticlesOn_n_pages(num_pages_to_check, session):
    if firstRunBool:
        num_pages_to_check = find_last_page(full_url+ str(1), session)
    articles = []
    print('\tgathering articles ...')
    for n in range(num_pages_to_check):
        r = session.get(full_url + str(n+1), timeout=10)
        soup = BeautifulSoup(r.text, 'html.parser')
        articles += soup.find('ul', class_='news').find_all('li', class_='pr')
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

        list_of_tuples = []
        print('\tgathering article info ...')
        for x in tqdm(articles):
            title = getTitle(x)
            date = getDate(x)
            hash_str = makeHash(title, date)

            if is_article_new(hash_str):
                link = getLink(x)
                content = getContent(link, session)
                tup = (str(datetime.date.today()), title, content, formatDate(date), hash_str, link, SOURCE)
                list_of_tuples.append(tup)
                num_new_articles += 1

        dbExecutor.insertMany(list_of_tuples)
        print(num_new_articles, 'new articles found,', articles_checked, 'articles checked,', num_errors, 'errors found\n')

if __name__ == '__main__':
    if len(sys.argv) == 2 and sys.argv[1] == "-F":
        firstRunBool = True
    main()
